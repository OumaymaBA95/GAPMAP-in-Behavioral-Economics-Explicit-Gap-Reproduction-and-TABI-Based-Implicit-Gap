#!/usr/bin/env bash
# Build a nicely styled PDF of Speaker_Script.md
set -euo pipefail

cd "$(dirname "$0")"

SRC=Speaker_Script.md
TMP=.script_build.md
OUT=Speaker_Script.pdf

# 1) Pre-process the markdown:
#    * drop the YAML front matter (lines between the first two `---` lines)
#    * drop the redundant H1 + the next 3 lines (group, time, separator)
#      -- we'll set those via pandoc metadata instead
#    * convert `**Speaker: X** *(~Y)*` lines into a raw LaTeX \speakerline{X}{Y}
python3 <<'PY' > "$TMP"
import re, io, sys
src = open("Speaker_Script.md","r",encoding="utf-8").read()

# strip YAML front matter
src = re.sub(r"\A---\n.*?\n---\n", "", src, count=1, flags=re.DOTALL)

# drop H1 + the two metadata lines + the trailing `---` separator
src = re.sub(
    r"\A# [^\n]*\n(?:\*\*[^\n]*\n){0,3}\n?---\n",
    "",
    src,
    count=1,
)

# Speaker line -> raw LaTeX chip (must be a block of its own for raw_tex)
def speaker(m):
    name = m.group(1).strip()
    dur  = m.group(2).strip()
    return f"\n\\speakerline{{{name}}}{{{dur}}}\n"

src = re.sub(
    r"\*\*Speaker:\s*([^*]+?)\*\*\s*\*\(\s*~?\s*([^)]+?)\s*\)\*",
    speaker,
    src,
)

sys.stdout.write(src)
PY

# 2) Compile via pandoc + xelatex
pandoc "$TMP" -o "$OUT" \
    --pdf-engine=xelatex \
    --include-in-header=script_style.tex \
    -V geometry:margin=0.95in \
    -V mainfont="Avenir Next" \
    -V sansfont="Avenir Next" \
    -V monofont="Menlo" \
    -V fontsize=11pt \
    -V colorlinks=true \
    -V linkcolor=accent \
    -V urlcolor=accent \
    -V linestretch=1.15 \
    -M title="Speaker Script" \
    -M subtitle="GAPMAP $\\times$ Behavioral Economics" \
    -M author="Oumayma Ben Aoun  \\enspace$\\cdot$\\enspace Chau Tran  \\enspace$\\cdot$\\enspace  Elise DeLeon" \
    -M date="Total runtime: \\textasciitilde 13 minutes \\enspace$\\cdot$\\enspace 11 slides" \
    -f markdown-yaml_metadata_block+raw_tex \
    --highlight-style=tango \
    --top-level-division=section

# 3) Clean up
rm -f "$TMP"
echo "Wrote $OUT"
