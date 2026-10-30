# Grading rules for the evaluation set

Source: development steps C and N of the private working repository (Grading, Decision rule). Frozen with `eval/items.jsonl`. After the freeze the scored items and these rules do not change. Practice items may refine grading notes only in a separate file (`eval/practice-notes.md`).

## Items

`eval/items.jsonl` holds 70 items, one JSON object per line. 60 have `"set": "scored"` (20 `exact`, 20 `paraphrase`, 20 `stale`); 10 have `"set": "practice"` (4 exact, 3 paraphrase, 3 stale). Only scored items count in results.

Fields: `id`, `set`, `kind`, `source` (corpus source name), `question`, `key_facts`, `quotes` (corpus-relative `path`, 1-based `line`, `text` that is a substring of that line), and for stale items a `stale` block: `superseded` and `current` (each with `path`, `line`, `text`, `fact`), `markers` and `basis`. `eval/check_items.py` verifies every path and line.

`key_facts` is a list. Each entry is a string, or a list of alternative strings (any one satisfies the entry). An alternative that starts with `=` is exact: the `=` is removed, then only rule 1 below applies to it (no content-word fallback).

## 1. Code grading (applied to every answer)

Grade the final answer text only. Remove any text between `<think>` and `</think>` first. An empty answer, or one that only says it does not know, is incorrect.

Normalisation, applied to answers, key facts and markers alike, in this order: Unicode NFKC and lowercase; replace `*` and the multiplication sign with ` times `; replace `+` with ` plus `; replace a hyphen, en dash or minus sign that has whitespace on both sides, and any unicode minus or en dash, with ` minus `; then replace every run of characters outside `0-9a-z` with one space and split on spaces. The result is a token list. So `4 * dimensions + 8` becomes `4 times dimensions plus 8`, `4 * dimensions - 8` becomes `4 times dimensions minus 8`, `--filter-sample-seed` becomes `filter sample seed`, and `4GB` and `4 GB` differ (items list both where it matters).

A key fact is present when, for at least one of its alternatives, either:

1. the alternative's tokens appear in the answer's tokens as a contiguous run (whole tokens, so `api embed` does not match `api embeddings`); or
2. at least 80 percent of the alternative's content words appear among the answer's tokens. Content words are the alternative's distinct tokens that are not in this stop list: `a an and are as at be by for from has have in is it its of on or that the this to was were will with`.

An answer is correct when every entry of `key_facts` is present.

### Stale items

A stale item is also incorrect when the answer states a stale marker. Marker matching uses rule 1 only (contiguous tokens, no fallback). Split the answer into clauses at `;`, at sentence ends (`.`, `!`, `?` followed by whitespace), at newlines, and at the words `but`, `however`, `whereas`, `while`. Do not split at colons or parentheses. Tokenise each clause. Each occurrence of a marker (tokens `M`, at positions `i` to `i+n`) counts as stated unless one of three exemptions binds to that occurrence:

1. Verbatim quote. The item's own quoted lines (`quotes[].text` and `stale.current.text`, normalised) contain a run of at least 5 consecutive tokens that includes this marker occurrence and appears identically in the clause around it. This lets an answer quote the documented line, which may describe the old term, without being marked stale.
2. Cue before the marker. Look at the token just before the marker, first skipping up to 3 tokens from `the a an use using to`. The occurrence is exempt if that token is one of `not never avoid without formerly previously earlier old older former legacy previous outdated obsolete from was were`, or starts with `deprecat supersed replac renam remov dropp`, or ends one of the pairs `no longer`, `instead of`, `rather than`. So `not display`, `instead of typical_p`, `the old ServiceContext`, `deprecated ibm:bam` and `from extended` are exempt; `do not use label, use display` is not, because the token before `display` (after skipping `use`) is `label`.
3. Cue after the marker. Look at the tokens after the marker, first skipping up to 8 tokens that are in the item's other marker tokens or in `is are was were been be being has have had now also since already officially currently long considered marked flagged labelled labeled upstream by a an the and or all both class classes object objects field fields parameter parameters option options alias flag flags property term terms name names strategy provider endpoint endpoints method methods`. The occurrence is exempt if the next token starts with `deprecat supersed replac renam remov dropp obsolet outdat unsupport sunset legacy` or is `old` or `older`. So `display is deprecated`, `AgentRunner and AgentWorker are deprecated` and `typical_p (deprecated)` are exempt; `Python 3.9 is supported and only Python 3.8 is deprecated` is not, because `only` is not a skipped token.

