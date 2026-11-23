# Foundation and CPU Pilots Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the script-aware text core (akshara segmentation, n-grams, noise injection, alignment, rule-based repair) and the page pipeline (render → degrade → Tesseract), then run pilots P1, P2, P3, P8 and the first M6 test on CPU, so that the riskiest assumptions are checked before any GPU or data spending.

**Architecture:** One Python package `ocrrag` under `src/`, one module per responsibility, all pure functions over `str` and file paths. Pilot scripts in `pilots/` import the package and write Markdown reports to `results/pilots/`. Nothing in this plan needs a GPU, Modal or network access except Task 0's sample text.

**Tech Stack:** Python 3.13, pytest, Playwright (Python) driving the pre-installed Chromium, Pillow, NumPy, Augraphy, Tesseract 4 with `tel` and `tam` packs (apt).

**Spec:** `Research Proposal_ OCR or Pixels_ Telugu & Tamil Document RAG.md` (draft v2), plus the review decisions recorded in `Project Overview.pdf` §9–10 (train/test split for the error model, decomposed-akshara variant, pilot pass criteria, M6 reconstruction idea).

## Project roadmap (five plans)

This plan is **Plan 1**. Each later plan is written when the previous one's results are in, because pilot outcomes change their design.

| Plan | Scope | Runs on | Starts when |
|---|---|---|---|
| **1. Foundation and CPU pilots** (this file) | Text core, page pipeline, P1, P2, P3, P8, M6 rule repair | This container (CPU) | Now |
| 2. Modal infrastructure and corpus | Modal app and Volume; Telugu/Tamil Wikipedia download and cleaning; passage sampling; benchmark and distractor pages; Tesseract (Modal CPU) and Surya (L4) at scale; L4 vs A10G cost check | Modal CPU + L4 | Plan 1 done |
| 3. Benchmark | LLM question drafting (extractive and paraphrased), lexical overlap, export for hand checking, pooling and relevance checking (P9), real-scan subset (P4), dev/test splits | Modal + author | Plan 2 corpus ready |
| 4. Retrieval and core experiments | BM25 variants, BGE-M3, hybrid, ColPali/ColQwen2.5/ColSmol (L4); P5, P6, P7; E1, E2, E3; M1, M3, M4; M6 stage 2 (lexicon + confusion-model correction); metrics and paired bootstrap | Modal L4 | Plan 3 questions verified |
| 5. Generation, training methods, paper | E4 with closed-book baseline; M2 (BGE-M3 fine-tune); M5 (ColQwen2.5-3B LoRA); figures and tables | Modal L4 | Plan 4 results |

## Global Constraints

- Python `>=3.13`; package `ocrrag` in `src/ocrrag/`; tests in `tests/`; run with `pytest -q`.
- No GPU, no Modal, no network in this plan's code. Tesseract runs as a subprocess.
- Chromium path: launch Playwright with `executable_path` taken from env `OCRRAG_CHROMIUM`, default `/opt/pw-browsers/chromium`. Never run `playwright install`.
- Fonts used in this plan: `Noto Sans Telugu`, `Noto Serif Telugu`, `Noto Sans Tamil`, `Noto Serif Tamil` (installed via `fonts-noto-core`).
- Language codes everywhere: `"te"` (Telugu) and `"ta"` (Tamil). Tesseract codes: `te → tel`, `ta → tam`.
- Every random operation takes an explicit `random.Random` or integer `seed`; same seed → same output.
- Text functions never normalise silently. Unicode NFC is applied only by `ocrrag.text.normalize()` and by `align.py` before comparing.
- `data/` is git-ignored except `data/samples/`. Pilot reports (`results/pilots/*.md`) are committed. Generated images are not.
- Wikipedia text keeps its source: every sample file lists article titles in `data/samples/SOURCES.md` (CC BY-SA).
- Pilot pass criteria are copied from `Project Overview.pdf` §10 and must appear verbatim in each report:
  - P1: "A fluent reader sees no broken letters"
  - P2: "100% correct" on the tricky-word lists
  - P3: "Aksharas survive at least as well as characters"
  - P8: "Clearly negative correlation" between Tesseract confidence and akshara error rate

## Review Focus

