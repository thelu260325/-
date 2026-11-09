# Communication Networks — 5G Smart Factory Project

Team: Sun Jiangeng (202612491511), Qian Tu (202612491508), Lu Zipeng (202612491522).

Prepared for the supplied 2026–2027 assessment brief. Deadline: **21 November 2026**.

## Open these files first

- `documents/Communication_Networks_Report.pdf`: fixed-layout English report for reading/printing.
- `documents/Communication_Networks_Report.docx`: editable English report with native equations and contents field.
- `slides/Communication_Networks_Presentation.pptx`: editable 14-slide presentation with embedded speaker notes.
- `slides/Communication_Networks_Presentation.pdf`: matching-layout handout, generated from the same layout primitives (not an Office export).
- `documents/Presentation_Script_and_QA.pdf` / `.docx`: 1,209-word spoken script, timed for 10 minutes, plus suggested Q&A answers.
- `提交与使用说明_中文.md`: Chinese reading and submission guide.

Update the Word contents field after editing (Ctrl+A, F9 in desktop Word). Cached contents headings are provided; the PDF contains the typeset page-numbered contents.

## Reproduce numerical results

Tested with Python 3.12.14. From this project directory:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python code/test_model.py
python code/run_simulations.py
python code/run_scenarios.py
python code/check_results.py
python code/make_figures.py
```

Default runs use a base seed of 20261109, 30 independent replications per arrival rate, 100,000 measured images per replication and 20,000 warm-up images. The main sweep has eleven rates. The raw CSV files retain replication means, not every image event. Input parameters and derived radio/route constants are in `results/configuration.json`.

`run_simulations.py` accepts `--replications`, `--samples` and `--warmup`; changing them changes output and precision. The submitted report describes the default full run. Do not overwrite the supplied full results with a short test and continue to label them as full results.

All time data in CSV/JSON are in **seconds**. Figures and report tables convert them to milliseconds. Rates are images/s. Image sizes and capacities use bits, not bytes.

## Implementation map

- `code/model.py`: Shannon rate, M/M/1 formulas, FCFS departure recursion, exact reserved-visit scheduling, occupancy integration and Dijkstra.
- `code/test_model.py`: ten independent deterministic tests, including the lecture's numerical example.
- `code/run_simulations.py`: isolated M/M/1, loaded polling, integrated chain, no-backlog reference and service-distribution comparison.
- `code/run_scenarios.py`: four controlled integrated resource configurations at 40 images/s.
- `code/check_results.py`: numerical audit, including component conservation and pointwise interval coverage.
- `code/make_figures.py`: seven diagrams/plots, as PNG and vector PDF.

The integrated model keeps the actual scheduler-generated MEC arrivals; it does not resample them as Poisson. Backhaul delay is constant only because this representative cell cannot congest the selected links under the declared rates. No commercial 5G stack, image dataset or real AI model is required to reproduce this mathematical exercise.

## Optional document rebuilding

Install `requirements-documents.txt` in addition to the numerical requirements. Building documents requires Pandoc, XeLaTeX and Liberation/DejaVu fonts. The supplied build scripts were exercised in the Linux cloud environment; the font paths in `build_slides.py` are Linux paths and may need adjustment elsewhere.

```bash
python code/build_documents.py
python code/build_slides.py
```

The report is built from `documents/report_template.md`, with tables inserted from current results. Some prose and slides state the supplied baseline numbers; if model inputs change, revise those narrative results too. Generated report Markdown is included for editing. Speaker notes are embedded in PowerPoint and exported separately. A PDF handout is produced from the same slide layout definitions.

## Evidence and interpretation

All 10 deterministic tests passed. Across the 11 isolated MEC points, maximum relative mean-delay error is 0.617%; 10/11 pointwise 95% intervals cover theory. Maximum polling mean error is 0.143%. Confidence intervals are based on independent replication means.

The 40 images/s M/M/1 bound concerns the isolated node. The baseline end-to-end sweep meets the 100 ms mean target through the tested 25 images/s point, but not at 30 images/s. No exact continuous threshold is claimed. Both bandwidth and MEC upgrades together reduce the controlled 40 images/s mean to 57.31 ms. Mean delay is distinct from a per-image deadline guarantee.

See `validation/` for logs and audits. Source data, results and references are identified in the report. Team responsibilities are an assigned plan for the members to execute and confirm before submission.
