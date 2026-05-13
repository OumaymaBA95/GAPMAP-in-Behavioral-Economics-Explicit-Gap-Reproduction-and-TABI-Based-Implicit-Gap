#!/usr/bin/env python3
"""
Part 3 utilities: gold cleaning, semantic-style evaluation, agreement export, implicit-gap scaffolding,
and TABI batch extraction (GAPMAP-style Claim–Grounds–Warrant–Bucket).

Usage (from project root):
  .venv/bin/python run_part3.py clean-gold
  .venv/bin/python run_part3.py semantic-compare [--threshold 0.55]
  .venv/bin/python run_part3.py export-agreement
  .venv/bin/python run_part3.py implicit-template [--n 50]
  .venv/bin/python run_part3.py implicit-sample [--n 50]
  .venv/bin/python run_part3.py ablation-commands
  .venv/bin/python run_part3.py implicit-extract --chunk-id 21   # needs OPENAI_API_KEY (optional demo)

  # Full GAPMAP Part 3 — TABI batch (writes Part3_Output/tabi_outputs.csv)
  export OPENAI_API_KEY=sk-...
  export OPENAI_MODEL=gpt-4o
  .venv/bin/python run_part3.py tabi-extract --backend openai --max-chunks 50
  .venv/bin/python run_part3.py tabi-extract --dry-run --max-chunks 5   # no API: schema / path test

  # Optional: RoBERTa-MNLI entailment scores on an existing CSV (needs torch + transformers)
  .venv/bin/python run_part3.py tabi-validate --input Part3_Output/tabi_outputs.csv
  .venv/bin/python run_part3.py tabi-dedupe --input Part3_Output/tabi_outputs.csv   # fix duplicate chunk_id rows

Expanded PDF corpus: place files under a folder and set GAPMAP_DATASET=Dataset_expanded (see Part3_Report.md).

See Part3_Report.md for methodology.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import time
from collections import Counter
from pathlib import Path

import pandas as pd

try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x, **kw: x  # noqa

PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUT_DIR = PROJECT_ROOT / "Part2_Output"
PART3_OUTPUT = PROJECT_ROOT / "Part3_Output"
PART3_OUTPUT.mkdir(exist_ok=True)
GOLD_IN = OUTPUT_DIR / "gold_standard.csv"


def _is_citation_fragment(s: str) -> bool:
    """Same logic as annotate_gold_standard / run_part2 (avoid importing run_part2 at load)."""
    s = s.strip()
    if len(s) < 40:
        if re.search(r"et\s+al\.|&\s*[A-Za-z]|,\s*\d{4}\)?\.?$", s):
            return True
    return False


def _load_preds(x):
    if isinstance(x, str):
        try:
            return json.loads(x)
        except Exception:
            return []
    return x if isinstance(x, list) else []


def _normalize_ws(s: str) -> str:
    return " ".join(s.split()).strip()


def bow_cosine_similarity(a: str, b: str) -> float:
    """Bag-of-words cosine similarity in [0, 1] (no extra dependencies)."""
    a, b = a.lower(), b.lower()
    if not a.strip() or not b.strip():
        return 0.0
    ta = Counter(re.findall(r"[a-z0-9]+", a))
    tb = Counter(re.findall(r"[a-z0-9]+", b))
    if not ta or not tb:
        return 0.0
    keys = set(ta) & set(tb)
    dot = sum(ta[k] * tb[k] for k in keys)
    na = math.sqrt(sum(v * v for v in ta.values()))
    nb = math.sqrt(sum(v * v for v in tb.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def cmd_clean_gold():
    """Remove citation-only sentences from gold_gap_sentences; write Part3_Output/gold_standard_cleaned.csv."""
    if not GOLD_IN.exists():
        print(f"Missing {GOLD_IN}")
        return

    df = pd.read_csv(GOLD_IN)
    removed = 0
    kept_rows = 0
    rows_out = []

    for _, row in df.iterrows():
        cid = row["chunk_id"]
        raw = row.get("gold_gap_sentences", "")
        if pd.isna(raw) or str(raw).strip() == "":
            rows_out.append({"chunk_id": cid, "gold_gap_sentences": ""})
            continue
        parts = [p.strip() for p in str(raw).split(";") if p.strip()]
        kept = []
        for p in parts:
            if _is_citation_fragment(p):
                removed += 1
                continue
            kept.append(_normalize_ws(p))
        joined = "; ".join(kept) if kept else ""
        if joined:
            kept_rows += 1
        rows_out.append({"chunk_id": cid, "gold_gap_sentences": joined})

    out = PART3_OUTPUT / "gold_standard_cleaned.csv"
    pd.DataFrame(rows_out).to_csv(out, index=False)
    print(f"Wrote {out}")
    print(f"Chunks with ≥1 gap after clean: {kept_rows} (citation-like sentences dropped: {removed})")


def cmd_semantic_compare(threshold: float):
    """Same counting as Part 2, but a prediction matches gold if max(ROUGE-L F1, bow_cosine) >= threshold."""
    from rouge_score import rouge_scorer

    gold_path = GOLD_IN
    if not gold_path.exists():
        print(f"Missing {gold_path}")
        return

    gold_df = pd.read_csv(gold_path)
    gold_df = gold_df[
        gold_df["gold_gap_sentences"].notna()
        & (gold_df["gold_gap_sentences"].astype(str).str.strip() != "")
    ]
    gold_ids = set(gold_df["chunk_id"])
    gold_by_chunk = gold_df.set_index("chunk_id")["gold_gap_sentences"].to_dict()

    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)

    def combined_score(gold: str, pred: str) -> float:
        g, p = _normalize_ws(gold), _normalize_ws(pred)
        r = scorer.score(g, p)["rougeL"].fmeasure
        c = bow_cosine_similarity(g, p)
        return max(r, c)

    def eval_file(path: Path):
        name = path.stem.replace("predictions_", "")
        preds = pd.read_csv(path).to_dict("records")
        pred_filtered = [p for p in preds if p["chunk_id"] in gold_ids]
        tp = fp = fn = 0
        for p in pred_filtered:
            cid = p["chunk_id"]
            plist = _load_preds(p["predictions"])
            gold_list = [g.strip() for g in str(gold_by_chunk.get(cid, "")).split(";") if g.strip()]
            matched = set()
            for pred in plist:
                best_idx, best_s = None, 0.0
                for i, gold in enumerate(gold_list):
                    s = combined_score(gold, pred)
                    if s >= threshold and s > best_s:
                        best_idx, best_s = i, s
                if best_idx is not None:
                    matched.add(best_idx)
                    tp += 1
                else:
                    fp += 1
            fn += len(gold_list) - len(matched)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        return name, prec, rec, f1

    pred_files = sorted(OUTPUT_DIR.glob("predictions_*.csv"))
    if not pred_files:
        print("No predictions_*.csv in Part2_Output/")
        return

    lines = [
        f"=== Semantic-augmented match: max(ROUGE-L, bow-cosine) >= {threshold} ===\n",
        f"{'Model':<25} {'Precision':>10} {'Recall':>10} {'F1':>10}\n",
        "-" * 57 + "\n",
    ]
    print(lines[0].strip())
    print(lines[1].rstrip())
    print(lines[2].rstrip())
    for pf in pred_files:
        name, prec, rec, f1 = eval_file(pf)
        line = f"{name:<25} {prec:>10.4f} {rec:>10.4f} {f1:>10.4f}\n"
        lines.append(line)
        print(line.rstrip())

    out = PART3_OUTPUT / "semantic_compare.txt"
    with open(out, "w") as f:
        f.writelines(lines)
    print(f"\nSaved to {out}")
    print("Note: This credits some paraphrases ROUGE alone would miss; compare to `python run_part2.py --compare`.")


def cmd_export_agreement():
    """Chunks where gpt4o_mini, gpt_4o, and ollama all have ≥1 prediction (high-confidence list)."""
    files = {
        "gpt4o_mini": OUTPUT_DIR / "predictions_gpt4o_mini.csv",
        "gpt_4o": OUTPUT_DIR / "predictions_gpt_4o.csv",
        "ollama": OUTPUT_DIR / "predictions_ollama.csv",
    }
    loaded = {}
    for k, p in files.items():
        if not p.exists():
            print(f"Missing {p.name}; skip agreement export.")
            return
        loaded[k] = pd.read_csv(p).set_index("chunk_id")["predictions"].to_dict()

    all_ids = set(loaded["gpt4o_mini"]) & set(loaded["gpt_4o"]) & set(loaded["ollama"])
    agree = []
    for cid in sorted(all_ids):
        if all(len(_load_preds(loaded[m][cid])) > 0 for m in files):
            agree.append({"chunk_id": cid})

    out = PART3_OUTPUT / "high_confidence_chunks.csv"
    pd.DataFrame(agree).to_csv(out, index=False)
    print(f"Chunks with gaps in all three models: {len(agree)}")
    print(f"Wrote {out}")


def cmd_implicit_template(n: int):
    """Rows: chunk_ids that have explicit gold, for manual implicit-gap labeling."""
    if not GOLD_IN.exists():
        print(f"Missing {GOLD_IN}")
        return
    gold_df = pd.read_csv(GOLD_IN)
    gold_df = gold_df[
        gold_df["gold_gap_sentences"].notna()
        & (gold_df["gold_gap_sentences"].astype(str).str.strip() != "")
    ]
    ids = gold_df["chunk_id"].head(n).tolist()
    out = PART3_OUTPUT / "implicit_gold_template.csv"
    pd.DataFrame({"chunk_id": ids, "implicit_gap_sentence": [""] * len(ids)}).to_csv(out, index=False)
    print(f"Wrote {out} ({len(ids)} rows). Fill implicit_gap_sentence manually.")


def cmd_implicit_sample(n: int):
    """Attach text excerpt per chunk for implicit annotation (uses live chunking)."""
    from run_part2 import chunk_all, load_articles

    articles = load_articles()
    chunks = chunk_all(articles)
    by_id = {c["chunk_id"]: c for c in chunks}

    if not GOLD_IN.exists():
        print(f"Missing {GOLD_IN}")
        return
    gold_df = pd.read_csv(GOLD_IN)
    gold_df = gold_df[
        gold_df["gold_gap_sentences"].notna()
        & (gold_df["gold_gap_sentences"].astype(str).str.strip() != "")
    ]
    ids = gold_df["chunk_id"].head(n).tolist()
    rows = []
    for cid in ids:
        c = by_id.get(cid, {})
        text = c.get("text", "")
        rows.append(
            {
                "chunk_id": cid,
                "article_filename": c.get("article_filename", ""),
                "text_excerpt": (text[:2500] + "…") if len(text) > 2500 else text,
                "implicit_gap_sentence": "",
            }
        )
    out = PART3_OUTPUT / "implicit_annotation_sample.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Wrote {out} ({len(rows)} rows).")


IMPLICIT_SYSTEM_PROMPT = """You identify IMPLICIT knowledge gaps in behavioral economics text.
An implicit gap is NOT a sentence that says "further research is needed" (that is explicit).
It is an unstated limitation inferable from the passage, e.g.:
- Conflicting findings without reconciliation
- Results that may not generalize beyond the sample
- A causal claim that the design cannot support