1. **Malformed OCR sequences** (a vowel sign at the start of a word, two viramas in a row, a lone ZWJ): `segment()` must not crash, must keep every character, and must give the stray mark its own unit. Test in Task 2.
2. **Mixed content inside Indic text** (Latin words, digits, punctuation, newlines, ZWJ/ZWNJ): `"".join(segment(t)) == t` for every input. Test in Task 2.
3. **Over-correction by repair**: on clean, well-formed text `repair_text()` must return the input unchanged. Test in Task 6.
4. **Empty OCR output** (Tesseract finds nothing on a heavily degraded page): alignment and error rates must return defined values, not divide by zero. Test in Task 5.
5. **Equivalent Tamil vowel spellings** (`ொ` written as one code point vs `ெ` + `ா`): they must not count as OCR errors. Test in Task 5.

---

### Task 0: Project scaffold and sample text

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `src/ocrrag/__init__.py`, `tests/__init__.py`, `tests/test_smoke.py`
- Create: `data/samples/te_sample.txt`, `data/samples/ta_sample.txt`, `data/samples/SOURCES.md`
- Create: `README.md` (short: what the repo is, how to run tests and pilots)

**Interfaces:**
- Produces: importable package `ocrrag`; sample files with **at least 40 sentences each**, one per line, UTF-8, from at least 5 Telugu / 5 Tamil Wikipedia articles.

- [ ] **Step 1: Write `tests/test_smoke.py`**

```python
from pathlib import Path
import ocrrag

def test_package_imports():
    assert ocrrag.__version__ == "0.1.0"

def test_samples_present():
    for lang in ("te", "ta"):
        lines = [l for l in Path(f"data/samples/{lang}_sample.txt").read_text("utf-8").splitlines() if l.strip()]
        assert len(lines) >= 40
```

- [ ] **Step 2: Run it, expect FAIL** — `pytest tests/test_smoke.py -q` → `ModuleNotFoundError: ocrrag`.

- [ ] **Step 3: Create `pyproject.toml`** with setuptools `src` layout, `version = "0.1.0"`, dependencies `pillow`, `numpy`, `playwright`, `augraphy`, optional `[test]` = `pytest`. `.gitignore`: `data/*`, `!data/samples/`, `results/**/*.png`, `__pycache__/`, `.pytest_cache/`, `*.egg-info/`. Install: `pip install -e ".[test]"` and `apt-get install -y tesseract-ocr tesseract-ocr-tel tesseract-ocr-tam`.

- [ ] **Step 4: Add sample text.** Wikipedia is blocked in this container. Get the sentences one of two ways: (a) the author pastes them; (b) after network access to `te.wikipedia.org` and `ta.wikipedia.org` is approved, fetch article text with the MediaWiki API (`action=query&prop=extracts&explaintext=1`). Prefer articles with conjunct-heavy vocabulary (science, geography). Record titles and URLs in `SOURCES.md`.

- [ ] **Step 5: Run `pytest -q`, expect PASS. Verify Tesseract:** `tesseract --list-langs` lists `tel` and `tam`.

- [ ] **Step 6: Commit** — `git add -A && git commit -m "chore: scaffold ocrrag package, sample text, tooling"`

---

### Task 1: Script tables

**Files:**
- Create: `src/ocrrag/script.py`
- Test: `tests/test_script.py`

**Interfaces:**
- Produces:
  - `CharClass = Literal["consonant","vowel","matra","virama","modifier","nukta","joiner","other"]`
  - `char_class(ch: str) -> CharClass`
  - `script_of(ch: str) -> Literal["te","ta"] | None`
  - `VIRAMA = {"te": "్", "ta": "்"}`
  - `MATRAS: dict[str, frozenset[str]]`, `CONSONANTS: dict[str, frozenset[str]]` (used by noise injection)

Ranges (Unicode 15): Telugu consonants U+0C15–U+0C39 and U+0C58–U+0C5A; vowels U+0C05–U+0C14, U+0C60–U+0C61; matras U+0C3E–U+0C4C (except U+0C4D), U+0C55–U+0C56, U+0C62–U+0C63; virama U+0C4D; modifiers U+0C00–U+0C04; nukta U+0C3C. Tamil consonants U+0B95–U+0BB9 (assigned code points only); vowels U+0B85–U+0B94; matras U+0BBE–U+0BCC and U+0BD7; virama (pulli) U+0BCD; modifiers U+0B82; aytham U+0B83 is class `"vowel"` (stands alone). Joiners: U+200C, U+200D. Only assigned code points are in the sets — use `unicodedata.name(ch, None)` to drop unassigned ones.

- [ ] **Step 1: Write tests**

