# OCR or Pixels? Measuring and Mitigating OCR-Induced Failures in Telugu and Tamil Document RAG

**Research proposal (draft v2)**

- **Author:** Yogeshwanth, Integrated MSc Data Science, Amrita Vishwa Vidyapeetham
- **Faculty advisor:** *to be confirmed*
- **Target venue:** ICDAR 2027 (abstract due 31 Jan 2027, full paper due 20 Feb 2027; to be confirmed on the official site)

*The author line will be removed from the double-blind submission version.*

---

## 1. Summary

Retrieval-augmented generation (RAG) over scanned documents normally runs in two stages: an OCR engine converts each page image to text, and a text retriever then searches that text. For English this works reasonably well. For Indian languages written in their native scripts it is fragile, because Indic OCR still misreads a meaningful share of words, especially in Telugu, and every misread vowel sign (matra) or conjunct turns a word into a different token that the retriever can no longer match. A newer alternative, OCR-free visual retrieval in the style of ColPali, embeds the page image directly and avoids OCR entirely. However, these models are trained overwhelmingly on English pages, and early multilingual evidence suggests they perform poorly on Indic scripts.

No published study has measured how Indic OCR errors propagate through a RAG pipeline, compared OCR-based and OCR-free retrieval on Telugu or Tamil documents, or proposed script-aware fixes. This project does all three. It will (1) build the first Telugu and Tamil document-RAG benchmark over page images, (2) learn script-specific OCR error models and use them to measure how retrieval and answer quality degrade as OCR noise increases, and (3) propose and evaluate fixes on both paths: akshara-level indexing and noise-aware embedding fine-tuning for the OCR path, synthetic-data adaptation and text-to-visual distillation for the visual path, and a reliability-weighted fusion that combines the two.

Both languages are covered from the start. They share one pipeline (rendering, OCR, alignment, retrieval and evaluation code), so the only language-specific work is the akshara segmentation rules, font checks, word lists and the hand verification of questions. The minimum publishable version (benchmark for both languages, noise model, measurement, akshara-level indexing and the simple baselines) runs on free cloud GPUs and fits within the ICDAR 2027 timeline. The visual-distillation component is a stretch goal.

---

## 2. Motivation

India produces enormous volumes of documents in its own languages: government circulars and orders, court records, textbooks, newspapers, land records, and archival material. Much of it exists only as scans or image-based PDFs. Making this material searchable and answerable through LLM-based assistants is a practical public-interest problem, and RAG is the standard architecture for it.

The weak point is the first step. OCR quality for Indic scripts has improved sharply with vision-language models, but it remains uneven across languages. Recent self-reported benchmarks on printed documents put the best systems at roughly 94% word accuracy for Tamil but only around 84–85% for Telugu, while widely used open-source engines fall to the low 60s for Telugu.[^ocrcard] In other words, even the strongest OCR misreads roughly one Telugu word in seven. These figures will be re-measured on this project's own data. Prior work on English and Chinese has already shown that OCR errors substantially reduce RAG performance, with semantic errors (wrong characters) hurting retrieval most. There is every reason to expect the damage to be larger for Telugu and Tamil, but nobody has measured it.

The alternative, OCR-free visual retrieval, is attractive precisely because it sidesteps OCR. But the only multilingual visual-retrieval benchmark that includes an Indian language (Hindi, in MIRACL-VISION) shows visual retrievers scoring far below text retrievers on Hindi pages. So today a practitioner building Indic document RAG faces two flawed options and no evidence on when to use which. This project supplies that evidence and proposes ways to close the gap.

[^ocrcard]: Self-reported figures from the IndicOCR model card (Hugging Face: bodhan-ai/indic-ocr). Not peer-reviewed.

---

## 3. Background and Related Work

**OCR noise and RAG.** OHRBench (Zhang et al., ICCV 2025) is the closest prior work. It built a QA benchmark over English and Chinese PDFs from several domains and separated OCR noise into *semantic noise* (character and word prediction errors) and *formatting noise* (inconsistent representation of tables, formulas and layout). It found that even the best OCR pipelines leave a clear gap relative to ground-truth text, and that severe semantic noise can roughly halve RAG performance. OHRBench injects noise using generic error patterns and covers no Indic scripts. This project adopts its methodology and extends it with script-specific, empirically learned error models for Telugu and Tamil.

