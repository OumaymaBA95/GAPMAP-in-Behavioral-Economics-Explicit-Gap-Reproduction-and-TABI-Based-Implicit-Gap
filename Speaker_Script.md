---
output:
  pdf_document: default
  html_document: default
  word_document: default
---
# Speaker Script 
**Group:** Oumayma Ben Aoun · Chau Tran · Elise DeLeon

***
## Slide 1 — Title
**Speaker: Oumayma** *(~30 sec)*

Good afternoon. I'm Oumayma, and along with Chau and Elise, our project explored how to find "knowledge gaps" in research papers — the places where authors directly state what's still unknown. Phrases like "further research is needed" or "this remains unclear."

Our central question: can large language models reliably find these for us? To investigate, we adapted a framework called GAPMAP, originally built for biomedical literature, and applied it to 107 papers from the Journal of Behavioral and Experimental Economics.

***
## Slide 2 — Knowledge gaps
**Speaker: Oumayma** *(~110 sec)*

Before we get into the methods, it helps to clarify that there are two kinds of gaps, and we treat them very differently.

The first is **explicit** — the authors directly write "this is unclear" or "further research is needed." These are relatively easy to detect because of their specific phrasing.

The second is **implicit** — gaps the authors never state outright, but that you can infer from the design or scope of the study. For example, if a paper only tests college students, there's an implicit gap about whether the findings extend to other populations — even if the authors never put it in those terms.

The original GAPMAP paper showed that LLMs can identify both kinds in biomedical literature.

Our pipeline also draws on three other established methods. I'll name them quickly — don't worry if these aren't familiar yet, each one will come back later when we walk through the pipeline. From philosophy, we borrow Toulmin's classical argument framework — the idea that any argument has three parts: a Claim, the Grounds for it, and a Warrant explaining why those grounds support the claim. From NLP, we use natural language inference, the task of deciding whether one sentence logically follows from another. That's what our RoBERTa validator — a separate, smaller language model — was trained to do. And from summarization, we use ROUGE-L, a standard metric that scores how much two pieces of text overlap.

Our question was whether the same approach still works in behavioral economics, which has a very different writing style and a much higher density of explicit gap phrases.

A quick look at our dataset.

***
## Slide 3 — Dataset
**Speaker: Oumayma** *(~70 sec)*

Our dataset is 107 articles from the Journal of Behavioral and Experimental Economics. We extracted the text with a PDF reader, cleaned it up, and divided each paper into text sections of up to 1,000 words while preserving complete sentences. That gave us 1,367 sections total.

From those, we manually labeled 93 sections ourselves to mark every explicit gap statement we could find. That hand-labeled set serves as our reference standard — our "answer key" — when we score the different methods.

Why behavioral economics? Two reasons. First, it's a different field from the biomedical setting GAPMAP was originally designed for, so we wanted to test whether the framework still transfers. Second, papers in this field frequently use phrases like "further research is needed" — and as you'll see in a moment, that turns out to matter quite a bit for our results.


***
## Slide 4 — Pipeline
**Speaker: Chau** *(~90 sec)*

I'll walk you through how the pipeline is built. It has two parallel tracks running on those 1,367 sections.

On the **explicit track** — the left side of the slide — we prompt three language models, GPT-4o, GPT-4o-mini, and Llama 3.2, to extract gap sentences from each section. We then run a filter that retains only sentences containing common gap phrases. Finally, we score each model against our 93 hand-labeled sections.

On the **implicit track** — the right side — we ask the model to do something harder: construct a small structured argument for each potential hidden gap. Each argument has three parts. A **Claim** about what's missing. The **Grounds**, a direct quote from the paper supporting the claim. And a **Warrant**, a brief explanation of why those grounds support that claim.

We then run every argument through a separate model — RoBERTa, which is trained for logical-validity checks — to see whether each argument actually holds together. After filtering, that leaves us with 842 high-confidence implicit gaps.

Now I'll walk you through our main results.


***
## Slide 5 — Results
**Speaker: Chau** *(~80 sec)*

Here's the most striking finding.

GPT-4o performs strongly. The two smaller models perform noticeably worse — about what you'd expect.

But look at the leftmost bar. That isn't a language model at all. It's just a script that scans each section for common gap phrases — no model in the loop. And that simple script **outperforms every LLM we tested**, scoring 0.91 F1 against GPT-4o's 0.88.

The reason is that behavioral economics authors frequently use exactly the phrases our regex looks for. So the regex catches almost every gap with near-perfect precision. The LLMs, in contrast, often generate extra sentences that sound plausible but don't match the specific gaps we had labeled.