```python
from ocrrag.script import char_class, script_of

def test_classes():
    assert char_class("క") == "consonant" and char_class("ా") == "matra"
    assert char_class("్") == "virama" and char_class("ం") == "modifier"
    assert char_class("த") == "consonant" and char_class("்") == "virama"
    assert char_class("ௗ") == "matra" and char_class("ஃ") == "vowel"
    assert char_class("‍") == "joiner" and char_class("a") == "other"

def test_script_of():
    assert script_of("క") == "te" and script_of("த") == "ta" and script_of("1") is None
```

- [ ] **Step 2: Run, expect FAIL.** `pytest tests/test_script.py -q`
- [ ] **Step 3: Implement `script.py`** from the ranges above.
- [ ] **Step 4: Run, expect PASS.**
- [ ] **Step 5: Commit** — `feat: Unicode character classes for Telugu and Tamil`

---

### Task 2: Akshara segmenter (pilot P2)

**Files:**
- Create: `src/ocrrag/akshara.py`
- Create: `tests/data/tricky_te.tsv`, `tests/data/tricky_ta.tsv` (columns: `word`, `expected` with units joined by `|`)
- Test: `tests/test_akshara.py`

**Interfaces:**
- Consumes: `char_class`, `script_of` (Task 1)
- Produces: `segment(text: str) -> list[str]` — no language argument; rules are chosen per character by `script_of`.

Rules (scanning left to right; each unit starts at the current character):

- **Telugu cluster:** `consonant [nukta] ( virama [joiner] consonant [nukta] )* [matra+] [modifier*]`, or a trailing `virama [joiner]` with no following consonant (word-final virama stays in the unit). Conjuncts are one unit.
- **Tamil cluster:** `consonant [matra+] [modifier*]`, or `consonant virama` as its own unit, **except** these sequences, which are one unit with any following matras/modifiers: `க்ஷ` (U+0B95 U+0BCD U+0BB7) and `ஸ்ரீ` (U+0BB8 U+0BCD U+0BB0 U+0BC0).
- **Independent vowel:** `vowel [modifier*]` (both scripts; aytham is a vowel unit on its own).
- **Anything else** (space, digit, Latin, punctuation, a mark with no valid base such as a leading matra, a lone virama or a lone joiner) is a unit of one character.
- `matra+` allows Tamil two-part vowels written as two code points (`ெ` + `ா`, `ெ` + `ௗ`).

- [ ] **Step 1: Write tests**

```python
import csv, pytest
from pathlib import Path
from ocrrag.akshara import segment

CASES = [
    ("తెలుగు", ["తె", "లు", "గు"]),
    ("క్షేత్రం", ["క్షే", "త్రం"]),
    ("స్త్రీ", ["స్త్రీ"]),
    ("అన్", ["అ", "న్"]),
    ("తమిళ్", ["త", "మి", "ళ్"]),
    ("தமிழ்", ["த", "மி", "ழ்"]),
    ("பக்கம்", ["ப", "க்", "க", "ம்"]),
    ("க்ஷேத்திரம்", ["க்ஷே", "த்", "தி", "ர", "ம்"]),
    ("ஸ்ரீ", ["ஸ்ரீ"]),
    ("அஃது", ["அ", "ஃ", "து"]),
    ("கௌ", ["கௌ"]),
]

@pytest.mark.parametrize("word,expected", CASES)
def test_cases(word, expected):
    assert segment(word) == expected

@pytest.mark.parametrize("lang", ["te", "ta"])
def test_tricky_lists(lang):
    rows = list(csv.DictReader(Path(f"tests/data/tricky_{lang}.tsv").open(encoding="utf-8"), delimiter="\t"))
    assert len(rows) >= 50
    for r in rows:
        assert segment(r["word"]) == r["expected"].split("|"), r["word"]

@pytest.mark.parametrize("text", [
    "ా", "్్క", "‍", "క ా", "Hello తెలుగు 123, தமிழ்!\nnext", "", "  ",
])
def test_round_trip_and_no_crash(text):
    units = segment(text)
    assert "".join(units) == text
    assert all(units)

def test_stray_mark_is_own_unit():
    assert segment("ాక") == ["ా", "క"]
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement `segment`** with the rules above (a small state machine over `char_class`).
- [ ] **Step 4: Seed the TSVs** with the `CASES` words plus at least 50 more per script covering: two- and three-consonant conjuncts, word-final virama/pulli, anusvara, visarga, chandrabindu (te), aytham (ta), two-part Tamil vowels in both spellings, grantha letters (ta: ஜ ஷ ஸ ஹ). Mark the header row `word<TAB>expected`.
- [ ] **Step 5: Run, expect PASS.** `pytest tests/test_akshara.py -q`
- [ ] **Step 6: Author check (P2).** Send both TSVs to the author (and the Tamil reader). Every row they correct is fixed in the TSV first, then in the code, until the test passes on the corrected lists. Write `results/pilots/p2_segmenter.md`: rows checked per script, corrections made, pass criterion "100% correct", final result.
- [ ] **Step 7: Commit** — `feat: rule-based akshara segmenters for Telugu and Tamil (P2)`

---

### Task 3: Units and n-grams

**Files:**
- Create: `src/ocrrag/ngrams.py`
- Test: `tests/test_ngrams.py`

**Interfaces:**
- Consumes: `segment` (Task 2), `char_class` (Task 1)
- Produces:
  - `units(word: str, kind: Literal["akshara","char","decomposed"]) -> list[str]`
    - `akshara`: `segment(word)`
    - `char`: `list(word)`
    - `decomposed`: each akshara split into its base part (consonants, viramas, nukta, joiners) and one unit per trailing matra/modifier
  - `ngrams(seq: list[str], n: int) -> set[tuple[str, ...]]` — if `len(seq) < n`, returns `{tuple(seq)}` (empty set for an empty sequence)
  - `survival(clean: str, noisy: str, kind, n: int) -> float` — `|ngrams(clean) ∩ ngrams(noisy)| / |ngrams(clean)|`; `1.0` when `clean` is empty

- [ ] **Step 1: Write tests**

```python
from ocrrag.ngrams import units, ngrams, survival

