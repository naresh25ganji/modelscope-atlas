# ModelScope Atlas

[Open the live app](https://modelscope-atlas.streamlit.app/)

An independent Streamlit research workspace for exploring AI models, their training scale, accessibility, and evidence quality.

## Features

- Historical explorer with shared year, organization, domain, accessibility, and text filters
- Multi-model comparison (up to six), publication links and estimation notes
- Explainable research retrieval across tasks, abstracts, domains, model names and organizations
- Structured data questions and downloadable research briefs
- Annual-maximum trend fitting with explicit limitations
- Adjustable compute-to-energy and emissions scenario calculator
- Session watchlists with persistent JSON export/import
- Data coverage audit, uncertainty visibility and filtered CSV exports
- Live Epoch AI data by default, automatic five-minute refresh, one-click update, and last-good/snapshot fallback

No API keys are required. Research retrieval is deterministic text matching, not an LLM or a capability benchmark. Training scale does not imply quality, inference performance, or deployment suitability.

## Run

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Use Python 3.11 or newer for deployment. Run checks with `python -m unittest test_app.py`.

## Deploy

In Streamlit Community Cloud, choose `naresh25ganji/modelscope-atlas`, branch `main`, entrypoint `app.py`, and Python 3.11. No secrets are needed.

## Data and attribution

Epoch AI, [Data on AI models](https://epoch.ai/data/ai-models). Snapshot retrieved October 11, 2026 from https://epoch.ai/data/all_ai_models.csv. Data is redistributed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The data license is separate from this repository's MIT code license. Numeric cleaning retains only positive measures, dates are parsed to UTC and missing values remain missing. Historical training cost is in 2023 USD.

Inspired by the research workflows in [AI Model Evolution Explorer](https://ai-model-explorer.streamlit.app/). This project is independently implemented and does not copy its source or branding.

Watchlists use stable hashes of model, organization and publication date. Corrections to these identity fields can cause saved entries not to match a future dataset.

## Limitations

The dataset is non-exhaustive, estimates can be uncertain, and this app does not provide benchmark comparisons or current API pricing. Energy scenarios omit hardware manufacturing and inference. Fit results depend on selection, coverage and annual maxima; they are descriptive rather than forecasts. The assistant does not execute user code or transmit questions to an AI provider.

## Dynamic updates

The app fetches Epoch AI's CSV by default, with a shared five-minute cache. Active sessions check freshness every minute and rerender all pages when a new source check completes. New visits fetch if the cache has expired. **Refresh now** bypasses the cache immediately. Automatic updates can be paused; interactions may still fetch after cache expiry.

The sidebar shows the source-check time, dataset-fetch time and total records. On source failure, an existing session retains its last successful live data; a new session uses the bundled snapshot. Failed checks are cached for five minutes to avoid repeated requests during outages. No background polling runs when the app has no active sessions. No repository commit or redeployment is needed for live data changes.

New models appear when Epoch AI publishes them in its dataset, which may lag provider announcements. Existing filters can hide new records. All times in freshness metadata are UTC.