**OCR-free visual document retrieval.** ColPali (Faysse et al., ICLR 2025) embeds page images with a vision-language model and scores query–page relevance through late interaction (MaxSim over patch embeddings), avoiding layout detection and OCR. It introduced the ViDoRe benchmark, later extended in ViDoRe V2. Successors such as ColQwen2.5, ColQwen3 and the lightweight ColSmol and ColModernVBERT variants improve accuracy or efficiency. VisRAG applies the same idea to full RAG pipelines. All of these are evaluated mainly on English or high-resource European languages.

**Multilingual and low-resource visual retrieval.** MIRACL-VISION (2025) is a multilingual visual retrieval benchmark that includes Hindi; its results show visual retrievers performing far worse than text retrievers on Hindi pages. LëtzCross (2026) studies visual page retrieval for Luxembourgish and finds that fine-tuning helps most when the target low-resource language is included in training. Together these suggest that visual retrievers need targeted adaptation before they are useful for Indic scripts.

**Indic text retrieval.** IndicRAGSuite (AI4Bharat, 2025) provides IndicMSMarco, a retrieval benchmark across 13 Indian languages, and large training sets. Multilingual dense retrievers such as BGE-M3 and multilingual-e5-large reach MRR around 0.49–0.50 on Telugu and Tamil. IndicRAGSuite works with clean digital text only; it does not involve scanned pages or OCR.

**Indic OCR.** Recent systems include Chitrapathak (2026), which reports state-of-the-art Telugu OCR, the Sarvam Vision document model, and open models released on Hugging Face. ORB-Indic (2025) evaluates OCR robustness to page rotation across 11 Indic languages. These works evaluate OCR accuracy in isolation, not its downstream effect on retrieval or question answering.

**The gap.** To our knowledge, there is no published work that (a) benchmarks document RAG over Telugu or Tamil page images, (b) quantifies how Indic OCR errors propagate into retrieval and generation, or (c) compares and fuses OCR-based and OCR-free retrieval for Indic scripts.[^doclens] A fuller literature search on Semantic Scholar, the ACL Anthology and FIRE proceedings will be completed in the first week of the project to confirm this.

[^doclens]: An open-source project, DocLens-VLM (GitHub: Ananayshiv/DocLens-VLM), compares OCR+BM25 against visual retrieval on Hindi and English pages but lists the Indic-script question as unverified, pending a properly labelled benchmark.

---

## 4. Research Questions

**RQ1 (Measurement).** How much do real Indic OCR errors degrade retrieval and answer quality in a document RAG pipeline, and how does the degradation differ between Telugu and Tamil?

**RQ2 (Error structure).** What do Telugu and Tamil OCR errors look like at the level of aksharas, matras, viramas and conjuncts, and does a script-specific error model predict RAG degradation better than generic character noise?

**RQ3 (OCR-free retrieval).** How do zero-shot visual retrievers (ColPali family) compare with OCR-based text retrieval on Telugu and Tamil pages, and at what OCR error rate does visual retrieval become the better choice?

**RQ4 (Mitigation).** Can script-aware methods (akshara-level indexing, noise-aware embedding fine-tuning, visual adaptation, and reliability-weighted fusion) close the gap between OCR-based RAG and RAG over ground-truth text, and do they beat simple alternatives such as character n-gram indexing and LLM-based OCR correction?

---

## 5. Hypotheses

**H1.** OCR-induced degradation in retrieval will be larger for Telugu than for Tamil, tracking the difference in OCR word accuracy between the two scripts.

**H2.** Most OCR errors in both scripts will affect a single akshara or diacritic within a word, so indexing on akshara n-grams will recover a large share of the retrieval lost to OCR noise, and more of it than plain character n-grams.

**H3.** Zero-shot visual retrievers will underperform OCR-based retrieval on clean pages but will degrade more gracefully on poor scans, producing a crossover point as page quality worsens.

**H4.** Fusing text and visual retrieval scores, weighted by a per-page estimate of OCR reliability (engine confidence where it is shown to be calibrated, otherwise a confidence-free signal), will outperform either path alone across the full range of page quality.

---

## 6. Expected Contributions

The project is designed so that each contribution stands on its own. The first three form a complete benchmark-and-analysis paper; the fourth strengthens it with methods.