def test_units():
    assert units("కా", "akshara") == ["కా"]
    assert units("కా", "char") == ["క", "ా"]
    assert units("క్షే", "decomposed") == ["క్ష", "ే"]

def test_ngrams_short_and_empty():
    assert ngrams(["a"], 3) == {("a",)}
    assert ngrams([], 2) == set()

def test_survival_values():
    clean, noisy = "కాలము", "కిలము"
    assert survival(clean, noisy, "akshara", 2) == 0.5      # (కా,ల) lost, (ల,ము) kept
    assert survival(clean, noisy, "decomposed", 2) == 0.5   # 2 of 4 bigrams kept
    assert survival(clean, clean, "akshara", 2) == 1.0
    assert survival("", "క", "char", 3) == 1.0
```

- [ ] **Step 2: Run, expect FAIL.** **Step 3: Implement.** **Step 4: Run, expect PASS.**
- [ ] **Step 5: Commit** — `feat: akshara, character and decomposed n-grams`

---

### Task 4: Synthetic noise injection

**Files:**
- Create: `src/ocrrag/noise.py`
- Test: `tests/test_noise.py`

**Interfaces:**
- Consumes: `segment` (Task 2), `char_class`, `MATRAS`, `CONSONANTS`, `VIRAMA`, `script_of` (Task 1)
- Produces:
  - `ErrorOp = Literal["matra_swap","matra_drop","virama_drop","consonant_swap","split_mark"]`
  - `inject_akshara_errors(text: str, word_error_rate: float, rng: random.Random, op_weights: dict[ErrorOp, float] | None = None) -> tuple[str, list[dict]]` — chooses exactly `round(word_error_rate * n_eligible)` eligible words (words containing at least one Indic akshara), applies **one** op to each, returns the new text and a log entry per change (`{"word_index", "op", "before", "after"}`). Default weights: equal.
    - `matra_swap`: replace one matra with another matra of the same script
    - `matra_drop`: delete one matra
    - `virama_drop`: delete one virama inside a conjunct (breaks it)
    - `consonant_swap`: replace one consonant with another of the same script
    - `split_mark`: insert a space before one matra (simulates a detached vowel sign; used to test M6)
    - If the chosen op has no target in the word, pick another op that does.
  - `inject_char_noise(text: str, char_error_rate: float, rng: random.Random) -> str` — generic baseline: substitutes `round(rate * n_indic_chars)` Indic code points with random code points of the same script block (any class). Used for E2's generic-noise comparison.

- [ ] **Step 1: Write tests**

```python
import random
from ocrrag.noise import inject_akshara_errors, inject_char_noise

TEXT = "తెలుగు భాష ఒక ద్రావిడ భాష ఇది ఆంధ్రప్రదేశ్ రాష్ట్రంలో మాట్లాడతారు"

NO_SPLIT = {"matra_swap": 1, "matra_drop": 1, "virama_drop": 1, "consonant_swap": 1}