Now, you might reasonably wonder: is this ranking robust, or could it be an artifact of our particular sample? And is our scoring even fair to the LLMs? Let me address both.


***
## Slide 6 — Are these results statistically robust?
**Speaker: Chau** *(~70 sec)*

To check whether this ranking is robust or just an artifact of our sample, we re-ran the evaluation 1,000 times, each time with a different random subsample of our 93 sections. This is a standard technique called bootstrapping.

The regex came out on top every time. GPT-4o beat Llama 3.2 in 100% of resamples, and beat GPT-4o-mini in 96.5%. So the ranking isn't a fluke — it holds up.


***
## Slide 7 — Why do the smaller LLMs underperform?
**Speaker: Elise** *(~75 sec)*

I'll explain why the smaller models did so much worse.

The main difference is in incorrect predictions. GPT-4o produced about 33 wrong predictions across our test sections. The two smaller models each produced over 148 — roughly four-and-a-half times as many.

When we examined those wrong predictions, they were almost all generic boilerplate. Sentences like "Further research is needed to replicate these findings." They sound reasonable, and they contain the right cue words, but they don't correspond to any specific gap we had labeled, so they're scored as wrong.

We also ran a focused experiment to see what the phrase filter is really doing. The filter helps substantially — it acts as a precision floor. But layering the regex extractor on top of the LLM output adds nothing. Anything the regex would surface, the LLM has already produced; anything it hasn't, the regex can't find either.

***
## Slide 8 — Caveats
**Speaker: Elise** *(~85 sec)*

Before drawing final conclusions, we want to highlight three caveats to that headline finding.

**First**, our scoring metric slightly penalizes verbosity. The LLMs do catch one extra real gap that the regex misses — 111 versus 110 — but if a model phrases the same gap three different ways, two of those count as wrong even though they're really paraphrases of the same idea. So the metric quietly rewards methods that don't repeat themselves.

**Second**, this whole story is specific to behavioral economics, where explicit gap phrases are extremely common. In a field where authors are subtler about flagging limitations — like theoretical economics or finance — the regex would almost certainly do worse, and the LLMs' advantage would grow.

**Third**, and this is a genuine limitation: only one of us did the hand-labeling for our reference set. That means our "answer key" reflects one team member's judgment. Ideally, we'd have two or three independent labelers comparing notes.

With those caveats noted, let's turn to where the LLMs clearly add value.


***
## Slide 9 — Implicit gaps
**Speaker: Elise** *(~95 sec)*

Implicit gaps are limitations the authors never state directly. So a regex cannot help us here at all — there's nothing literal to match against.

This is where the LLMs deliver clear value.

We had GPT-4o build a Claim/Grounds/Warrant argument for every section in the corpus, then ran each argument through the RoBERTa validator. That left us with 842 implicit gaps that passed our validation step.

Here's one example, from a paper on loss aversion. The model proposed this **Claim**: "The mechanism by which loss aversion interacts with intertemporal discounting in this sample remains unclear."

For the **Grounds** — which must be a direct quote from the paper — it pulled out: "We do not directly measure intertemporal preferences in this study."

And the **Warrant** tied them together: "Without a discounting measurement, the interaction can't be tested at the individual level."

The authors never stated any of this as a limitation. The model identified it by reasoning about the study's design. A regex cannot make this kind of connection — that requires actually understanding the paper.

To sanity-check the validator, we hand-reviewed 20 of those 842 candidates ourselves. About 70% turned out to be real implicit gaps. That's a rough estimate rather than a benchmark, but it tells us the validator is mostly keeping the right things.

***
## Slide 10 — How we compare to GAPMAP
**Speaker: Elise** *(~70 sec)*

We also wanted to compare our results to the original GAPMAP paper. We used the same method — just on a different set of papers — and the most interesting finding is that the model rankings actually flip.

On our behavioral economics corpus, GPT-4o leads at 0.88 F1, with mini trailing at 0.70. But on GAPMAP's biomedical corpus, those rankings reverse — mini outperformed 4o, 0.81 to 0.74.

Our best interpretation is cue-phrase density. Behavioral econ papers use stock phrases like "further research is needed" constantly, and mini tends to over-generate sentences that just sound like gaps. On a cue-dense corpus like ours, that hurts mini badly. On GAPMAP's less templated biomedical text, the same tendency apparently helped it surface real gaps that the bigger model missed.

The broader point is that even when the leaderboard flips, the overall framework still transfers — you just have to expect the rankings to look different in each new domain.

***
## Slide 11 — Takeaways
**Speaker: Oumayma** *(~80 sec)*

Three main takeaways from this work.