1. **Benchmark.** The first document-RAG benchmark for Telugu and Tamil over page images, with page-level relevance labels (including additional relevant pages found by pooling) and verified question–answer pairs in extractive and paraphrased form.
2. **Measurement.** The first quantification of how Indic OCR errors propagate through retrieval and generation, including noise-versus-performance curves for each script and a direct Telugu–Tamil comparison.
3. **Error analysis.** Empirically learned, script-specific OCR confusion models at the akshara and diacritic level, released for reuse together with the per-script akshara segmenters.
4. **Methods.** Akshara n-gram indexing, noise-aware embedding fine-tuning, reliability-weighted fusion, and (stretch) text-to-visual distillation for adapting visual retrievers to Indic scripts, each compared against simple baselines.

---

## 7. Methodology

### 7.1 Data

**Synthetic page corpus (primary).** Text passages are sampled from Telugu and Tamil Wikipedia and rendered into page images. Rendering varies open-licensed fonts (for example Noto Sans and Noto Serif in each script plus several Google Fonts Telugu and Tamil faces), font sizes, single- and two-column layouts, and page elements such as headers and simple tables. Pages are laid out as HTML and rendered with a HarfBuzz-based text shaper (headless Chromium) so that conjuncts and matras are drawn correctly. A sample of about 20 conjunct-heavy pages per script and font is inspected by eye before the full corpus is generated. Each page is then rendered at several quality levels using document-degradation augmentation (blur, noise, low resolution, skew, ink bleed, and scanner artifacts, for example via the Augraphy library). Because the source text is known exactly, every page has perfect ground truth. Wikipedia text is released under CC BY-SA, so the resulting benchmark can be shared.

**Real scan subset (secondary, test only).** A smaller set of real scanned documents in each language that also exist in digital form, such as state government circulars or textbook pages with digital originals. These provide a realistic held-out test of whether findings from synthetic pages transfer to real scans. Because this material is unlikely to appear in LLM training data, it also checks for the contamination effects described below. Licensing will be checked for each source before release; anything that cannot be redistributed will be used for evaluation only and described, not released.

**Question–answer pairs.** For each selected page, an LLM drafts candidate questions answerable from that page, covering factoid, numeric, multi-sentence and table questions. Two sets are produced:

- **Extractive questions**, drafted normally.
- **Paraphrased questions**, drafted with an instruction to rephrase and avoid copying phrases from the passage, so that the benchmark does not favour lexical retrievers.

The lexical overlap between each question and its page (shared akshara n-grams) is measured and reported, and results are shown on both sets and split by low and high overlap. Every question is then checked by hand by a fluent reader of the target language for correctness, answerability and fluency, and ambiguous questions are discarded.

**Additional relevant pages.** Wikipedia repeats facts, so a question may be answerable from more than one page. For each question, the top 5–10 pages from BM25 and BGE-M3 over ground-truth text and from a zero-shot visual retriever are pooled. Each candidate is checked (by an LLM, with a hand spot-check of a sample) and marked relevant if it also answers the question. Including a visual retriever in the pool keeps the judgments from favouring text retrieval. Questions answerable from too many pages are discarded as too generic.

**Target size.** About 200 verified questions per language over roughly 1,500 pages per language for the first submission, extended to about 400 per language afterwards.

**English reference set (optional, after submission).** A small English set built with the same pipeline (around 500 pages and 100–150 questions) can serve as a high-resource reference point, showing how much larger the OCR penalty is for Indic scripts than for English.

### 7.2 OCR engines

Each page is processed by several OCR systems spanning the quality range: Tesseract with Telugu and Tamil language packs (weak open-source baseline), Surya OCR (stronger open-source), and one or two commercial vision-language OCR services (for example Gemini and Sarvam Vision) on a subset to limit API cost. Per-word or per-block confidence scores are kept wherever the engine provides them, since they are needed for the fusion method.

### 7.3 Script-specific OCR error model

OCR output is aligned with ground truth at the level of aksharas, using a rule-based akshara segmenter written separately for each script:

- **Telugu:** an akshara is an independent vowel, or (consonant + virama)\* + consonant followed by an optional matra and modifiers (anusvara, visarga, chandrabindu, ardhanusvara). Conjuncts are kept as one unit.
- **Tamil:** a consonant with pulli (mei letter) is its own unit, because Tamil consonant clusters are written visually separate. The joined forms க்ஷ and ஸ்ரீ are treated as single units.