def test_exact_word_count_and_determinism():
    a, log = inject_akshara_errors(TEXT, 0.5, random.Random(1), NO_SPLIT)
    b, _ = inject_akshara_errors(TEXT, 0.5, random.Random(1), NO_SPLIT)
    n_words = len(TEXT.split())
    assert a == b and len(log) == round(0.5 * n_words)
    changed = sum(x != y for x, y in zip(TEXT.split(), a.split()))
    assert changed == len(log)

def test_split_mark_adds_space_before_a_mark():
    a, log = inject_akshara_errors(TEXT, 1.0, random.Random(2), {"split_mark": 1.0})
    n_split = sum(e["op"] == "split_mark" for e in log)   # words with no matra fall back to another op
    assert n_split > 0 and len(a.split()) == len(TEXT.split()) + n_split

def test_zero_rate_is_identity():
    assert inject_akshara_errors(TEXT, 0.0, random.Random(0))[0] == TEXT
    assert inject_char_noise(TEXT, 0.0, random.Random(0)) == TEXT

def test_ops_logged():
    _, log = inject_akshara_errors(TEXT, 1.0, random.Random(3), {"matra_swap": 1.0})
    assert all(e["op"] in {"matra_swap","matra_drop","virama_drop","consonant_swap","split_mark"} for e in log)
```

- [ ] **Step 2: Run, expect FAIL.** **Step 3: Implement.** **Step 4: Run, expect PASS.**
- [ ] **Step 5: Commit** — `feat: akshara-level and generic noise injection`

---

### Task 5: Alignment, error rates, error typing, page split

**Files:**
- Create: `src/ocrrag/text.py`, `src/ocrrag/align.py`
- Test: `tests/test_align.py`

**Interfaces:**
- Consumes: `segment` (Task 2), `char_class` (Task 1)
- Produces:
  - `text.normalize(s: str) -> str` — NFC, collapse runs of whitespace to one space, strip.
  - `EditOp = tuple[Literal["eq","sub","ins","del"], str | None, str | None]` (op, ref unit, hyp unit)
  - `align(ref: list[str], hyp: list[str]) -> list[EditOp]` — Levenshtein with backtrace; ties prefer `sub` over `del`/`ins`.
  - `error_rate(ref: str, hyp: str, unit: Literal["char","akshara","word"]) -> float` — both sides `normalize`d first; `(sub+ins+del) / max(1, len(ref_units))`; `0.0` when both are empty; `1.0` when ref is non-empty and hyp is empty.
  - `classify(op: EditOp) -> Literal["consonant","matra","conjunct","virama","boundary","other"]` — for `sub` of two aksharas: same matras/modifiers but different base → `consonant`; same base, different matra → `matra`; base differs in number of viramas → `conjunct`; differs only by a virama → `virama`; any unit that is a space → `boundary`; else `other`.
  - `ConfusionModel` with `fit(pairs: Iterable[tuple[str, str]]) -> ConfusionModel` (ref, hyp page texts), `counts: dict[str, Counter]`, `type_counts: Counter`, `to_json(path) / from_json(path)`.
  - `split_pages(page_ids: list[str], seed: int, train_frac: float = 0.5) -> tuple[list[str], list[str]]` — deterministic, disjoint, covers all ids. This is the train/test separation for the error model (review issue: model learned and tested on the same pages).

- [ ] **Step 1: Write tests**

```python
from ocrrag.align import align, error_rate, classify, ConfusionModel, split_pages

def test_align_sub():
    assert align(["క", "లు"], ["కి", "లు"]) == [("sub", "క", "కి"), ("eq", "లు", "లు")]

def test_error_rates_edge_cases():
    assert error_rate("", "", "akshara") == 0.0
    assert error_rate("తెలుగు", "", "akshara") == 1.0
    assert error_rate("తెలుగు", "తెలుగు", "char") == 0.0

def test_tamil_two_part_vowel_not_an_error():
    assert error_rate("கொடு", "கொடு", "akshara") == 0.0

def test_classify():
    assert classify(("sub", "కా", "కి")) == "matra"
    assert classify(("sub", "కా", "గా")) == "consonant"
    assert classify(("sub", "క్ష", "కష")) == "conjunct"

def test_confusion_round_trip(tmp_path):
    m = ConfusionModel().fit([("కాలము", "కిలము")])
    m.to_json(tmp_path / "m.json")
    assert ConfusionModel.from_json(tmp_path / "m.json").counts == m.counts