Output exactly ONE short sentence stating the inferred gap, grounded ONLY in the text.
If none can be justified, output exactly: NONE
Do not quote long passages."""


def cmd_implicit_extract(chunk_id: int):
    """Demo: one chunk implicit extraction via OpenAI (optional)."""
    import os

    from run_part2 import chunk_all, load_articles

    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key.startswith("sk-"):
        print("Set OPENAI_API_KEY=sk-...")
        return
    articles = load_articles()
    chunks = chunk_all(articles)
    by_id = {c["chunk_id"]: c for c in chunks}
    c = by_id.get(chunk_id)
    if not c:
        print(f"No chunk {chunk_id}")
        return
    from openai import OpenAI

    client = OpenAI(api_key=key)
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    user = f"Text:\n\n{c['text'][:8000]}\n\nOne implicit gap sentence or NONE:"
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": IMPLICIT_SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        temperature=0,
    )
    out = resp.choices[0].message.content.strip()
    print(f"chunk_id={chunk_id}\n{out}")


TABI_MAX_TEXT = 8000

# GAPMAP-style TABI: Toulmin-inspired quadruple + confidence bucket (3-shot, JSON only).
TABI_SYSTEM_PROMPT = """You infer at most ONE implicit knowledge gap from scientific text using a Toulmin-style scaffold (GAPMAP / TABI).