Both segmenters handle ZWJ/ZWNJ and nukta, and both are validated on a hand-checked list of about 50 tricky words per script (conjuncts, words ending in virama or pulli, anusvara and visarga). Exact Python and library versions are recorded. Edit-distance alignment over these units yields substitutions, insertions and deletions, which are aggregated into a confusion model for each script and engine. Errors are further categorised by type: wrong base consonant, dropped or wrong matra, broken or merged conjunct, virama errors, and word-boundary errors. This model answers RQ2 directly and is also used to generate realistic synthetic noise for the controlled experiments in 7.5.

### 7.4 Retrieval pipelines

**OCR path.** OCR text is chunked by page and indexed with:

- (a) word-level BM25
- (b) akshara n-gram BM25
- (c) BGE-M3 dense retrieval
- (d) a hybrid of BM25 and dense scores
- (e) character n-gram BM25 (plain Unicode character 3–5-grams), as a baseline that tests whether akshara units specifically help
- (f) BM25 and BGE-M3 over LLM post-corrected OCR text, where an LLM is asked to correct OCR errors in the Telugu or Tamil text without changing its meaning

**Visual path.** Page images are indexed zero-shot with ColPali, ColQwen2.5 and a lightweight ColSmol variant.

**Upper bound.** All text retrievers are also run on ground-truth text, giving the "perfect OCR" ceiling against which degradation is measured.

### 7.5 Experiments

All experiments are run for both Telugu and Tamil.

**E1: Real-OCR degradation (RQ1).** Run every OCR engine and retriever combination on the benchmark and compare against the ground-truth ceiling. This produces the headline measurement of how much real Indic OCR costs a RAG system, and the direct Telugu–Tamil comparison for H1.

**E2: Controlled noise curves (RQ1, RQ2).** Starting from ground-truth text, inject noise sampled from the learned confusion model at controlled word-accuracy levels (for example 95%, 90%, 85%, 80%, 70%) and plot retrieval and answer quality against noise level. Repeat with generic character noise of the same rate to test whether the script-specific model predicts degradation better. This is the core scientific result of the paper.

**E3: OCR path versus visual path (RQ3).** Compare zero-shot visual retrievers with OCR-based retrieval across page-quality levels to locate the crossover point, if one exists.

**E4: End-to-end answer quality.** Feed the top retrieved pages to a generator and measure answer accuracy. Two generators will be used: an open vision-language model and a commercial API model. A variant passes the page image together with the OCR text, to test whether the generator can correct OCR errors at answer time. Because Telugu and Tamil Wikipedia are likely in the generators' training data, a **closed-book baseline** (no retrieved pages) is also run, and results on the real-scan subset are reported separately, so that answers from memorised knowledge are not credited to retrieval.

### 7.6 Mitigation methods (RQ4)

**M1: Akshara n-gram indexing.** Index overlapping n-grams of aksharas in addition to whole words, so that a word with one misread akshara still shares most of its n-grams with the correct form. This is cheap, interpretable and specific to abugida scripts.

**M2: Noise-aware embedding fine-tuning.** Fine-tune BGE-M3 with a contrastive objective on pairs of clean queries and passages corrupted by the learned noise model, so the embedding space treats near-identical akshara sequences as matches. To avoid the known failure mode where code-mixed or noisy training erodes relevance matching, the standard query–passage relevance loss is kept and the noise-alignment loss is added alongside it.

M1 and M2 are compared against both simple baselines from 7.4: character n-gram BM25 (e) and LLM post-corrected OCR text (f).

**M3: Multi-OCR indexing.** Index outputs from two or three OCR engines for each page and merge their scores. Different engines make different mistakes, so the correct text is more likely to be present in at least one.

**M4: Reliability-weighted fusion.** For each page, combine text and visual retrieval scores with a weight that depends on an estimate of how reliable that page's OCR is: pages that OCR reads well lean on the text score, and poorly read pages lean on the visual score. Two reliability signals are used:

- **Engine confidence.** Its calibration is checked first: for each engine, page-level mean confidence is plotted against the actual akshara error rate and the correlation is reported, because engines (especially Tesseract) can be confidently wrong on Indic scripts and some give no scores.
- **A confidence-free signal.** The perplexity of the OCR text under a character/akshara n-gram language model trained on the script's Wikipedia, with the out-of-vocabulary rate against a Wikipedia word list as a simpler variant. Perplexity is preferred because Telugu and Tamil are agglutinative, so clean text already contains many words missing from any word list.

