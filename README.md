# README — Push Personalization Pipeline (CASE 1) — English

Complete guide for the reviewer: how to prepare, run, validate, and package results. Target platforms: Windows (PowerShell) and Linux/macOS (bash). Follow steps exactly.

## Table of contents

- Requirements
- Repository structure and important files
- Setup (virtual environment, dependencies)
- API setup (optional — AI paraphrasing)
- Data preparation (required files and filenames)
- Running the pipeline (without AI / with AI)
- Outputs (result files and debug)
- Evaluation & reports (what the jury should check)
- Creating submission (archive for delivery)
- GitHub security tips
- Common errors & fixes
- Quick checklist for the jury

---

## 1. Requirements

- Python 3.10+
- ~200 MB free disk (depends on data)
- Internet **only** if you run with `--use-ai true` (makes calls to OpenRouter)
- Python packages listed in `requirements.txt`

---

## 2. Repository structure (important)

```
project-root/
├── .gitignore
├── .env.example
├── requirements.txt
├── README.md
├── submission_debug.py
├── examples/
│   └── results.csv            # example output
├── data/                      # place input CSVs here
└── src/
    ├── app.py                 # CLI entrypoint
    ├── pipeline/
    │   ├── preprocess.py
    │   ├── features.py
    │   ├── scorer.py
    │   └── generator.py
    ├── utils/
    │   └── io.py
    └── eval/
        └── evaluate.py
```

Required repository files: `src/` (code), `requirements.txt`, `.env.example`, `.gitignore`, `README.md`. `examples/` is recommended. **Do NOT commit `.env`** — it is included in `.gitignore`.

---

## 3. Setup (virtual environment & dependencies)

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Linux / macOS (bash):**

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Verify Python version:

```bash
python --version
# must be 3.10 or higher
```

---

## 4. API configuration (optional — only for AI paraphrasing)

1. Copy `.env.example` → `.env`:

**Windows:**

```powershell
copy .env.example .env
```

**Linux / macOS:**

```bash
cp .env.example .env
```

2. Open `.env` and set your key(s):

```
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=deepseek/deepseek-r1:free
```

Notes:
- You can keep `OPENROUTER_URL` and `OPENROUTER_MODEL` as in `.env.example`. The critical field to fill is `OPENROUTER_API_KEY`.
- If `.env` is empty or missing, the pipeline runs without AI using built-in templates.

---

## 5. Data preparation (required file names and formats)

Place input files in the `data/` folder. Filenames and formats are strict.

**profiles.csv** — required
```
Columns: client_code,name,status,age,city,avg_monthly_balance_KZT
client_code: integer 1..60
```

For each client `i` (1..60), provide two files:

```
client_{i}_transactions_3m.csv
client_{i}_transfers_3m.csv
```

Maximum: 120 client files + `profiles.csv`.

If any client files are missing, the pipeline will skip that client and record missing items in `debug/missing_files.json`.

Column formats (required):

**client_{i}_transactions_3m.csv**
```
date,category,amount,currency,client_code
```

**client_{i}_transfers_3m.csv**
```
date,type,direction,amount,currency,client_code
```

---

## 6. Running the pipeline

Recommended invocation (module mode ensures imports work correctly).

**Without AI:**

```bash
python -m src.app --data-dir data --use-ai false --output examples/results.csv
```

**With AI (requires valid `.env` with API key):**

```bash
python -m src.app --data-dir data --use-ai true --output examples/results.csv
```

Arguments:
- `--data-dir` — path to input CSV folder (default: `data/`)
- `--use-ai` — `true` or `false`
- `--output` — path for final CSV (recommended: `examples/results.csv`)

If you run `src/app.py` directly (not via `-m`), ensure package layout and imports are correct; safer to run with `python -m src.app`.

---

## 7. Outputs — what is created and where to check

After a successful run you will have:

- `examples/results.csv` — final CSV with columns:

```
client_code,product,push_notification
```

- `debug/` — directory with detailed files:

```
client_{i}_scores.json   # per-client detailed signals and scores
missing_files.json        # list of missing files (if any)
evaluation_summary.json  # overall automatic evaluation summary
evaluation_per_client.csv # per-client quality scores
```