A cue anywhere else in the answer exempts nothing. Worked cases: "use `external`, or use `extended` if no compression is needed" is incorrect (nothing binds to `extended`); "use `options.transform`; `options.postprocess` is a deprecated alias" is correct; "use `options.postprocess`" is incorrect; "choose typical_p instead of top_p or min_p" is incorrect; "use watsonx or ibm:bam" is incorrect.

### Citations (arm A3 only)

A3 asks the model to quote the line it relied on and cite its path. A citation counts only when `engine/bin/cerebrollm verify` prints `OK` for it. A citation that fails verify, or is missing, counts as no citation. Report the verify pass rate separately. Correctness of the answer is graded by the rules above and is not changed by the citation.

## 2. Owner grading (pending on the owner)

The owner grades a random sample of 20 answers per model, blind to the arm, drawn with a fixed seed. Owner grades are not available overnight; the blind sheets are prepared and agreement is reported as pending.

## 3. Model grader (development step N4)

A model grader is used only if it agrees with the owner on the 20-answer sample at least 18 times in 20 on each sheet. development step N4 (2026-10-29) sets up the grader and the test; the rubric below is frozen before the first validation run, and a failed validation is not followed by a rubric change and a rerun on the same 40 samples.

Grader: `eval/judge.py`, `gpt-oss:20b` (digest in `engine/models.toml`) on the local Ollama, one call per answer, reasoning effort medium, temperature 0, JSON output `{"verdict": "Y"|"N", "reason": "<one sentence>"}`. Inputs: question, reference lines, key facts, for stale items the current and out-of-date statements, and the answer with any `<think>` block removed. Rubric (the wording in `judge.py` `RUBRIC` is the text of record):

1. Y when the answer gives the reference fact as its answer and nothing in it contradicts the reference.
2. Naming the out-of-date value to reject or explain it does not fail a stale item; recommending it does.
3. N when the answer says it does not know or lacks the information, even if it then mentions the fact.
4. Citations and style do not change the verdict.

A reply that does not parse is retried once, then recorded as `error`, never as Y or N. The keyword grade of section 1 stays as a second column.

## 4. Decision rule

For each model, take the per-question majority over the runs of an arm (five runs for A0 and A3 on both models, five runs per arm for the local model, one run for A1 and A2 on the hosted model; with one run the majority is that run). Per kind (exact, paraphrase, stale) and overall, count questions where A3 is correct and the comparison arm is not, and the reverse. Apply a two-sided sign test at the 5 percent level for A3 against A0, A1 and A2; ties are dropped. Report pass^5 for A0 and A3: the share of questions answered correctly in all five runs.

Report a negative or inconclusive result as it is. Never report a number that is not in a saved result file.

## Known limits of code grading

The stale check is a keyword heuristic. It has false passes (an answer that asserts the stale fact in words that match none of the markers, or whose wording happens to satisfy an exemption) and false fails (an answer that describes the old behaviour in a form the exemptions do not recognise, for example "extended was used before 0.6.0", or that quotes a source line only partly). Key-fact matching has the same two error types: the 80 percent content-word fallback can accept an answer that is partly wrong, and strict token matching can reject a correct paraphrase. No code-based grade is evidence of correctness on its own. The owner's blind 20-answer sample per model is the measure of this error: report each disagreement between the owner's grade and the code grade, with the item id, in `RESULTS.md`. Do not retune the cue rules after the first scored run.
