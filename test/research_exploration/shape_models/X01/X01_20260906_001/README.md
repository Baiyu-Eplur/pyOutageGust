# X01_20260906_001

Independent X01 candidate-curve experiment. All analysis inputs actually used are copied below `frozen_sources/`; the large frozen event database is omitted from the return ZIP but retained locally with its hash.

## Results

- Chinese report: `X01_REPORT.md`
- Research story log: `RESEARCH_STORY_LOG.md`
- ChatGPT return: `RETURN_TO_CHATGPT_X01.md`
- Rankings: `tables/model_leaderboard.csv`
- OOF predictions: `predictions/oof_predictions.parquet`
- Curves: `evidence/curve_data.parquet`

## Re-run

Run `python -B src/x01_run.py` from this directory in a scientific Python environment containing NumPy, pandas, SciPy, pyarrow and Matplotlib. The source only reads `frozen_sources/input/R02_event_master.parquet` and writes inside this run.

Input SHA-256: `8ac332cdb59d5eb961a01146757665a2600ebaada4265c8ac1ac30218c6f066d`.