Running `python submission_debug.py` will create `submission_debug.zip` that contains `examples/results.csv` and `debug/` — ready to send to reviewers.

---

## 8. Evaluation & reports (what reviewers should check)

Automatic evaluation results are in `debug/`.

Key files to inspect:
- `debug/evaluation_summary.json` — average quality score and processed client count
- `debug/evaluation_per_client.csv` — per-client scores by 4 criteria (personalization, tone/length, CTA, formatting)
- `debug/client_{i}_scores.json` — raw_signals, normalized_signals, product_scores, top4, chosen — shows why a product was selected

Manual checks:
- Verify each `product` in `examples/results.csv` is one of:
  - Travel Card
  - Premium Card
  - Credit Card
  - Currency Exchange
  - Cash Loan
  - Multi-currency Deposit
  - Savings Deposit
  - Accumulative Deposit
  - Investments
  - Gold Bars

- Open `debug/client_{i}_scores.json` and compare raw signals and computed benefits to ensure deterministic logic.

---

## 9. Create submission (archive for delivery)

From repo root run:

```bash
python submission_debug.py
```

This produces `submission_debug.zip` containing `examples/results.csv` and `debug/` — send this zip to the jury.

---

## 10. GitHub & security (what to push)

**Never** commit `.env`. Use `.env.example` in the repo so reviewers know required variables.

Files to push to GitHub:
- `src/` (code)
- `.env.example`
- `.gitignore`
- `requirements.txt`
- `README.md`
- `examples/` (optional)
- an empty `data/` folder or instructions for reviewers (they provide real data themselves)

Quick git steps:

```bash
git init
git add .
git commit -m "Release: Push Personalization Pipeline"
git branch -M main
git remote add origin https://github.com/youruser/yourrepo.git
git push -u origin main
```

---

## 11. Common errors & fixes

**ModuleNotFoundError: No module named 'src'**

- Run via module mode:

```bash
python -m src.app --data-dir data --use-ai false --output examples/results.csv
```

- Or add `src/__init__.py` and/or fix `PYTHONPATH`.

**pandas date parsing warnings (dayfirst=True)**

- `src/pipeline/preprocess.py` tries multiple date formats and avoids warnings; ensure input dates follow one of accepted formats.

**.env accidentally committed**

```bash
git rm --cached .env
echo ".env" >> .gitignore
git commit -m "Remove .env from repo"
git push
```

**AI call fails (timeout / 401)**

- Check `OPENROUTER_API_KEY` correctness
- Check `OPENROUTER_URL` correctness
- Internet connectivity
- API limits

**Invalid push texts (length / TOV issues)**

- Inspect `debug/client_{i}_scores.json` — it contains template, benefit and final text. If AI fails, the pipeline uses a fallback template.

---

## 12. Quick checklist for the jury

- Clone repository.
- Create `.venv` and install deps: `pip install -r requirements.txt`.
- Copy `.env.example` → `.env` and fill the API key (only if testing AI).
- Place `profiles.csv` and `client_{i}_*.csv` in `data/`.
- Run:

```bash
python -m src.app --data-dir data --use-ai false --output examples/results.csv
```

- Open `examples/results.csv` — confirm columns `client_code,product,push_notification`.
- Open `debug/client_{i}_scores.json` for several clients and check selection logic.
- Run `python submission_debug.py` and provide `submission_debug.zip` (or attach `examples/results.csv` with debug folder).

---

## Example output format (sample)

```
examples/results.csv:

client_code,product,push_notification
1,Travel Card,"Aliya, in August 2025 you had 3 trips/taxis totaling 45 000 ₸. With Travel Card you would have earned ≈1 800 ₸. Open"
2,Premium Card,"Asker, your average balance is 2 400 000 ₸ and restaurant spend is 75 000 ₸. Premium Card gives up to 4% on restaurants and free cash withdrawals. Apply"
```

`debug/client_1_scores.json` contains: `raw_signals`, `normalized_signals`, `product_scores` (benefit, score), `top4`, `chosen`.

---

If you paste this README into `README.md`, the repository will contain instructions and the exact commands needed for a reviewer to set up and run the pipeline immediately. If you want, I can also produce a short `CHECKLIST.md` with only terminal commands and minimal text for fast execution.

