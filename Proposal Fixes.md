# Fixes for the Research Proposal

Companion to *Research Proposal_ OCR or Pixels_ Telugu & Tamil Document RAG.md*. Each fix says what to change in the proposal and what to do in practice.

> **Status (draft v2 of the proposal):** Fixes 1–7 have been applied, with the corrections listed under *Fix 9* at the end. Of Fix 8, the metadata split and the footnotes are done; the remaining checks are still open.

Priority: **Fix 1, 3 and 4 first.** Fixes 1 and 3 can silently make results wrong; Fix 4 is what reviewers will ask about.

---

## Fix 1: Render pages correctly (Telugu/Tamil letter shaping)

**Problem:** Pillow without the raqm library draws joined letters (e.g. క్ష) as broken pieces, so "ground truth" pages are wrong.

**What to do:**
- Render pages as HTML in a headless browser (Playwright + Chromium) and screenshot them to PNG. Browsers shape Indic text correctly.
- If you use Pillow anyway, confirm shaping is on:
  ```python
  from PIL import features
  assert features.check("raqm"), "raqm missing: Indic text will render wrongly"
  ```
- Before generating the full corpus, render ~20 pages with conjunct-heavy text and check them by eye.

**Change in proposal (Section 7.1):** add one sentence: *"Pages are rendered with a HarfBuzz-based text shaper (Chromium) to ensure correct conjunct and matra rendering; a sample is manually inspected."*

---

## Fix 2: Use a reliable akshara splitter

**Problem:** `regex` `\X` (grapheme clusters) does not always equal aksharas. Telugu conjuncts are kept together only in newer Unicode versions; Tamil is handled differently.

**What to do:**
- Write a small rule-based akshara splitter: an akshara = (consonant + virama)* + consonant + optional matra/modifier, or an independent vowel.
- Test it on a hand-made list of ~50 tricky words per script (conjuncts, words ending in virama, anusvara/visarga).
- Record the exact Python and library versions in the paper.

**Change in proposal (Section 7.3):** replace "Python's `regex` module splits text into these with the `\X` pattern" with *"a rule-based akshara segmenter, validated on a hand-checked word list for each script."*

---

## Fix 3: Stop the questions from favouring keyword search

**Problem:** LLM-generated questions copy words from the page, which makes BM25 look better and visual retrievers look worse than in real use.

**What to do:**
- When generating questions, instruct the LLM to paraphrase and avoid copying phrases from the passage.
- Keep two question sets: **extractive** (normal) and **paraphrased**. Report results on both.
- Measure word overlap between each question and its page and report the average. Optionally show results split by low/high overlap.

**Change in proposal (Section 7.1, QA pairs):** add *"A paraphrased subset with low lexical overlap is created to avoid favouring lexical retrievers; question–page overlap is reported."*

---

## Fix 4: Add two missing baselines

**Problem:** Reviewers will ask whether your methods beat the obvious simple alternatives.

**What to do:**
- **Character n-gram BM25:** index plain character n-grams (e.g. 3–5) alongside akshara n-grams. This shows whether *akshara* units specifically help (supports H2).
- **LLM OCR correction:** pass OCR text through an LLM with the prompt "correct OCR errors in this Telugu text, do not change the meaning", then index the corrected text. Compare against M1 and M2.

**Change in proposal:**
- Section 7.4, OCR path: add *(e) character n-gram BM25* and *(f) LLM post-corrected OCR text*.
- Section 7.6: note that M1 and M2 are compared against both baselines.

---

## Fix 5: Find all correct pages for each question

**Problem:** Wikipedia repeats facts, so a question may be answerable from more than one page. Only one is labelled correct, so good systems get marked wrong.

**What to do:**
- For each question, run BM25 and BGE-M3 on clean text and take the top 5–10 pages.
- Check these pages (by hand or with an LLM, then spot-check) and mark any that also answer the question as relevant.
- Discard questions that are answerable from too many pages (too generic).

**Change in proposal (Section 7.1):** add *"Additional relevant pages are identified by pooling top-ranked candidates from multiple retrievers and verifying them."*

---

## Fix 6: Check OCR confidence before relying on it

**Problem:** The M4 fusion method trusts OCR confidence, but engines (especially Tesseract) are often confidently wrong on Indic scripts, and some give no scores.

**What to do:**
- For each engine, plot page-level mean confidence against actual akshara error rate. Report the correlation.
- Add a backup signal that needs no confidence score: the **fraction of words on the page not found in a Telugu/Tamil word list** (built from Wikipedia).
- Run M4 with confidence, with the backup signal, and with both.

**Change in proposal (Section 7.6, M4):** add *"Confidence calibration is checked per engine; an out-of-vocabulary rate is used as a confidence-free alternative weighting signal."*

---

## Fix 7: Make the timeline realistic

**Problem:** 400 hand-checked questions plus all indexes plus E1 and E3 in three weeks is too much for one person.

**What to do:**
- Set the ICDAR target to **~250 verified Telugu questions**; grow to 400 after submission.
- Start question checking in parallel with OCR runs (late November) instead of waiting until December.
- Build the BM25 and BGE-M3 indexes first; add visual retrievers after.

**Change in proposal (Sections 7.1 and 9):** change "about 400" to "about 250 for the first submission, extended to 400 afterwards", and adjust the timeline table.

---

## Fix 8: Small checks

- [ ] Confirm ICDAR 2027 abstract/paper deadlines, page limit, and preprint policy on the official site.
- [ ] Verify that references 5 (LëtzCross), 7 (Chitrapathak) and 8 (ORB) exist with the listed arXiv IDs.
- [x] Move DocLens-VLM and the bodhan-ai model card to footnotes, or remove them; re-measure OCR accuracy on your own data.
- [x] Split the metadata line at the top of the proposal (author, advisor, venue) onto separate lines.
- [ ] Anonymise the author line for the double-blind submission version.

---

## Fix 9: Corrections to the fixes above (applied in draft v2)

- **Fix 2:** one akshara rule does not suit both scripts. Tamil treats a consonant with pulli (mei letter) as its own unit, and only க்ஷ and ஸ்ரீ join; Telugu keeps conjuncts together. Separate rules per script, with ZWJ/ZWNJ and nukta handled.
- **Fix 4:** the LLM correction prompt covers Tamil as well as Telugu.
- **Fix 5:** pool candidates from a visual retriever too, not only BM25 and BGE-M3, so relevance labels do not favour text retrieval. Report Hit@k, since questions can have several relevant pages.
- **Fix 6:** the OOV rate is noisy for agglutinative Telugu and Tamil. Use akshara/character n-gram language-model perplexity as the main confidence-free signal, with OOV rate as the simpler variant. H4 is reworded to match.
- **Fix 7:** both languages are now full parts of the plan: ~200 verified questions per language for submission, ~400 afterwards. The timeline absorbs the extra work from Fixes 3–6.
- **New: LLM contamination.** Telugu and Tamil Wikipedia are likely in LLM training data. E4 adds a closed-book baseline, and real-scan results are reported separately.
- **New: consistency.** §1 and §6 now agree that the benchmark covers both languages. An optional English reference set is planned for after submission.
- **New: references.** VisRAG gets an arXiv ID (2410.10594, to verify); missing authors are marked for completion.
