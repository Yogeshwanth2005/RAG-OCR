# Graph Report - RAG-OCR  (2026-11-24)

## Corpus Check
- 55 files · ~92,549 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: .csv 3, .tsv 2, (none) 1)

## Summary
- 424 nodes · 823 edges · 28 communities (21 shown, 7 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 48 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Akshara Segmenter
- Page Rendering & Degradation
- Alignment & Error Classification
- P1 Render-OCR Pilot
- P3 N-gram Survival Pilot
- M6 Repair Evaluation
- Project Overview & Methods
- Noise Injection
- Tesseract OCR Wrapper
- Proposal Fixes & Benchmarks
- Roadmap & Mitigation Methods
- Pilots & Baselines
- Sample Corpora & Fixes
- Conventions & Error Model
- Plan 1 & Package Tasks
- Confidence Calibration
- Tamil p01 Render
- Tamil p10 Render
- Tamil p15 Render
- Telugu p01 Render
- Telugu p05 Render
- Tamil p05 Render
- Tamil p20 Render
- Telugu p10 Render
- Telugu p15 Render
- Telugu p20 Render
- ocrrag Package Root

## God Nodes (most connected - your core abstractions)
1. `main()` - 23 edges
2. `char_class()` - 22 edges
3. `inject_akshara_errors()` - 18 edges
4. `classify()` - 17 edges
5. `segment()` - 16 edges
6. `render_pages()` - 16 edges
7. `Research Proposal: OCR or Pixels? Telugu & Tamil Document RAG (draft v2)` - 14 edges
8. `PageSpec` - 13 edges
9. `script_of()` - 13 edges
10. `ocr_tesseract()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `P1 Rendering Pilot (broken conjuncts)` --implements--> `Chromium (HarfBuzz) page rendering`  [INFERRED]
  results/pilots/p1_render_ocr.md → Project Overview.pdf
- `P2 Akshara Segmenter (Telugu and Tamil)` --implements--> `Akshara (written syllable unit)`  [INFERRED]
  results/pilots/p2_segmenter.md → Project Overview.pdf
- `page.html Render Template` --implements--> `Chromium (HarfBuzz) page rendering`  [INFERRED]
  src/ocrrag/templates/page.html → Project Overview.pdf
- `P3 N-gram Survival Pilot` --references--> `H2: akshara n-grams recover retrieval better than character n-grams`  [EXTRACTED]
  results/pilots/p3_ngram_survival.md → Project Overview.pdf
- `build_page()` --uses--> `PageSpec`  [INFERRED]
  pilots/p1_render_ocr.py → src/ocrrag/render.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **RQ4 mitigation methods M1-M6** — research_proposal_ocr_or_pixels_telugu_tamil_document_rag_m1_ngram_indexing, research_proposal_ocr_or_pixels_telugu_tamil_document_rag_m2_noise_aware_finetuning, research_proposal_ocr_or_pixels_telugu_tamil_document_rag_m3_multi_ocr_indexing, research_proposal_ocr_or_pixels_telugu_tamil_document_rag_m4_reliability_weighted_fusion, research_proposal_ocr_or_pixels_telugu_tamil_document_rag_m5_text_to_visual_distillation, research_proposal_ocr_or_pixels_telugu_tamil_document_rag_m6_script_aware_reconstruction [EXTRACTED 0.95]
- **Benchmark construction flow (pages, QA, pooling, real scans)** — research_proposal_ocr_or_pixels_telugu_tamil_document_rag_synthetic_page_corpus, research_proposal_ocr_or_pixels_telugu_tamil_document_rag_qa_pairs_extractive_paraphrased, research_proposal_ocr_or_pixels_telugu_tamil_document_rag_relevance_pooling, research_proposal_ocr_or_pixels_telugu_tamil_document_rag_real_scan_subset [EXTRACTED 0.90]
- **CPU pilot scripts (P1/P8, P3, M6)** — readme_p1_render_ocr_pilot, readme_p3_ngram_survival_pilot, readme_m6_repair_eval_pilot, readme_ocrrag_package [EXTRACTED 0.90]
- **Plan 1 CPU pilots validating the Telugu/Tamil pipeline** — results_pilots_p1_render_ocr_p1_rendering_pilot, results_pilots_p2_segmenter_p2_akshara_segmenter, results_pilots_p3_ngram_survival_p3_pilot, results_pilots_p1_render_ocr_p8_confidence_pilot, results_pilots_m6_repair_m6_stage1_repair [EXTRACTED 1.00]
- **Render, degrade, OCR and score flow** — src_ocrrag_templates_page, results_pilots_p1_render_ocr_degradation_levels, results_pilots_p1_render_ocr_tesseract_ocr, results_pilots_p1_render_ocr_zwnj_scoring, results_pilots_p1_render_ocr_error_type_taxonomy [INFERRED 0.85]

## Communities (28 total, 7 thin omitted)

### Community 0 - "Akshara Segmenter"
Cohesion: 0.06
Nodes (30): _is_joiner(), _match(), segment(), _skip_run(), _tamil_unit(), _telugu_unit(), _unit_end(), _decompose() (+22 more)

### Community 1 - "Page Rendering & Degradation"
Cohesion: 0.09
Nodes (21): _blur_and_noise(), degrade(), _ink_bleed_and_scanner(), _low_res_and_skew(), _body_html(), _check_fonts(), _css_string(), _installed_families() (+13 more)

### Community 2 - "Alignment & Error Classification"
Cohesion: 0.08
Nodes (21): align(), classify(), ConfusionModel, _consonant_count(), error_rate(), _split_base(), split_pages(), _strip_viramas() (+13 more)

### Community 3 - "P1 Render-OCR Pilot"
Cohesion: 0.09
Nodes (19): build_page(), correlate(), fmt(), font_for(), load_sentences(), log(), main(), make_record() (+11 more)

### Community 4 - "P3 N-gram Survival Pilot"
Cohesion: 0.09
Nodes (19): cell(), corrupt(), decision_text(), fmt(), label(), load_sentences(), log(), main() (+11 more)

### Community 5 - "M6 Repair Evaluation"
Cohesion: 0.10
Nodes (20): build_report(), decision_text(), delta(), fmt_counter(), level_mean(), load_lines(), log(), main() (+12 more)

### Community 6 - "Project Overview & Methods"
Cohesion: 0.09
Nodes (28): Project Overview: OCR or Pixels?, Akshara (written syllable unit), Chromium (HarfBuzz) page rendering, ColPali visual document retriever (Faysse et al., ICLR 2025), E2 Controlled noise curves (central claim), H2: akshara n-grams recover retrieval better than character n-grams, M1 Akshara n-gram indexing, M4 Reliability-weighted fusion (+20 more)

### Community 7 - "Noise Injection"
Cohesion: 0.19
Nodes (12): _apply(), _choose_op(), inject_akshara_errors(), inject_char_noise(), _targets(), test_eligible_word_rate_keyword(), test_exact_word_count_and_determinism(), test_ops_logged() (+4 more)

### Community 8 - "Tesseract OCR Wrapper"
Cohesion: 0.17
Nodes (10): ocr_tesseract(), OcrResult, OcrWord, _parse_tsv(), _run_tesseract(), _stderr_tail(), test_missing_image_raises_runtime_error_naming_the_path(), test_ocr_blank_page() (+2 more)

### Community 9 - "Proposal Fixes & Benchmarks"
Cohesion: 0.13
Nodes (14): Proposal Fixes (companion to research proposal), Research Proposal: OCR or Pixels? Telugu & Tamil Document RAG (draft v2), Chitrapathak (production-scale Indic OCR), E3: OCR path vs visual path crossover, E4: End-to-end answer quality with closed-book baseline, IndicRAGSuite (AI4Bharat), LetzCross (Luxembourgish visual retrieval benchmark), LLM contamination risk (Wikipedia in training data) (+6 more)

### Community 10 - "Roadmap & Mitigation Methods"
Cohesion: 0.18
Nodes (10): Five-plan project roadmap, BGE M3-Embedding, ColPali (Faysse et al., ICLR 2025), E1: Real-OCR degradation, M2: Noise-aware BGE-M3 fine-tuning, M3: Multi-OCR indexing, M5: Text-to-visual distillation (stretch), OCR engines (Tesseract, Surya, Gemini, Sarvam Vision) (+2 more)

### Community 11 - "Pilots & Baselines"
Cohesion: 0.25
Nodes (10): README (ocrrag repository), M6 pilot: rule-based repair evaluation, P1/P8 pilot: rendering, Tesseract error profile, confidence calibration, P3 pilot: n-gram survival under synthetic akshara errors, Tesseract OCR (tel, tam data), Character n-gram BM25 baseline, H2: Script-aware units recover more retrieval than char n-grams, LLM post-corrected OCR baseline (+2 more)

### Community 12 - "Sample Corpora & Fixes"
Cohesion: 0.22
Nodes (6): Sample text sources (Wikipedia articles list), Tamil sample sentences (ta_sample.txt), Telugu sample sentences (te_sample.txt), QA pairs (extractive and paraphrased sets), Additional relevant page pooling, Synthetic page corpus (Wikipedia rendered pages with degradation)

### Community 13 - "Conventions & Error Model"
Cohesion: 0.29
Nodes (7): Conventions (ocrrag text handling and performance notes), ConfusionModel JSON format and deletion/insertion convention, Review focus (malformed OCR, mixed content, over-correction, empty OCR, Tamil vowel spellings), E2: Controlled noise curves, OHRBench (OCR Hinders RAG, Zhang et al., ICCV 2025), Script-specific OCR confusion/error model, ZWJ/ZWNJ removal before scoring

### Community 14 - "Plan 1 & Package Tasks"
Cohesion: 0.32
Nodes (7): Plan 1: Foundation and CPU Pilots Implementation Plan, Task 2: akshara.py segment() segmenter (pilot P2), Pilot pass criteria (P1, P2, P3, P8), Task 1: script.py character class tables, ocrrag Python package, Rule-based akshara segmenter (per script), Pilot study (CPU pilots, section 7.9)

### Community 15 - "Confidence Calibration"
Cohesion: 0.60
Nodes (4): OCR confidence calibration check, Confidence-free signal (n-gram LM perplexity, OOV rate), H4: Reliability-weighted fusion beats either path, M4: Reliability-weighted fusion

### Community 16 - "Tamil p01 Render"
Cohesion: 0.67
Nodes (3): Tamil rendered page ta_p01 (L0, clean render), Degradation level L0 (no degradation baseline) in P1 render+OCR pilot, Tamil script (rendered text, geography/history of India passage)

### Community 17 - "Tamil p10 Render"
Cohesion: 1.00
Nodes (3): Tamil page 10 render, level L0 (clean) - P1 pilot sample, P1 render+OCR pilot, degradation level L0 (no degradation baseline), Tamil script text rendering (justified Unicode Tamil prose on A4 page)

### Community 18 - "Tamil p15 Render"
Cohesion: 0.67
Nodes (3): Tamil page 15 rendered at degradation level L0 (P1 pilot sample), Degradation level L0 (clean render, no degradation), Tamil script two-column justified text (Himalayan glaciers, Indian forest cover)

### Community 19 - "Telugu p01 Render"
Cohesion: 0.67
Nodes (3): Telugu page 01 render (L0, clean) for P1 OCR pilot, Degradation level L0 (clean render baseline), Telugu script text rendering

### Community 20 - "Telugu p05 Render"
Cohesion: 1.00
Nodes (3): Telugu page 05 rendered at L0 (clean) for P1 OCR pilot, P1 render+OCR pilot, degradation level L0 (no degradation), Telugu script rendering (dense conjuncts, India facts text)

## Knowledge Gaps
- **38 isolated node(s):** `ocrrag`, `Real scan subset (test only)`, `Retrieval pipelines (word BM25, akshara n-gram BM25, BGE-M3, hybrid, char n-gram, LLM-corrected)`, `E2: Controlled noise curves`, `E3: OCR path vs visual path crossover` (+33 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 127 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `P1 Render-OCR Pilot` to `Tesseract OCR Wrapper`, `Page Rendering & Degradation`, `Alignment & Error Classification`, `P3 N-gram Survival Pilot`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `main()` (e.g. with `ConfusionModel` and `PageSpec`) actually correct?**
  _`main()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `ocrrag`, `Real scan subset (test only)`, `Retrieval pipelines (word BM25, akshara n-gram BM25, BGE-M3, hybrid, char n-gram, LLM-corrected)` to the rest of the system?**
  _38 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Akshara Segmenter` be split into smaller, more focused modules?**
  _Cohesion score 0.06453634085213032 - nodes in this community are weakly interconnected._
- **Why does `char_class()` connect `Alignment & Error Classification` to `Akshara Segmenter`, `M6 Repair Evaluation`, `Noise Injection`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Should `Page Rendering & Degradation` be split into smaller, more focused modules?**
  _Cohesion score 0.08695652173913043 - nodes in this community are weakly interconnected._
- **Why does `inject_akshara_errors()` connect `Noise Injection` to `Akshara Segmenter`, `P3 N-gram Survival Pilot`, `M6 Repair Evaluation`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._