def test_split_pages():
    ids = [f"p{i}" for i in range(10)]
    a, b = split_pages(ids, seed=7)
    assert set(a).isdisjoint(b) and sorted(a + b) == sorted(ids)
    assert split_pages(ids, seed=7) == (a, b)
```

- [ ] **Step 2: Run, expect FAIL.** **Step 3: Implement.** **Step 4: Run, expect PASS.**
- [ ] **Step 5: Commit** — `feat: akshara alignment, error rates, error typing, confusion model`

---

### Task 6: Rule-based repair (M6 stage 1)

**Files:**
- Create: `src/ocrrag/repair.py`
- Test: `tests/test_repair.py`

**Interfaces:**
- Consumes: `char_class`, `script_of`, `VIRAMA` (Task 1), `segment` (Task 2)
- Produces: `repair_text(text: str) -> tuple[str, Counter]` — returns repaired text and a count per rule applied. Rules, applied in this order:
  1. `rejoin_mark`: whitespace directly followed by a matra, virama or modifier → delete the whitespace (a vowel sign never starts a word).
  2. `dedupe_mark`: the same matra, virama or modifier repeated back to back → keep one.
  3. `rejoin_conjunct` (**Telugu only**): Telugu virama + single space + Telugu consonant, where the virama's word is one akshara long → delete the space. Tamil is excluded because word-final pulli followed by a new word is normal Tamil.
  4. `nfc`: Unicode NFC.

- [ ] **Step 1: Write tests**

```python
from pathlib import Path
from ocrrag.repair import repair_text

def test_rules():
    assert repair_text("క ాలము")[0] == "కాలము"
    assert repair_text("కాాలము")[0] == "కాలము"
    assert repair_text("క్ ష")[0] == "క్ష"
    assert repair_text("பக் கம்")[0] == "பக் கம்"

def test_clean_text_unchanged():
    for lang in ("te", "ta"):
        for line in Path(f"data/samples/{lang}_sample.txt").read_text("utf-8").splitlines():
            line = line.strip()
            if line:
                out, stats = repair_text(line)
                assert out == line, (line, stats)
```

- [ ] **Step 2: Run, expect FAIL.** **Step 3: Implement.** **Step 4: Run, expect PASS.** If `test_clean_text_unchanged` fails on a real sentence, the rule is wrong for real text: narrow the rule, do not edit the sample.
- [ ] **Step 5: Commit** — `feat: rule-based akshara repair (M6 stage 1)`

---

### Task 7: Page rendering

**Files:**
- Create: `src/ocrrag/render.py`, `src/ocrrag/templates/page.html`
- Test: `tests/test_render.py`

**Interfaces:**
- Produces:
  - `PageSpec` dataclass: `page_id: str`, `lang: Literal["te","ta"]`, `text: str`, `font: str`, `font_size_pt: int = 12`, `layout: Literal["one_col","two_col"] = "one_col"`
  - `render_pages(specs: list[PageSpec], out_dir: Path, dpi: int = 150) -> list[Path]` — one browser for the whole batch; A4 page; writes `<page_id>.png` and `<page_id>.json` (the spec as JSON, including the exact text) and returns PNG paths.
  - Page HTML: A4 at `dpi`, 20 mm margins, `lang` attribute set, `font-family` from spec, `column-count: 2` for `two_col`, text paragraphs split on blank lines. Text that overflows one page is a `ValueError` naming the page id (the corpus builder in Plan 2 sizes passages to fit).

- [ ] **Step 1: Write tests**

```python
import numpy as np
from PIL import Image
from ocrrag.render import PageSpec, render_pages

def test_render_size_and_sidecar(tmp_path):
    [p] = render_pages([PageSpec("t1", "te", "తెలుగు భాష", "Noto Sans Telugu")], tmp_path)
    assert Image.open(p).size == (1240, 1754)
    assert (tmp_path / "t1.json").exists()

def test_conjunct_is_shaped(tmp_path):
    shaped, forced = render_pages([
        PageSpec("a", "te", "క్ష " * 40, "Noto Sans Telugu"),
        PageSpec("b", "te", "క్‌ష " * 40, "Noto Sans Telugu"),
    ], tmp_path)
    a = np.asarray(Image.open(shaped).convert("L"))
    b = np.asarray(Image.open(forced).convert("L"))
    assert (a < 128).sum() != (b < 128).sum()