**First**: if your field relies heavily on stock phrases like "further research is needed" — and many social-science fields do — you may not actually need an LLM for explicit gaps. A simple regex can match or even outperform the models, at essentially no cost.

**Second**: for implicit gaps — the ones authors don't state directly — LLMs are doing genuine work that simpler methods cannot replicate. The hand-check we showed earlier flagged roughly 70% of those implicit-gap candidates as real. So this capability is genuinely additive over keyword search.

**Third**: the natural next steps are clear. We'd like to test this on fields where authors are subtler — like theoretical economics or finance — build a larger reference set with multiple independent labelers, and explore smarter ways to combine the cue-phrase method with the LLM rather than treating them as alternatives.

Thank you. We're happy to take any questions.

***

## Quick reference: who speaks when

| Slide | Speaker | Topic | Time |
|-------|---------|-------|------|
| 1. Title | Oumayma | Hook | 30s |
| 2. Knowledge gaps | Oumayma | Setup + prior work | 110s |
| 3. Dataset | Oumayma | Data | 70s |
| 4. Pipeline | Chau | Methods | 90s |
| 5. Results | Chau | Headline finding | 80s |
| 6. Robustness | Chau | Stability check | 70s |
| 7. Failure analysis | Elise | Why LLMs miss | 75s |
| 8. Caveats | Elise | Limitations | 85s |
| 9. Implicit gaps | Elise | Where LLMs add value | 95s |
| 10. vs. GAPMAP | Elise | Comparison | 70s |
| 11. Takeaways | Oumayma | Conclusion | 80s |

**Per person:** Oumayma ~4:50, Chau ~4:00, Elise ~5:25
**Total runtime:** approximately 14 minutes. Allow 2-3 minutes for questions.

***

## Likely questions — be prepared for these

**"What is ROUGE-L exactly?"**
ROUGE-L compares two pieces of text by identifying the longest run of words they share in the same order. It returns a score between 0 and 1, where higher means more overlap. We use it to compare each method's output against our hand-labeled gaps. The main reason we chose it is that the original GAPMAP paper uses ROUGE-L as well, so our numbers are directly comparable to theirs.

**"What is RoBERTa?"**
RoBERTa is a different pretrained language model, separate from GPT-4o or Llama. We use a version that's been fine-tuned specifically for natural language inference — that is, deciding whether one sentence logically follows from another. In our pipeline, RoBERTa serves as a quality-control step: it checks whether the Grounds and Warrant actually support the Claim the LLM produced. If they don't, we drop the candidate.

**"Why ROUGE-L rather than a more semantic metric?"**
Primarily for comparability with GAPMAP. We did run a sensitivity check using a more flexible semantic matching method, and the model rankings came out the same. The metric choice accounts for at most about 0.027 of the F1 difference between methods — far too small to alter any of our conclusions.

**"Did you really only have one team member label the data?"**
Yes, and we acknowledge that as a limitation throughout the paper. The 70% implicit-gap accuracy figure should be read as an order-of-magnitude estimate, not a benchmark number. Bringing in additional independent labelers is the first item on our future-work agenda.

**"Will the cue-phrase baseline generalize to other fields?"**
We don't expect it to. Behavioral economics papers are unusually rich in stock phrases like "further research is needed." In a field where authors signal limitations more subtly — theoretical economics or finance, for instance — the regex would likely miss far more gaps, and the LLMs' relative advantage would grow. Testing that explicitly is one of our future-work items.

**"Why didn't you fine-tune a model for gap detection?"**
That was outside the scope of this project. Our goal was to reproduce GAPMAP's pipeline rather than modify the underlying models. Fine-tuning on labeled gap data would be a reasonable extension if such a labeled dataset existed — we don't have one yet.

**"How much did the project cost in API usage?"**
GPT-4o calls were the main expense, since we ran them across all 1,367 sections. The Llama experiments, the regex baseline, the RoBERTa validation step, and the bootstrap evaluation all ran free on local hardware. We also kept API costs down by running each prompt configuration only once.

**"Why 0.55 as the ROUGE-L threshold?"**
That's GAPMAP's threshold, which we adopted for comparability. We did test 0.50 and 0.60 as a sensitivity check, and the model rankings were consistent across all three settings.

**"How does your implicit-gap method differ from GAPMAP's?"**
We use the same Claim / Grounds / Warrant prompt format as GAPMAP — that structure originates from a classical argument framework in philosophy. Our main addition is the separate logical-validity check using RoBERTa MNLI. The other difference is that GAPMAP has a curated implicit-gap test set for biomedical text, which we don't have an equivalent for in behavioral economics. That's why our implicit-gap results are based on a 20-row hand-check rather than a full benchmark.
