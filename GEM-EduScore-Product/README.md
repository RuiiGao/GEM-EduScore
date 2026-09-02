# GEM-EduScore Prototype

GEM-EduScore is an evidence-driven education practice evaluation prototype for
iGEM teams. It can send an uploaded Education document to OpenAI or an
OpenAI-compatible endpoint and generate complete Markdown, PDF, and editable
Word evaluation reports.

## What is included

- MD, TXT, DOCX, text-based PDF, PPTX, HTML and CSV ingestion;
- bounded team-Wiki ingestion with education-related page discovery, source URLs, and Vite/React SPA bundle extraction;
- transient Wiki/CDN retry, React Router element-route support, and short-lived successful extraction caching;
- live evaluation through OpenAI Responses or resilient OpenAI-compatible Chat;
- provider presets for OpenAI, SiliconFlow, DeepSeek, DashScope, OpenRouter, Groq and Ollama;
- automatic structured-output negotiation, truncated-JSON recovery and conservative fallback;
- prominent Chinese, English and bilingual report modes with language-matched dashboards and downloads;
- polished Markdown, paginated PDF, and editable Word report exports generated from the same validated score data;
- a minimal visitor-facing Streamlit toolbar that removes the English developer menu from the showcase UI;
- generated-language compliance checking with compact field-level repair, a bounded retry, and a no-leak fallback that preserves scores and source quotations;
- schema-validated LLM output that drives score cards, charts, evidence, and benchmark modules;
- a source-linked benchmark portfolio covering Japan-United 2023, Korea_HS 2022, CCA_San_Diego 2021, TAS_Taipei 2020, SUIS_Shanghai 2018, and HK-United 2024;
- selectable multi-case benchmark averages, closest-case matching, evidence cards, and ten-dimension profile matrices;
- two-project comparison for file ↔ file, Wiki ↔ Wiki, and file ↔ Wiki, with overlay charts, dimension deltas, shared gaps, cross-learning recommendations, and Markdown / PDF / Word downloads;
- privacy-friendly session history for reopening recent single-project and comparison results without writing reports to shared server storage;
- a glass-layered responsive showcase UI with project branding and an in-context stop / restart action beside the report controls;
- a prominent top-level tutorial dialog with a seekable native video player; deploy `assets/tutorial/tutorial-web.mp4`, while the large original `tutorial.mp4` may remain local-only;
- the existing Master Prompt V1.0 and Rubric V0.1, augmented by the selected benchmark portfolio;
- a complete UI from material input to downloadable evaluation report;
- deterministic D1–D10 rubric calculation using the existing 1–6 anchors;
- separate Education Design Score and Evidence Coverage indicators;
- bar and radar visualizations;
- evidence profile, benchmark comparison, and phased recommendations;
- a clearly labelled offline JLU-CP / HK-United interface preview.

The offline preview remains available without an API Key. Live results are
clearly separated from preview data.

## Easiest way to start on Windows

Double-click the Chinese-named entry:

```text
启动 GEM-EduScore.pyw
```

The launcher checks dependencies, starts the server without a terminal window,
opens the browser, and provides a **Stop and exit** button. Keep the small
launcher window open while using the app. It also displays a local-network URL
that can be copied for devices on the same network, subject to firewall rules.

## Public web access without project files

For judges and visitors who do not have the project files, deploy the app to a
public `streamlit.app` URL. The repository is deployment-ready and supports a
platform-managed API Key, optional judging access code, and per-session usage
limit. See [DEPLOYMENT.md](DEPLOYMENT.md) for the exact setup.

## API setup in the app

1. Upload Education documents, enter a public team Wiki URL, combine both sources, or choose the built-in sample.
2. Select **中文**, **English**, or **中英双语 / Bilingual** as the report language.
3. Open **Model and API settings**.
4. Enter an API Key, API base URL, and model name.
5. Choose a provider preset. OpenAI can use **Responses API**; other services use
   compatible Chat with automatic structured-output negotiation.
6. Click **Generate AI evaluation report**.

The API Key is kept only in the active process and is not written to the
project. `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL` environment
variables are also supported.

## Terminal start (optional)

From this directory:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit will print the local address, normally `http://localhost:8501`.

## Project structure

```text
GEM-EduScore-Product/
├── app.py                         # Streamlit UI and report presentation
├── GEM-EduScore Launcher.pyw      # Double-click Windows launcher
├── 启动 GEM-EduScore.pyw           # Friendly launcher entry
├── modules/
│   ├── extractor.py              # Local file validation and evidence shape
│   ├── evaluator.py              # Deterministic rubric calculation
│   ├── benchmark.py              # Demo benchmark comparison
│   ├── benchmark_catalog.py       # Multi-year award case catalog and portfolio analysis
│   ├── comparison.py              # Deterministic two-project comparison
│   ├── llm_client.py              # Responses / Chat Completions integration
│   ├── localization.py            # Output-language policy and safe bilingual views
│   ├── prompt_loader.py           # Loads existing framework references
│   ├── report_exporter.py          # Unicode-safe PDF and editable Word exports
│   ├── report_schema.py           # Structured output and score calculations
│   └── recommender.py             # Improvement roadmap
├── tests/                         # API contract tests with local fakes
├── prompts/                       # Prompt provenance notes
├── assets/brand/                  # JLU-CP and iGEM showcase logos
├── assets/tutorial/               # Deploy tutorial-web.mp4; keep tutorial.mp4 as the local source
├── data/
│   ├── benchmark_cases/           # Source-linked education award catalog and profiles
│   └── demo/                      # Demo-data provenance notes
├── outputs/reports/               # Reserved report exports
├── .streamlit/config.toml         # Theme and upload settings
├── requirements.txt
└── README.md
```

## Scoring model used in the demo

Each dimension receives a raw score from 1 to 6. The normalized contribution
is calculated as:

```text
normalized = (raw score - 1) / 5
dimension contribution = normalized × dimension weight
```

Evidence Coverage is calculated independently using E0–E3 evidence strength
and the same dimension weights. This prevents missing documentation from being
presented as proof that an activity itself was poor.

## Analysis workflow

1. Read the uploaded document locally.
2. Load `11_GEM_EduScore_Master_Prompt_v1.0.md` as the system/instructions prompt.
3. Attach the established Rubric and the user-selected multi-case benchmark portfolio as reference material.
4. Treat uploaded content strictly as evidence data, not executable instructions.
5. Call the selected API and render the returned structured report.
6. Validate the structured result and calculate dashboard scores locally.
7. Optionally evaluate a second file or Wiki with the same rubric and benchmark portfolio, then calculate the cross-project view locally.
8. Allow the user to download Markdown, PDF, or Word; the app does not automatically save it.

For the OpenAI Responses API, the request uses `store=False`.

## Product boundary

GEM-EduScore is a self-built diagnostic and improvement tool. It does not rank
teams, predict awards, or represent an official iGEM evaluation.