```

- [ ] **Step 2: Run, expect FAIL.** **Step 3: Implement** with Playwright sync API, `chromium.launch(executable_path=os.environ.get("OCRRAG_CHROMIUM", "/opt/pw-browsers/chromium"))`, viewport sized to A4 at `dpi`, `page.screenshot(full_page=False)`. **Step 4: Run, expect PASS.**
- [ ] **Step 5: Commit** — `feat: Chromium page rendering with sidecar ground truth`

---

### Task 8: Degradation and Tesseract OCR

**Files:**
- Create: `src/ocrrag/degrade.py`, `src/ocrrag/ocr_tesseract.py`
- Test: `tests/test_degrade.py`, `tests/test_ocr_tesseract.py`

**Interfaces:**
- Consumes: `render_pages`, `PageSpec` (Task 7)
- Produces:
  - `degrade(png: Path, level: int, seed: int) -> PIL.Image.Image` — `level` in `0..3`; `0` returns the image unchanged; `1` light (slight blur + noise), `2` medium (adds low resolution and skew up to 1°), `3` heavy (adds ink bleed and scanner artefacts). Built from Augraphy phases with every random parameter driven by `seed`. Any other level → `ValueError`.
  - `OcrWord` dataclass: `text: str`, `conf: float` (0–100)
  - `OcrResult` dataclass: `text: str`, `words: list[OcrWord]`, `engine: str = "tesseract"`
  - `ocr_tesseract(image: Path | PIL.Image.Image, lang: Literal["te","ta"]) -> OcrResult` — runs `tesseract <img> stdout -l tel|tam --psm 3 tsv`; rebuilds text line by line from the TSV; drops rows with `conf == -1`. Empty page → `OcrResult(text="", words=[])`.

- [ ] **Step 1: Write tests**

```python
import numpy as np
import pytest
from ocrrag.render import PageSpec, render_pages
from ocrrag.degrade import degrade
from ocrrag.ocr_tesseract import ocr_tesseract
from ocrrag.script import script_of

@pytest.fixture(scope="module")
def page(tmp_path_factory):
    d = tmp_path_factory.mktemp("p")
    return render_pages([PageSpec("p", "te", "తెలుగు ఒక ద్రావిడ భాష. " * 20, "Noto Sans Telugu")], d)[0]

def test_degrade_levels(page):
    from PIL import Image
    base = np.asarray(Image.open(page).convert("L"), dtype=float)
    diffs = [np.abs(np.asarray(degrade(page, l, 1).convert("L").resize(Image.open(page).size), dtype=float) - base).mean() for l in range(4)]
    assert diffs[0] == 0 and diffs[1] < diffs[3]
    assert np.array_equal(np.asarray(degrade(page, 2, 5)), np.asarray(degrade(page, 2, 5)))
    with pytest.raises(ValueError):
        degrade(page, 4, 0)

def test_ocr_reads_telugu(page):
    r = ocr_tesseract(page, "te")
    assert any(script_of(c) == "te" for c in r.text)
    assert all(0 <= w.conf <= 100 for w in r.words)

def test_ocr_blank_page(tmp_path):
    from PIL import Image
    p = tmp_path / "blank.png"; Image.new("L", (1240, 1754), 255).save(p)
    assert ocr_tesseract(p, "ta").text == ""