M4 is run with confidence alone, with the confidence-free signal alone, and with both. A simple logistic weighting with two parameters is fitted on a development split first; a small learned router is tried afterwards if time allows.

**M5 (stretch): Text-to-visual distillation.** Adapt a visual retriever (ColQwen with LoRA) to Indic scripts without any human-labelled queries. On synthetic pages the exact text is known, so a strong text retriever (BGE-M3 over ground-truth text) can score relevance between each query and every page in a batch. The visual retriever is trained to reproduce that score distribution from page images alone, using a KL-divergence objective over in-batch candidates. The text model acts as teacher and transfers its Indic-language knowledge into the visual student. Synthetic queries for training are generated automatically from page text.

### 7.7 Evaluation metrics

| Stage | Metrics |
| --- | --- |
| OCR | Character error rate (CER), word error rate (WER), akshara error rate |
| Retrieval | Hit@1 and Hit@5 (at least one relevant page retrieved), Recall@5 over all relevant pages, nDCG@5, MRR |
| Generation | Exact match, token F1, LLM-judged correctness with human spot-checks on a sample; closed-book baseline for reference |
| Robustness | Area under the noise-versus-performance curve; relative drop from the ground-truth ceiling |

Retrieval results are reported separately for extractive and paraphrased questions and by question–page lexical overlap. Statistical significance between systems will be tested with paired bootstrap resampling over questions.

### 7.8 Ablations

The study will ablate n-gram length in M1 (and in the character n-gram baseline), the balance between relevance and noise-alignment losses in M2, the number of OCR engines in M3, the reliability signal and weighting function in M4, and (if M5 is completed) the number of synthetic training pages and whether including degraded renderings in training helps.

---

## 8. Compute and Resources

The minimum version (benchmark, OCR runs, error model, E1–E3, M1, M3 and the baselines) needs only inference and lightweight indexing, which runs on free Colab or Kaggle GPUs (T4 class). Covering two languages roughly doubles OCR and indexing time but not development time, since the code is shared. ColPali-3B inference fits within this budget; ColQwen2.5-7B is borderline on a 16 GB GPU and may need quantisation or a subset. M2 (BGE-M3 fine-tuning) is feasible on the same hardware with small batches and gradient accumulation. M5 (LoRA fine-tuning of a visual retriever) is the only component that realistically needs a 24 GB or larger GPU for several days; access will be requested through the faculty advisor or university facilities.

Commercial OCR APIs and the LLM post-correction baseline will be run only on a sampled subset of pages to keep costs low. All other software (Chromium, Tesseract, Surya, BGE-M3, ColPali-family models, OHRBench evaluation code) is open-source.

---

## 9. Timeline (targeting ICDAR 2027)

| Period | Work | Output |
| --- | --- | --- |
| 16 Nov – 6 Dec 2026 | Final literature check; render Telugu and Tamil pages and inspect conjunct samples; write and validate both akshara segmenters; start OCR runs; start drafting and checking questions | Page corpora, segmenters, first OCR outputs |
| 7 Dec – 20 Dec 2026 | Finish OCR runs; build alignment and both confusion models; continue question checking in both languages; build BM25 and BGE-M3 indexes | Telugu and Tamil confusion models, text indexes |
| 21 Dec 2026 – 10 Jan 2027 | Pool and verify additional relevant pages; run E1 and E2 for both languages; M1 and baselines (e), (f) | Benchmark v1, core result figures |
| 11 Jan – 31 Jan 2027 | Visual indexes and E3; M3; confidence calibration and M4; E4; submit abstract | ICDAR abstract (31 Jan) |
| 1 Feb – 20 Feb 2027 | Write paper, finalise figures and tables, internal review with advisor | ICDAR full paper (20 Feb) |
| After submission | Extend to ~400 questions per language; M2 and M5; optional English reference set; release benchmark and code; arXiv preprint per venue policy | Extended version, public release |

Question checking runs in parallel with the OCR jobs rather than after them. Text indexes are built first and visual retrievers added afterwards, so the headline OCR-path results are available early.

---