Goal: produce HIGH-PRECISION implicit gaps. It is OK to return NONE often.

An implicit gap must be a research-relevant limitation or missing evidence that could motivate a future study, such as:
- generalizability limits (sample, context, country, lab vs field)
- missing mechanism / causal identification limits
- short horizon / no longitudinal durability evidence
- unresolved contradictions / mixed evidence without reconciliation
- missing moderators / boundary conditions

DO NOT output pseudo-gaps like:
- “details are not provided” about acknowledgments, funding, grants, datasets, project names
- “the paper did not describe X” unless X is a research-relevant limitation tied to results

Grounding rules (strict):
- "grounds" MUST be verbatim text copied from the input (short quotes), and should include a limitation cue or concrete constraint.
- If you cannot quote strong grounds, output claim = "NONE".

Reply with ONE JSON object only (no markdown fences) using exactly these keys:
- "claim": string. ONE sentence: the inferred gap. Use "NONE" if no defensible implicit gap exists.
- "grounds": string. Verbatim phrase(s) copied from the input supporting the gap (quotes).
- "warrant": string. ONE sentence: how the grounds support the claim (the reasoning link).
- "bucket": either "more_probable" or "least_probable" reflecting confidence.

Few-shot exemplars (output shape only; your input will be different):

Input: "We observe high green intent in surveys but low uptake in costly actions. Prior field work is mostly Western samples."
{"claim":"Whether pro-environmental intention translates to costly behavior depends on moderators that are underspecified outside Western samples.","grounds":"Prior field work is mostly Western samples","warrant":"Because the authors contrast stated intent with costly behavior but limit generalizability, cross-context mechanisms remain untested.","bucket":"more_probable"}