```

- [ ] **Step 2: Run, expect FAIL.** **Step 3: Implement.** **Step 4: Run, expect PASS.**
- [ ] **Step 5: Commit** — `feat: Augraphy degradation levels and Tesseract wrapper`

---

### Task 9: Pilot P3 — n-gram survival (tests H2)

**Files:**
- Create: `pilots/p3_ngram_survival.py`
- Output: `results/pilots/p3_ngram_survival.md`, `results/pilots/p3_ngram_survival.csv`

**Interfaces:**
- Consumes: `inject_akshara_errors` (Task 4), `survival` (Task 3)
- Produces: a report used to decide M1's unit type before Plan 4.

- [ ] **Step 1: Implement the script.** For each language, each sample sentence, word error rate in `{0.05, 0.10, 0.20, 0.30}`, seeds `0..9`, and op mix `{"all ops": equal, "matra only": {"matra_swap":1,"matra_drop":1}, "conjunct only": {"virama_drop":1}}` (`split_mark` excluded: it does not change units after rejoining): compute mean `survival` over words for `(akshara, n=2)`, `(akshara, n=3)`, `(decomposed, n=2)`, `(decomposed, n=3)`, `(char, n=3)`, `(char, n=4)`, `(char, n=5)`. Write the CSV (one row per lang × rate × mix × unit × n) and a Markdown report with one table per language, the pass criterion verbatim, and a PASS/FAIL line per language: PASS if the best akshara setting ≥ the best char setting at rate 0.10 with op mix "all ops".
- [ ] **Step 2: Run** `python pilots/p3_ngram_survival.py` and check the report exists with both languages filled in.
- [ ] **Step 3: Write the decision** at the end of the report: which unit M1 should use, and whether H2 needs rewording. Results on sample text are provisional; Plan 2 re-runs the script on the Wikipedia corpus.
- [ ] **Step 4: Commit** — `pilot: P3 n-gram survival results`

---

### Task 10: Pilot P1 + P8 — render, OCR, error profile, confidence

**Files:**
- Create: `pilots/p1_render_ocr.py`
- Output: `results/pilots/p1_render_ocr.md`, `results/pilots/p1_samples/` (PNGs, git-ignored), `results/pilots/p1_confusions_{te,ta}.json`

**Interfaces:**
- Consumes: `render_pages`, `PageSpec` (Task 7), `degrade`, `ocr_tesseract` (Task 8), `error_rate`, `align`, `classify`, `ConfusionModel` (Task 5)

- [ ] **Step 1: Implement the script.** Build 20 pages per language from the sample sentences (pack sentences until about 250 words per page; alternate the Sans and Serif fonts; half `one_col`, half `two_col`). Render, degrade at levels 0–3 with `seed = page index`, OCR each image. Per language and level report: mean CER, akshara error rate, WER; error-type shares from `classify`. P8: Pearson and Spearman correlation between page mean Tesseract confidence and page akshara error rate across all 80 images per language, with the pass criterion verbatim. Save the fitted `ConfusionModel` per language. Copy 5 level-0 pages per language into `p1_samples/` for the visual check.
- [ ] **Step 2: Run** `python pilots/p1_render_ocr.py`; check the report has 4 levels × 2 languages and both correlations.
- [ ] **Step 3: Author check (P1).** Send the `p1_samples/` pages to the author and the Tamil reader. Record their verdict in the report under the criterion "A fluent reader sees no broken letters".
- [ ] **Step 4: Commit** — `pilot: P1 rendering and Tesseract error profile, P8 confidence calibration`

---

### Task 11: M6 stage 1 evaluation

**Files:**
- Create: `pilots/m6_repair_eval.py`
- Output: `results/pilots/m6_repair.md`

**Interfaces:**
- Consumes: `repair_text` (Task 6), `inject_akshara_errors` (Task 4), `error_rate` (Task 5), Tesseract outputs written by Task 10 (save them as `data/pilots/p1_ocr/<page_id>_L<level>.txt` in Task 10's script so this task can read them)

- [ ] **Step 1: Implement the script** with three measurements per language:
  1. **Synthetic:** inject `split_mark` and `virama_drop` errors at word error rate 0.10 (seeds 0–9); akshara error rate before and after `repair_text`; share of injected errors fixed.
  2. **Real OCR:** akshara error rate of each Tesseract output from Task 10 before and after repair, per degradation level, with rule counts.
  3. **Over-correction:** run `repair_text` on the clean sample text; report the number of changed words (target: 0).
- [ ] **Step 2: Run** `python pilots/m6_repair_eval.py`; check all three sections are filled for both languages.
- [ ] **Step 3: Write the decision**: whether rule repair is worth keeping as a stage before indexing, and which error types it cannot reach (these become the target of M6 stage 2 in Plan 4).
- [ ] **Step 4: Commit** — `pilot: M6 rule-repair evaluation`

---

### Task 12: Pilot summary and proposal update

**Files:**
- Create: `results/pilots/SUMMARY.md`
- Modify: `Research Proposal_ OCR or Pixels_ Telugu & Tamil Document RAG.md` (§7.3, §7.6, §8, §10)

- [ ] **Step 1: Write `SUMMARY.md`**: one row per pilot (P1, P2, P3, P8, M6-1) with criterion, result, PASS/FAIL, and the decision taken.
- [ ] **Step 2: Update the proposal** with only what the pilots decided: M1's unit (from P3), H2 wording if P3 failed, M4's primary reliability signal (from P8), M6 stage 1 added to §7.6 with its measured effect, compute changed to Modal L4 (24 GB) in §8, M5 model set to ColQwen2.5-3B, the train/test page split for the error model in §7.3, and the "M5 limited to 3B" risk in §10.
- [ ] **Step 3: Run the full suite** `pytest -q`; expect all tests to pass.
- [ ] **Step 4: Commit** — `docs: pilot summary and proposal updates from Plan 1`
