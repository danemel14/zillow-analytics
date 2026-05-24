# Zillow Analytics

A local Streamlit dashboard for reviewing rental property deals exported from a Zillow Chrome extension. The app imports spreadsheet exports, stores deals in SQLite, recalculates investment metrics, and explains why a listing receives a good or bad grade.

## Tech Stack

- Python
- Streamlit
- pandas
- SQLite
- Plotly

## What It Does

- Uploads CSV, XLS, and XLSX exports from the Chrome extension.
- Supports Zillow-style HTML spreadsheet exports saved with an `.xls` extension.
- Saves imported deals into a local SQLite database.
- Shows saved deals in a dashboard with filters and KPI cards.
- Ranks deals by cash flow, cap rate, cash-on-cash ROI, 1% rule, and total investment.
- Filters deals by price, cash flow, ROI, and investment grade.
- Shows Plotly charts, including a monthly cost breakdown and listing comparisons.
- Explains what is weak about a deal and what targets would make it stronger.
- Deletes saved deals from the local database.

## Quick Start

On Windows, double-click:

```text
Run Deal Analytics App.bat
```

The launcher creates a local virtual environment, installs requirements, and starts Streamlit.

Manual setup:

```bash
cd deal-analytics-app
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

On macOS or Linux:

```bash
cd deal-analytics-app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints, usually `http://localhost:8501`.

## Suggested Demo Flow

1. Start the app.
2. Upload an export from the Zillow Chrome extension.
3. Click `Save deals`.
4. Show the Overview tab with saved deals and KPI cards.
5. Select a listing and explain the grade breakdown.
6. Show Rankings to compare deals by different metrics.
7. Show Charts for expense breakdown and listing comparison.
8. Show Manage to delete a saved deal.

For portfolio screenshots or videos, export a listing from the extension and use that file in the demo. Do not upload real private listing data to GitHub.

## Scoring Logic

The app matches the Chrome extension's investment grade logic. It scores three metrics for a total of 75 possible points:

- Cash-on-cash ROI: up to 25 points
- Cap rate: up to 25 points
- 1% rule: up to 25 points

Grades are assigned from the normalized score:

- `A`: 80%+
- `B`: 70%+
- `C`: above 60%
- `D`: 50% to 60%
- `F`: below 50%

The app recalculates the 1% rule and investment grade locally so saved deals stay consistent with the extension logic.

## Import Format

The importer supports the Zillow extension HTML spreadsheet export that uses a `Metric | Value | Notes` table. It parses these sections directly:

- `PROPERTY DETAILS`
- `ZILLOW PAYMENT ESTIMATE`
- `PURCHASE INFORMATION`
- `LOAN INFORMATION`
- `MONTHLY EXPENSES`
- `INCOME & CASH FLOW`
- `INVESTMENT METRICS`
- `NOTES`

It also supports normal CSV/XLS/XLSX files with common column headers.

## Local Data

The app creates a local SQLite database at:

```text
data/deals.sqlite3
```

## Disclaimer

This is an analytics prototype for comparing real estate assumptions. It is not financial advice, and results depend on the accuracy of imported rent, loan, tax, insurance, and expense estimates.