Input: "The nudge increased short-term recycling; six months later the effect was indistinguishable from baseline."
{"claim":"Long-term durability of this nudge beyond six months is unknown.","grounds":"six months later the effect was indistinguishable from baseline","warrant":"Because only short-horizon outcomes are shown, persistence and habituation cannot be assessed.","bucket":"more_probable"}

Input: "Our experiment confirms Hypothesis 2 at p<0.05."
{"claim":"NONE","grounds":"","warrant":"The excerpt reports a confirmed hypothesis without exposing a structural limitation to infer as a gap.","bucket":"least_probable"}
"""


_PSEUDO_GAP_RE = re.compile(
    r"(funded by|funding|grant|h2020|acknowledg|project\s+[a-z0-9_-]+|this work was funded)",
    re.I,
)


def _tabi_strict_sanitize(parsed: dict, min_grounds_chars: int) -> dict:
    """Post-check TABI outputs to reduce low-value overgeneration."""
    claim = (parsed.get("claim") or "").strip()
    grounds = (parsed.get("grounds") or "").strip()
    warrant = (parsed.get("warrant") or "").strip()
    if not claim:
        parsed["claim"] = "NONE"
        parsed["bucket"] = "least_probable"
        return parsed
    if claim.upper() == "NONE":
        parsed["bucket"] = "least_probable"
        return parsed
    # Require some real quoted grounds.
    if len(grounds) < int(min_grounds_chars):
        parsed["claim"] = "NONE"
        parsed["bucket"] = "least_probable"
        parsed["grounds"] = ""
        parsed["warrant"] = warrant or "Insufficient grounded evidence quoted from the text."
        return parsed
    # Drop “funding / project details missing” pseudo-gaps.
    if _PSEUDO_GAP_RE.search(grounds) and re.search(r"(not\s+detail|not\s+describ|not\s+provide|not\s+specif)", claim, re.I):
        parsed["claim"] = "NONE"
        parsed["bucket"] = "least_probable"
        parsed["grounds"] = ""
        parsed["warrant"] = "Filtered pseudo-gap about acknowledgments/funding details (not a research limitation)."
        return parsed
    return parsed


def _strip_json_fence(content: str) -> str:
    s = content.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _parse_tabi_json(content: str) -> dict:
    raw = _strip_json_fence(content)
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"claim": "", "grounds": "", "warrant": "", "bucket": "least_probable", "_parse_error": str(e), "_raw": raw[:500]}
    out = {
        "claim": _normalize_ws(str(obj.get("claim", ""))),
        "grounds": _normalize_ws(str(obj.get("grounds", ""))),
        "warrant": _normalize_ws(str(obj.get("warrant", ""))),
        "bucket": str(obj.get("bucket", "least_probable")).lower().strip(),
    }
    if out["bucket"] not in ("more_probable", "least_probable"):
        out["bucket"] = "least_probable"
    return out


def _claim_fingerprint(claim: str) -> str:
    c = re.sub(r"[^\w\s]+", " ", claim.lower()).split()
    return hashlib.sha256(" ".join(c[:40]).encode("utf-8")).hexdigest()[:20]


def cmd_tabi_extract(
    backend: str,
    model: str | None,
    max_chunks: int | None,
    out_path: Path,
    chunk_ids_csv: Path | None,
    resume: bool,
    dedupe: bool,
    sleep_s: float,
    dry_run: bool,
    strict: bool,
    min_grounds_chars: int,
):
    """Batch TABI over all chunks from run_part2.load_articles + chunk_all."""
    from run_part2 import chunk_all, load_articles

    articles = load_articles()
    chunks = chunk_all(articles)
    if not chunks:
        print("No chunks — add PDFs under Dataset/ or set GAPMAP_DATASET to your PDF folder.")
        return

    id_filter: set | None = None
    if chunk_ids_csv is not None and chunk_ids_csv.exists():
        cdf = pd.read_csv(chunk_ids_csv)
        if "chunk_id" not in cdf.columns:
            print(f"CSV must have chunk_id column: {chunk_ids_csv}")
            return
        id_filter = set(cdf["chunk_id"].astype(int).tolist())
        chunks = [c for c in chunks if c["chunk_id"] in id_filter]
        print(f"Filtered to {len(chunks)} chunks from {chunk_ids_csv}")

    if max_chunks is not None:
        chunks = chunks[: max(0, int(max_chunks))]

    done_ids: set = set()
    if resume and out_path.exists():
        try:
            prev = pd.read_csv(out_path)
            # Only skip rows that appear successfully processed.
            # This allows --resume to RETRY rows that previously failed (e.g., quota/rate-limit).
            if "parse_error" in prev.columns:
                ok = prev["parse_error"].fillna("").astype(str).str.strip().eq("")
                done_ids = set(prev.loc[ok, "chunk_id"].astype(int).tolist())
            else:
                done_ids = set(prev["chunk_id"].astype(int).tolist())
            print(f"Resume: skipping {len(done_ids)} successful chunk_ids already in {out_path.name}")
        except Exception as e:
            print(f"Could not read resume file ({e}); overwriting.")
            done_ids = set()

    seen_fp: set = set()
    if resume and out_path.exists() and dedupe:
        try:
            prev = pd.read_csv(out_path)
            for _, r in prev.iterrows():
                seen_fp.add(_claim_fingerprint(str(r.get("claim", ""))))
        except Exception:
            pass

    backend = backend.lower().strip()
    model_name = model or (
        os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        if backend == "openai"
        else os.environ.get("OLLAMA_MODEL", "llama3.2")
    )

    if dry_run:
        model_name = model or "dry-run"
        print("DRY-RUN mode: no API calls; writing placeholder TABI JSON per chunk.")

        def infer_one(_text: str) -> str:
            return json.dumps(
                {
                    "claim": "NONE",
                    "grounds": "",
                    "warrant": "Placeholder (tabi-extract --dry-run). Export OPENAI_API_KEY and rerun without --dry-run for real TABI.",
                    "bucket": "least_probable",
                }
            )

    elif backend == "openai":
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key.startswith("sk-"):
            print("Set OPENAI_API_KEY=sk-... for tabi-extract --backend openai")
            return
        from openai import OpenAI

        client = OpenAI(api_key=key)
        try:
            client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Reply with exactly: OK"}],
                temperature=0,
                max_tokens=6,
            )
            print(f"OpenAI pre-flight OK ({model_name}).")
        except Exception as e:
            print(
                "Aborting tabi-extract: OpenAI rejected this key or model.\n"
                "Fix: copy a fresh API key from https://platform.openai.com/api-keys\n"
                "Never use placeholder text like sk-... in tutorials — export the full secret.\n"
                f"Detail: {e}"
            )
            return

        def infer_one(text: str) -> str:
            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": TABI_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Input text:\n\n{text[:TABI_MAX_TEXT]}\n\nRespond with JSON only."},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            return (resp.choices[0].message.content or "").strip()

    elif backend == "ollama":
        import urllib.request

        base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

        def infer_one(text: str) -> str:
            payload = json.dumps(
                {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": TABI_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Input text:\n\n{text[:TABI_MAX_TEXT]}\n\nRespond with JSON only. No markdown."},
                    ],
                    "stream": False,
                    "options": {"temperature": 0},
                }
            ).encode()
            req = urllib.request.Request(
                f"{base_url}/api/chat",
                data=payload,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=180) as r:
                out = json.loads(r.read().decode())
            return out.get("message", {}).get("content", "").strip()

    else:
        print("--backend must be openai or ollama")
        return

    new_rows = []
    run_label = f"{backend}/{model_name}" + (" (dry-run)" if dry_run else "")
    for c in tqdm(chunks, desc=f"TABI ({run_label})"):
        cid = c["chunk_id"]
        if cid in done_ids:
            continue
        text = c.get("text", "") or ""
        try:
            raw_body = infer_one(text)
            parsed = _parse_tabi_json(raw_body)
            if strict:
                parsed = _tabi_strict_sanitize(parsed, min_grounds_chars=min_grounds_chars)
            claim = parsed.get("claim", "")
            err = parsed.get("_parse_error")
            if dedupe and claim and claim.upper() != "NONE":
                fp = _claim_fingerprint(claim)
                if fp in seen_fp:
                    continue
                seen_fp.add(fp)
            new_rows.append(
                {
                    "chunk_id": cid,
                    "article_filename": c.get("article_filename", ""),
                    "word_count": c.get("word_count", ""),
                    "backend": backend,
                    "model": model_name,
                    "claim": claim,
                    "grounds": parsed.get("grounds", ""),
                    "warrant": parsed.get("warrant", ""),
                    "bucket": parsed.get("bucket", "least_probable"),
                    "parse_error": err if err else "",
                    "raw_response_excerpt": (raw_body[:1200] + "…") if len(raw_body) > 1200 else raw_body,
                }
            )
        except Exception as e:
            err_s = str(e)
            new_rows.append(
                {
                    "chunk_id": cid,
                    "article_filename": c.get("article_filename", ""),
                    "word_count": c.get("word_count", ""),
                    "backend": backend,
                    "model": model_name,
                    "claim": "",
                    "grounds": "",
                    "warrant": "",
                    "bucket": "least_probable",
                    "parse_error": err_s,
                    "raw_response_excerpt": "",
                }
            )
            # Avoid burning 1k+ calls on a bad key (common classroom mistake: literal sk-...)
            if "401" in err_s or "invalid_api_key" in err_s.lower() or "incorrect api key" in err_s.lower():
                print(
                    "\nStopping early: OpenAI rejected the API key. "
                    "Export a real key, delete or rename the bad CSV if needed, then rerun with --resume."
                )
                break
            # Stop early if quota is exhausted; you can top up and rerun with --resume to retry failures.
            if "Error code: 429" in err_s and ("exceeded your current quota" in err_s.lower() or "billing" in err_s.lower()):
                print(
                    "\nStopping early: OpenAI quota exhausted (429). "
                    "Top up / fix billing, then rerun with --resume to retry remaining chunk_ids."
                )
                break
        if sleep_s > 0:
            time.sleep(sleep_s)

    if not new_rows:
        print("No new rows to write (everything skipped or empty selection).")
        return

    df_new = pd.DataFrame(new_rows)
    if resume and out_path.exists():
        try:
            df_old = pd.read_csv(out_path)
            df_out = pd.concat([df_old, df_new], ignore_index=True)
            n_concat = len(df_out)
            # Resume retries failed chunk_ids: old file still has error rows — keep latest row per chunk_id.
            df_out = df_out.drop_duplicates(subset=["chunk_id"], keep="last").sort_values("chunk_id", kind="stable")
            if len(df_out) < n_concat:
                print(
                    f"Merged resume: {n_concat} rows → {len(df_out)} unique chunk_id rows "
                    f"(kept latest per chunk_id; dropped {n_concat - len(df_out)} duplicates)."
                )
        except Exception:
            df_out = df_new
    else:
        df_out = df_new

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(out_path, index=False)
    print(f"Wrote {len(df_new)} new inference rows → {out_path} (file now has {len(df_out)} rows, one per chunk_id).")


def cmd_tabi_dedupe(path: Path):
    """Collapse duplicate chunk_id rows (keep latest row per chunk_id). Use after older resume runs that concat without dedupe."""
    if not path.exists():
        print(f"Missing {path}")
        return
    df = pd.read_csv(path)
    n0 = len(df)
    df = df.drop_duplicates(subset=["chunk_id"], keep="last").sort_values("chunk_id", kind="stable")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"tabi-dedupe: {n0} rows → {len(df)} unique chunk_id rows → {path}")


def cmd_tabi_high_confidence(
    input_path: Path,
    out_path: Path,
    mnli_threshold: float,
    require_bucket: str | None,
    require_non_none: bool,
):
    """
    Export a high-confidence implicit-gap subset from TABI outputs.

    Intended use: after `tabi-validate`, keep rows that (a) have a real claim and
    (b) pass an MNLI entailment threshold, optionally constrained to a bucket.
    """
    if not input_path.exists():
        print(f"Missing {input_path}")
        return
    df = pd.read_csv(input_path)
    for col in ["claim", "grounds", "warrant", "bucket"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)
    if "bucket" in df.columns:
        df["bucket"] = df["bucket"].str.lower().str.strip()

    if require_non_none and "claim" in df.columns:
        c = df["claim"].str.strip()
        df = df[(c != "") & (c.str.upper() != "NONE")]

    if require_bucket:
        b = require_bucket.lower().strip()
        if "bucket" not in df.columns:
            print("Input has no bucket column; cannot filter by bucket.")
        else:
            df = df[df["bucket"].eq(b)]

    if "mnli_entailment_prob" not in df.columns:
        print("Input has no mnli_entailment_prob. Run `tabi-validate` first.")
        return

    df["mnli_entailment_prob"] = pd.to_numeric(df["mnli_entailment_prob"], errors="coerce")
    df = df[df["mnli_entailment_prob"].notna() & (df["mnli_entailment_prob"] >= float(mnli_threshold))]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows → {out_path}")


def cmd_tabi_validate(input_path: Path, threshold: float, device: str | None):
    """Optional RoBERTa-MNLI entailment: premise = grounds+warrant, hypothesis = claim."""
    input_path = input_path.resolve()
    if not input_path.exists():
        print(f"Missing {input_path}")
        return

    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError:
        print(
            "Missing torch/transformers in THIS interpreter.\n"
            "If you use a project venv, install into it:\n"
            "  .venv/bin/python -m pip install -r requirements_part3_optional.txt\n"
            "(Plain `pip install` may target Anaconda base instead of .venv.)"
        )
        return

    df = pd.read_csv(input_path)
    tok_name = "roberta-large-mnli"
    tokenizer = AutoTokenizer.from_pretrained(tok_name)
    model = AutoModelForSequenceClassification.from_pretrained(tok_name)
    model.eval()
    dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    model.to(dev)

    id2label = model.config.id2label
    ent_id = None
    for k, v in id2label.items():
        if "entail" in str(v).lower():
            ent_id = int(k)
            break
    if ent_id is None:
        ent_id = 2  # common MNLI layout for RoBERTa

    entail_scores = []
    pass_flags = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="MNLI entailment"):
        claim = str(row.get("claim", "")).strip()
        if not claim or claim.upper() == "NONE":
            entail_scores.append(float("nan"))
            pass_flags.append(False)
            continue
        premise = _normalize_ws(str(row.get("grounds", "")) + " " + str(row.get("warrant", "")))
        if len(premise) < 8:
            entail_scores.append(float("nan"))
            pass_flags.append(False)
            continue
        inputs = tokenizer(premise, claim, truncation=True, max_length=512, return_tensors="pt").to(dev)
        with torch.no_grad():
            logits = model(**inputs).logits
        prob = torch.softmax(logits, dim=-1)[0, ent_id].item()
        entail_scores.append(prob)
        pass_flags.append(prob >= threshold)

    df["mnli_entailment_prob"] = entail_scores
    df["mnli_entailment_pass"] = pass_flags
    out_p = input_path.with_name(input_path.stem + "_validated.csv")
    df.to_csv(out_p, index=False)
    passed = sum(pass_flags)
    print(f"Entailment threshold {threshold}: pass {passed}/{len(df)} rows with non-empty claims")
    print(f"Wrote {out_p}")


def cmd_ablation_commands():
    """Write suggested shell commands for post-filter / hybrid ablations (requires re-extraction)."""
    txt = """# Part 3 ablation: re-run extraction with different flags (saves new CSV filenames).