## 10. Risks and Mitigations

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Hand-verifying QA pairs takes longer than planned | Medium | Start checking in late November alongside OCR runs; target 200 per language for submission and extend afterwards; rely on synthetic pages for most experiments |
| No fluent Tamil reader available to verify questions | Medium | Arrange a Tamil-speaking collaborator in week one; if none is available, reduce the Tamil set and report it as preliminary |
| Rendered pages have broken conjuncts or matras | Low | Render with Chromium (HarfBuzz shaping) and inspect a sample per script and font before generating the corpus |
| Generators answer from memorised Wikipedia knowledge | Medium | Report a closed-book baseline and real-scan results separately |
| Relevance labels miss correct pages | Medium | Pool candidates from text and visual retrievers and verify them; report Hit@k |
| OCR confidence is poorly calibrated | Medium | Check calibration per engine; use the confidence-free reliability signal in M4 |
| Real scans with digital originals are hard to find or cannot be redistributed | Medium | The paper's core results rest on synthetic pages; real scans are used for evaluation only where licensing is unclear |
| Commercial OCR costs exceed budget | Low | Run commercial engines and LLM correction on a sampled subset; open-source engines cover the full corpus |
| Zero-shot visual retrievers perform near random on Telugu or Tamil | Medium | This is itself a reportable finding that motivates M5; the paper does not depend on visual retrieval succeeding |
| M5 distillation fails to improve over the text path | Medium | M5 is a stretch goal; a negative result with analysis is still informative and can be reported in an extended version |
| Insufficient GPU for M5 | Medium | Request access through the advisor; otherwise defer M5 to the post-submission extension |
| A closely related paper appears before submission | Low–Medium | Complete the literature check in week one and position contributions around the script-specific error model and fusion method, which are least likely to be duplicated |

---

## 11. Ethics, Licensing and Release

Synthetic pages built from Wikipedia text will be released under CC BY-SA in line with the source licence. Real documents will be checked individually; government documents are not automatically free to redistribute, so only material with clear permissions will be released. No personal data will be included; any real document containing personal information (names in circulars, for example) will be excluded or redacted. Generated questions will be reviewed by a human before inclusion. Code, error models, akshara segmenters and evaluation scripts will be released openly after the review period, respecting the venue's double-blind and preprint policies.

---

## 12. Fallback Venues

If ICDAR 2027 is missed or the paper is not accepted, suitable alternatives include ICDAR 2027 workshops (whose deadlines typically fall a few months after the main conference deadline), FIRE (the Forum for Information Retrieval Evaluation, the main Indian IR venue), and ACL/EMNLP workshops on multilingual or low-resource NLP. A preprint on arXiv, posted in line with the chosen venue's policy, will also make the work citable for applications in the meantime.

---

## 13. References

1. Zhang, J., Zhang, Q., Wang, B., et al. *OCR Hinders RAG: Evaluating the Cascading Impact of OCR on Retrieval-Augmented Generation.* ICCV 2025. arXiv:2412.02592.
2. Faysse, M., Sibille, H., Wu, T., et al. *ColPali: Efficient Document Retrieval with Vision Language Models.* ICLR 2025. arXiv:2407.01449.
3. *ViDoRe Benchmark V2: Raising the Bar for Visual Retrieval.* 2025. arXiv:2505.17166. *(authors to be added)*
4. *MIRACL-VISION: A Large, Multilingual, Visual Document Retrieval Benchmark.* 2025. arXiv:2505.11651. *(authors to be added)*
5. *LëtzCross: A Cross-Lingual Page-Level Benchmark for Multimodal Retrieval over Luxembourgish Documents.* 2026. arXiv:2608.21714. *(authors and arXiv ID to be verified)*
6. Prasanjith, P., More, P. B., Kunchukuttan, A., Dabre, R. *IndicRAGSuite: Large-Scale Datasets and a Benchmark for Indian Language RAG Systems.* 2025. arXiv:2506.01615.
7. *Designing Production-Scale OCR for India: Multilingual and Domain-Specific Systems* (Chitrapathak). 2026. arXiv:2602.16430. *(authors and arXiv ID to be verified)*
8. *OCR-Rotation-Bench (ORB): Evaluating OCR Robustness to Rotation, including ORB-Indic.* 2025. arXiv:2511.04161. *(authors and arXiv ID to be verified)*
9. Chen, J., et al. *BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation.* 2024. arXiv:2402.03216.
10. Yu, S., et al. *VisRAG: Vision-based Retrieval-Augmented Generation on Multi-modality Documents.* 2024. arXiv:2410.10594. *(arXiv ID to be verified)*

*Note: figures cited from model cards and product pages are self-reported by their authors and will be re-verified on this project's own data.*
