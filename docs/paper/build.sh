#!/bin/sh
# Builds the paper's PDFs from docs/paper.md and its translations (docs/paper.<lang>.md) with pandoc and LaTeX (tectonic).
#   sh docs/paper/build.sh            # every language
# Needs pandoc 3, tectonic and poppler (pdftocairo). The figures are compiled first, from
# docs/figures/*.tex and their tables in docs/figures/data/ (tools/paper_figures.py), to PDF
# for the paper and SVG for the Markdown.
set -e
here=$(cd "$(dirname "$0")" && pwd)
docs=$(dirname "$here")
for f in "$docs"/figures/*.tex; do
  [ -e "$f" ] || continue
  case $(basename "$f") in _*) continue ;; esac   # shared preamble, not a figure
  b=${f%.tex}
  if [ ! -e "$b.pdf" ] || [ ! -e "$b.svg" ] || [ "$f" -nt "$b.pdf" ] || [ -n "$(find "$docs/figures" -name "*.tex" -newer "$b.pdf" 2>/dev/null)" ] || [ -n "$(find "$docs/figures/data" -newer "$b.pdf" 2>/dev/null)" ]; then
    tectonic -X compile --outdir "$docs/figures" "$f" 2>&1 | grep -v "^note:" || true
    pdftocairo -svg "$b.pdf" "$b.svg"
  fi
done
build() { # $1 source, $2 output
  pandoc "$docs/$1" --from markdown+tex_math_dollars+raw_tex --template "$here/template.tex" \
    --lua-filter "$here/figures.lua" --citeproc --bibliography "$here/references.bib" --csl "$here/ieee.csl" \
    -H "$here/style.tex" -H "$here/colours.tex" --resource-path "$docs:$here" --number-sections --toc --pdf-engine=tectonic -o "$docs/$2"
}
base=n-ways-addressing-cabo-verde
for src in "$docs"/paper.md "$docs"/paper.*.md; do
  [ -e "$src" ] || continue
  name=$(basename "$src")
  case $name in paper.md) lang=en ;; *) lang=${name#paper.}; lang=${lang%.md} ;; esac
  build "$name" "$base-$lang.pdf"
done