# Baseline (post-filter ON, hybrid OFF — default in run_part2.py):
#   .venv/bin/python run_part2.py --model openai
# With hybrid merge:
#   .venv/bin/python run_part2.py --model openai --hybrid
# Post-filter OFF (no phrase filter after LLM):
#   .venv/bin/python run_part2.py --model openai --no-post-filter

# After each run, compare:
#   .venv/bin/python run_part2.py --compare

# Rename outputs between runs so files are not overwritten, e.g.:
#   mv Part2_Output/predictions_gpt4o_mini.csv Part2_Output/predictions_gpt4o_mini_nofilter.csv
"""
    out = PART3_OUTPUT / "ablation_commands.txt"
    out.write_text(txt)
    print(f"Wrote {out}")


def main():
    p = argparse.ArgumentParser(description="Part 3 utilities")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("clean-gold", help="Write gold_standard_cleaned.csv (drop citation-like sentences)")

    sp = sub.add_parser("semantic-compare", help="P/R/F1 with max(ROUGE-L, bow-cosine) match")
    sp.add_argument("--threshold", type=float, default=0.55)

    sub.add_parser("export-agreement", help="high_confidence_chunks.csv (all 3 models non-empty)")

    sp = sub.add_parser("implicit-template", help="implicit_gold_template.csv (chunk_id + empty column)")
    sp.add_argument("--n", type=int, default=50)

    sp = sub.add_parser("implicit-sample", help="implicit_annotation_sample.csv with text excerpts")
    sp.add_argument("--n", type=int, default=50)

    sub.add_parser("ablation-commands", help="Write ablation_commands.txt")

    sp = sub.add_parser("implicit-extract", help="Demo implicit gap for one chunk (OpenAI)")
    sp.add_argument("--chunk-id", type=int, required=True)

    sp = sub.add_parser("tabi-extract", help="Batch TABI (Claim/Grounds/Warrant/Bucket) → CSV")
    sp.add_argument("--backend", choices=["openai", "ollama"], default="openai")
    sp.add_argument("--model", type=str, default=None, help="Override OPENAI_MODEL / OLLAMA_MODEL")
    sp.add_argument("--max-chunks", type=int, default=None, help="Process only first N chunks after filters")
    sp.add_argument("--out", type=str, default=str(PART3_OUTPUT / "tabi_outputs.csv"))
    sp.add_argument("--chunk-ids-csv", type=str, default=None, help="Optional CSV with chunk_id column")
    sp.add_argument("--resume", action="store_true", help="Append; skip chunk_ids already in output")
    sp.add_argument("--dedupe", action="store_true", help="Skip duplicate claims (normalized) within session + existing file")
    sp.add_argument("--sleep", type=float, default=0.0, help="Seconds between API calls (rate limits)")
    sp.add_argument(
        "--dry-run",
        action="store_true",
        help="No API: write stub JSON rows (schema check / CI). Use real run for production.",
    )
    sp.add_argument(
        "--strict",
        action="store_true",
        help="Higher precision: post-filter weak/ungrounded outputs (may increase NONE).",
    )
    sp.add_argument(
        "--min-grounds-chars",
        type=int,
        default=30,
        help="Strict mode: minimum length of quoted grounds required to keep a non-NONE claim.",
    )

    sp = sub.add_parser("tabi-validate", help="Add RoBERTa-MNLI entailment columns to TABI CSV")
    sp.add_argument("--input", type=str, required=True)
    sp.add_argument("--threshold", type=float, default=0.4)
    sp.add_argument("--device", type=str, default=None, help="cuda or cpu")

    sp = sub.add_parser(
        "tabi-dedupe",
        help="In-place: collapse duplicate chunk_id rows (keep latest). Fixes older resume merges.",
    )
    sp.add_argument("--input", type=str, default=str(PART3_OUTPUT / "tabi_outputs.csv"))

    sp = sub.add_parser(
        "tabi-high-confidence",
        help="Export high-confidence implicit gaps from validated TABI CSV (MNLI threshold + optional bucket).",
    )
    sp.add_argument(
        "--input",
        type=str,
        default=str(PART3_OUTPUT / "tabi_outputs_validated.csv"),
        help="Validated TABI CSV (from tabi-validate).",
    )
    sp.add_argument(
        "--out",
        type=str,
        default=str(PART3_OUTPUT / "tabi_high_confidence.csv"),
        help="Output CSV path.",
    )
    sp.add_argument("--mnli-threshold", type=float, default=0.6)
    sp.add_argument(
        "--bucket",
        type=str,
        default="more_probable",
        help="Bucket filter (e.g., more_probable). Use empty string to disable.",
    )
    sp.add_argument(
        "--allow-none",
        action="store_true",
        help="If set, do not drop claim==NONE/empty (default drops them).",
    )

    args = p.parse_args()

    if args.cmd == "clean-gold":
        cmd_clean_gold()
    elif args.cmd == "semantic-compare":
        cmd_semantic_compare(args.threshold)
    elif args.cmd == "export-agreement":
        cmd_export_agreement()
    elif args.cmd == "implicit-template":
        cmd_implicit_template(args.n)
    elif args.cmd == "implicit-sample":
        cmd_implicit_sample(args.n)
    elif args.cmd == "ablation-commands":
        cmd_ablation_commands()
    elif args.cmd == "implicit-extract":
        cmd_implicit_extract(args.chunk_id)
    elif args.cmd == "tabi-extract":
        chunk_csv = Path(args.chunk_ids_csv) if args.chunk_ids_csv else None
        cmd_tabi_extract(
            backend=args.backend,
            model=args.model,
            max_chunks=args.max_chunks,
            out_path=Path(args.out),
            chunk_ids_csv=chunk_csv,
            resume=args.resume,
            dedupe=args.dedupe,
            sleep_s=args.sleep,
            dry_run=args.dry_run,
            strict=args.strict,
            min_grounds_chars=args.min_grounds_chars,
        )
    elif args.cmd == "tabi-validate":
        cmd_tabi_validate(Path(args.input), args.threshold, args.device)
    elif args.cmd == "tabi-dedupe":
        cmd_tabi_dedupe(Path(args.input))
    elif args.cmd == "tabi-high-confidence":
        bucket = args.bucket.strip()
        cmd_tabi_high_confidence(
            input_path=Path(args.input),
            out_path=Path(args.out),
            mnli_threshold=args.mnli_threshold,
            require_bucket=bucket if bucket else None,
            require_non_none=(not args.allow_none),
        )


if __name__ == "__main__":
    main()
