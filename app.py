from __future__ import annotations

import re
import sqlite3
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "data" / "deals.sqlite3"
PLOTLY_CHART_CONFIG = {"displayModeBar": False}
REMOVED_DEAL_FIELDS = ["debt_service_coverage_ratio"]

NUMERIC_FIELDS = [
    "beds",
    "baths",
    "sqft",
    "year_built",
    "price",
    "zestimate",
    "monthly_rent",
    "zillow_monthly_payment",
    "principal_interest_monthly",
    "down_payment",
    "down_payment_percent",
    "loan_amount",
    "interest_rate",
    "loan_term_years",
    "taxes_monthly",
    "insurance_monthly",
    "hoa_monthly",
    "pmi_monthly",
    "maintenance_monthly",
    "utilities_monthly",
    "electricity_monthly",
    "water_monthly",
    "gas_monthly",
    "internet_monthly",
    "trash_monthly",
    "capex_monthly",
    "vacancy_monthly",
    "property_mgmt_monthly",
    "other_expenses_monthly",
    "closing_costs",
    "monthly_expenses",
    "monthly_cash_flow",
    "annual_cash_flow",
    "cap_rate",
    "cash_on_cash_roi",
    "one_percent_rule",
    "total_investment",
]

TEXT_FIELDS = [
    "source_file",
    "imported_at",
    "address",
    "city",
    "state",
    "zip_code",
    "property_url",
    "property_type",
    "investment_grade",
    "analysis_date",
    "notes",
]

FIELD_ALIASES = {
    "address": ["address", "property address", "street address", "full address"],
    "city": ["city"],
    "state": ["state"],
    "zip_code": ["zip", "zip code", "zipcode", "postal code"],
    "property_url": ["url", "property url", "zillow url", "listing url", "property link"],
    "property_type": ["property type", "home type", "type"],
    "beds": ["beds", "bedrooms", "bed"],
    "baths": ["baths", "bathrooms", "bath"],
    "sqft": ["sqft", "square feet", "living area", "home size"],
    "year_built": ["year built", "built"],
    "price": ["price", "list price", "purchase price", "sale price", "asking price"],
    "zestimate": ["zestimate", "zillow estimate"],
    "monthly_rent": ["rent", "monthly rent", "rent estimate", "zillow rent estimate"],
    "zillow_monthly_payment": [
        "zillow monthly payment",
        "estimated monthly payment",
        "monthly payment",
        "mortgage payment",
    ],
    "principal_interest_monthly": ["principal & interest", "principal and interest"],
    "down_payment": ["down payment", "down payment amount", "cash down"],
    "down_payment_percent": ["down payment %", "down payment percent"],
    "loan_amount": ["loan amount", "mortgage amount", "principal"],
    "interest_rate": ["interest rate", "rate", "apr"],
    "loan_term_years": ["loan term", "loan term years", "term years"],
    "taxes_monthly": ["taxes", "property taxes", "monthly taxes", "tax/month"],
    "insurance_monthly": ["insurance", "home insurance", "monthly insurance"],
    "hoa_monthly": ["hoa", "hoa dues", "monthly hoa"],
    "pmi_monthly": ["pmi", "mortgage insurance"],
    "maintenance_monthly": ["maintenance", "monthly maintenance"],
    "utilities_monthly": ["utilities", "monthly utilities"],
    "electricity_monthly": ["electricity"],
    "water_monthly": ["water"],
    "gas_monthly": ["gas"],
    "internet_monthly": ["internet"],
    "trash_monthly": ["trash"],
    "capex_monthly": ["capex", "capital expenditures", "monthly capex"],
    "vacancy_monthly": ["vacancy", "vacancy reserve", "monthly vacancy"],
    "property_mgmt_monthly": [
        "property management",
        "property mgmt",
        "management fee",
        "monthly management",
    ],
    "other_expenses_monthly": ["other expenses", "misc expenses", "other monthly expenses"],
    "closing_costs": ["closing costs"],
    "monthly_expenses": ["monthly expenses", "total monthly expenses", "expenses"],
    "monthly_cash_flow": ["cash flow", "monthly cash flow", "net cash flow"],
    "annual_cash_flow": ["annual cash flow"],
    "cap_rate": ["cap rate", "capitalization rate"],
    "cash_on_cash_roi": ["cash on cash roi", "cash-on-cash roi", "coc roi", "cash on cash return"],
    "one_percent_rule": ["1% rule", "one percent rule", "rent to price", "rent/price"],
    "total_investment": ["total investment", "cash needed", "total cash needed", "cash invested"],
    "investment_grade": ["investment grade", "grade", "rating"],
    "analysis_date": ["analysis date"],
    "notes": ["notes", "comments"],
}

DISPLAY_NAMES = {
    "id": "ID",
    "address": "Address",
    "city": "City",
    "state": "State",
    "price": "Price",
    "monthly_rent": "Rental Income",
    "zillow_monthly_payment": "Mortgage Payment",
    "principal_interest_monthly": "Principal & Interest",
    "down_payment": "Down Payment",
    "down_payment_percent": "Down Payment %",
    "loan_amount": "Loan Amount",
    "interest_rate": "Interest Rate",
    "loan_term_years": "Loan Term",
    "taxes_monthly": "Taxes",
    "insurance_monthly": "Insurance",
    "hoa_monthly": "HOA",
    "pmi_monthly": "PMI",
    "maintenance_monthly": "Maintenance",
    "utilities_monthly": "Utilities",
    "electricity_monthly": "Electricity",
    "water_monthly": "Water",
    "gas_monthly": "Gas",
    "internet_monthly": "Internet",
    "trash_monthly": "Trash",
    "closing_costs": "Closing Costs",
    "monthly_expenses": "Monthly Payment",
    "monthly_cash_flow": "Cash Flow",
    "annual_cash_flow": "Annual Cash Flow",
    "cap_rate": "Cap Rate",
    "cash_on_cash_roi": "Cash-on-Cash ROI",
    "one_percent_rule": "1% Rule",
    "total_investment": "Total Investment",
    "investment_grade": "Grade",
    "analysis_date": "Analysis Date",
    "property_url": "Zillow URL",
}

SECTION_NAMES = {
    "PROPERTY DETAILS",
    "ZILLOW PAYMENT ESTIMATE",
    "PURCHASE INFORMATION",
    "LOAN INFORMATION",
    "MONTHLY EXPENSES",
    "INCOME & CASH FLOW",
    "INVESTMENT METRICS",
    "NOTES",
}

METRIC_EXPORT_ALIASES = {
    ("PROPERTY DETAILS", "Address"): "address",
    ("PROPERTY DETAILS", "Price"): "price",
    ("PROPERTY DETAILS", "Bedrooms"): "beds",
    ("PROPERTY DETAILS", "Bathrooms"): "baths",
    ("PROPERTY DETAILS", "Square Feet"): "sqft",
    ("PROPERTY DETAILS", "Year Built"): "year_built",
    ("ZILLOW PAYMENT ESTIMATE", "Estimated Monthly Payment"): "zillow_monthly_payment",
    ("ZILLOW PAYMENT ESTIMATE", "Principal & Interest"): "principal_interest_monthly",
    ("ZILLOW PAYMENT ESTIMATE", "Mortgage Insurance"): "pmi_monthly",
    ("ZILLOW PAYMENT ESTIMATE", "Property Taxes"): "taxes_monthly",
    ("ZILLOW PAYMENT ESTIMATE", "Home Insurance"): "insurance_monthly",
    ("ZILLOW PAYMENT ESTIMATE", "HOA Fees"): "hoa_monthly",
    ("ZILLOW PAYMENT ESTIMATE", "Utilities"): "utilities_monthly",
    ("PURCHASE INFORMATION", "Purchase Type"): "property_type",
    ("PURCHASE INFORMATION", "Total Investment"): "total_investment",
    ("LOAN INFORMATION", "Down Payment %"): "down_payment_percent",
    ("LOAN INFORMATION", "Interest Rate %"): "interest_rate",
    ("LOAN INFORMATION", "Loan Term"): "loan_term_years",
    ("LOAN INFORMATION", "Down Payment"): "down_payment",
    ("LOAN INFORMATION", "Loan Amount"): "loan_amount",
    ("LOAN INFORMATION", "Monthly Payment"): "zillow_monthly_payment",
    ("LOAN INFORMATION", "Closing Costs"): "closing_costs",
    ("MONTHLY EXPENSES", "Property Tax"): "taxes_monthly",
    ("MONTHLY EXPENSES", "Insurance"): "insurance_monthly",
    ("MONTHLY EXPENSES", "Mortgage Insurance"): "pmi_monthly",
    ("MONTHLY EXPENSES", "HOA Fees"): "hoa_monthly",
    ("MONTHLY EXPENSES", "Maintenance"): "maintenance_monthly",
    ("MONTHLY EXPENSES", "Electricity"): "electricity_monthly",
    ("MONTHLY EXPENSES", "Water"): "water_monthly",
    ("MONTHLY EXPENSES", "Gas"): "gas_monthly",
    ("MONTHLY EXPENSES", "Internet"): "internet_monthly",
    ("MONTHLY EXPENSES", "Trash"): "trash_monthly",
    ("MONTHLY EXPENSES", "Other Utilities"): "other_expenses_monthly",
    ("MONTHLY EXPENSES", "Total Monthly Expenses"): "monthly_expenses",
    ("INCOME & CASH FLOW", "Monthly Rental Income"): "monthly_rent",
    ("INCOME & CASH FLOW", "Monthly Cash Flow"): "monthly_cash_flow",
    ("INCOME & CASH FLOW", "Annual Cash Flow"): "annual_cash_flow",
    ("INVESTMENT METRICS", "Investment Grade"): "investment_grade",
    ("INVESTMENT METRICS", "Cash-on-Cash ROI"): "cash_on_cash_roi",
    ("INVESTMENT METRICS", "Cap Rate"): "cap_rate",
    ("INVESTMENT METRICS", "1% Rule"): "one_percent_rule",
    ("NOTES", "Property URL"): "property_url",
    ("NOTES", "Analysis Date"): "analysis_date",
}


def normalize_header(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def parse_number(value: Any) -> float | None:
    if pd.isna(value) or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    is_percent = "%" in text
    cleaned = re.sub(r"[^0-9.\-]", "", text)
    if cleaned in {"", "-", "."}:
        return None

    try:
        number = float(cleaned)
    except ValueError:
        return None

    if is_percent and abs(number) > 1:
        return number / 100
    return number


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).replace("\xa0", " ").strip()


def split_address(address: str | None) -> tuple[str | None, str | None, str | None]:
    if not address:
        return None, None, None

    match = re.search(r",\s*([^,]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$", address)
    if not match:
        return None, None, None
    return match.group(1).strip(), match.group(2), match.group(3)


def display_money(value: Any) -> str:
    number = parse_number(value)
    return "" if number is None else f"${number:,.0f}"


def display_percent(value: Any) -> str:
    number = parse_number(value)
    if number is None:
        return ""
    return f"{number * 100:.2f}%" if abs(number) <= 1 else f"{number:.2f}%"


def field_sql_type(field: str) -> str:
    return "TEXT" if field in TEXT_FIELDS else "REAL"


def init_db() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    all_fields = TEXT_FIELDS + NUMERIC_FIELDS
    columns = [f"{field} {field_sql_type(field)}" for field in all_fields]
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {", ".join(columns)}
            )
            """
        )
        existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(deals)")}
        for field in all_fields:
            if field not in existing_columns:
                conn.execute(f"ALTER TABLE deals ADD COLUMN {field} {field_sql_type(field)}")
        remove_obsolete_deal_columns(conn)
        resequence_deal_ids(conn)


def remove_obsolete_deal_columns(conn: sqlite3.Connection) -> None:
    existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(deals)")}
    obsolete_columns = [field for field in REMOVED_DEAL_FIELDS if field in existing_columns]
    if not obsolete_columns:
        return

    for field in obsolete_columns:
        try:
            conn.execute(f"ALTER TABLE deals DROP COLUMN {field}")
        except sqlite3.OperationalError:
            rebuild_deals_table(conn)
            return


def rebuild_deals_table(conn: sqlite3.Connection) -> None:
    all_fields = TEXT_FIELDS + NUMERIC_FIELDS
    columns = [f"{field} {field_sql_type(field)}" for field in all_fields]
    existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(deals)")}
    copy_columns = ["id"] + [field for field in all_fields if field in existing_columns]
    column_sql = ", ".join(copy_columns)

    conn.execute(
        f"""
        CREATE TABLE deals_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {", ".join(columns)}
        )
        """
    )
    conn.execute(f"INSERT INTO deals_new ({column_sql}) SELECT {column_sql} FROM deals")
    conn.execute("DROP TABLE deals")
    conn.execute("ALTER TABLE deals_new RENAME TO deals")


def resequence_deal_ids(conn: sqlite3.Connection) -> None:
    rows = conn.execute("SELECT id FROM deals ORDER BY id").fetchall()
    for new_id, (old_id,) in enumerate(rows, start=1):
        if old_id != new_id:
            conn.execute("UPDATE deals SET id = ? WHERE id = ?", (new_id, old_id))

    if rows:
        sequence_exists = conn.execute("SELECT 1 FROM sqlite_sequence WHERE name = 'deals'").fetchone()
        if sequence_exists:
            conn.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = 'deals'", (len(rows),))
        else:
            conn.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('deals', ?)", (len(rows),))
    else:
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'deals'")


def read_uploaded_file(uploaded_file: Any) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    content = uploaded_file.getvalue()

    if b"<html" in content[:500].lower() or b"<table" in content[:500].lower():
        tables = pd.read_html(BytesIO(content), header=None)
        if not tables:
            raise ValueError("No table found in the HTML spreadsheet export.")
        return tables[0]

    if name.endswith(".csv"):
        return pd.read_csv(BytesIO(content))
    if name.endswith((".xls", ".xlsx")):
        return pd.read_excel(BytesIO(content))
    raise ValueError("Unsupported file type. Upload a CSV, XLS, or XLSX file.")


def build_column_map(columns: list[str]) -> dict[str, str]:
    normalized_to_source = {normalize_header(column): column for column in columns}
    column_map = {}

    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            normalized_alias = normalize_header(alias)
            if normalized_alias in normalized_to_source:
                column_map[field] = normalized_to_source[normalized_alias]
                break

    return column_map


def first_present(row: pd.Series, column_name: str | None) -> Any:
    if column_name is None:
        return None
    value = row.get(column_name)
    return None if pd.isna(value) else value


def is_metric_value_export(raw_df: pd.DataFrame) -> bool:
    first_column_values = {clean_text(value).lower() for value in raw_df.iloc[:, 0].dropna().tolist()}
    return "metric" in first_column_values and "property details" in first_column_values


def normalize_metric_value_export(
    raw_df: pd.DataFrame, source_file: str
) -> tuple[pd.DataFrame, dict[str, str], list[str]]:
    deal: dict[str, Any] = {field: None for field in TEXT_FIELDS + NUMERIC_FIELDS}
    deal["source_file"] = source_file
    deal["imported_at"] = datetime.utcnow().isoformat(timespec="seconds")

    current_section = ""
    column_map: dict[str, str] = {}
    unmapped_metrics = []

    for _, row in raw_df.iterrows():
        metric = clean_text(row.iloc[0] if len(row) > 0 else "")
        value = clean_text(row.iloc[1] if len(row) > 1 else "")
        if not metric or metric.lower() == "metric":
            continue

        normalized_metric = metric.upper().replace("&AMP;", "&")
        if normalized_metric in SECTION_NAMES and not value:
            current_section = normalized_metric
            continue

        field = METRIC_EXPORT_ALIASES.get((current_section, metric))
        if field is None:
            if value:
                unmapped_metrics.append(f"{current_section}: {metric}")
            continue

        column_map[field] = f"{current_section} > {metric}"
        if field in TEXT_FIELDS:
            deal[field] = value or None
        elif field in NUMERIC_FIELDS:
            deal[field] = parse_number(value)

    if deal.get("address"):
        city, state, zip_code = split_address(deal["address"])
        deal["city"] = deal.get("city") or city
        deal["state"] = deal.get("state") or state
        deal["zip_code"] = deal.get("zip_code") or zip_code

    deal = compute_deal_metrics(deal)
    return pd.DataFrame([deal]), column_map, unmapped_metrics


def compute_deal_metrics(deal: dict[str, Any]) -> dict[str, Any]:
    price = deal.get("price") or deal.get("zestimate")
    rent = deal.get("monthly_rent")

    recurring_expense_fields = [
        "zillow_monthly_payment",
        "taxes_monthly",
        "insurance_monthly",
        "hoa_monthly",
        "pmi_monthly",
        "maintenance_monthly",
        "utilities_monthly",
        "electricity_monthly",
        "water_monthly",
        "gas_monthly",
        "internet_monthly",
        "trash_monthly",
        "capex_monthly",
        "vacancy_monthly",
        "property_mgmt_monthly",
        "other_expenses_monthly",
    ]
    operating_expense_fields = [
        "taxes_monthly",
        "insurance_monthly",
        "hoa_monthly",
        "maintenance_monthly",
        "utilities_monthly",
        "electricity_monthly",
        "water_monthly",
        "gas_monthly",
        "internet_monthly",
        "trash_monthly",
        "capex_monthly",
        "vacancy_monthly",
        "property_mgmt_monthly",
        "other_expenses_monthly",
    ]

    recurring_expenses = sum(deal.get(field) or 0 for field in recurring_expense_fields)
    operating_expenses = sum(deal.get(field) or 0 for field in operating_expense_fields)

    if deal.get("monthly_expenses") is None and recurring_expenses:
        deal["monthly_expenses"] = recurring_expenses

    if deal.get("monthly_cash_flow") is None and rent is not None:
        deal["monthly_cash_flow"] = rent - (deal.get("monthly_expenses") or recurring_expenses)

    if deal.get("annual_cash_flow") is None and deal.get("monthly_cash_flow") is not None:
        deal["annual_cash_flow"] = deal["monthly_cash_flow"] * 12

    if price:
        # Recompute this locally because exports can represent 0.51% as 51%.
        deal["one_percent_rule"] = (rent or 0) / price

    if deal.get("cap_rate") is None and price:
        annual_noi = ((rent or 0) - operating_expenses) * 12
        deal["cap_rate"] = annual_noi / price

    if deal.get("total_investment") is None:
        down_payment = deal.get("down_payment")
        if down_payment is not None:
            deal["total_investment"] = down_payment
        elif price and deal.get("loan_amount"):
            deal["total_investment"] = price - deal["loan_amount"]

    if deal.get("cash_on_cash_roi") is None and deal.get("total_investment"):
        deal["cash_on_cash_roi"] = ((deal.get("monthly_cash_flow") or 0) * 12) / deal["total_investment"]

    deal["investment_grade"] = grade_deal(deal)

    return deal


def grade_deal(deal: dict[str, Any]) -> str:
    score = 0
    cash_on_cash_roi = deal.get("cash_on_cash_roi") or 0
    cap_rate = deal.get("cap_rate") or 0
    one_percent_rule = deal.get("one_percent_rule") or 0

    if cash_on_cash_roi >= 0.08:
        score += 25
    elif cash_on_cash_roi >= 0.06:
        score += 20
    elif cash_on_cash_roi >= 0.04:
        score += 15
    elif cash_on_cash_roi >= 0.02:
        score += 10
    elif cash_on_cash_roi >= 0:
        score += 5

    if cap_rate >= 0.08:
        score += 25
    elif cap_rate >= 0.06:
        score += 20
    elif cap_rate >= 0.04:
        score += 15
    elif cap_rate >= 0.02:
        score += 10
    else:
        score += 5

    if one_percent_rule >= 0.012:
        score += 25
    elif one_percent_rule >= 0.01:
        score += 20
    elif one_percent_rule >= 0.008:
        score += 15
    elif one_percent_rule >= 0.006:
        score += 10
    else:
        score += 5

    normalized_score = (score / 75) * 100
    if normalized_score >= 80:
        return "A"
    if normalized_score >= 70:
        return "B"
    if normalized_score > 60:
        return "C"
    if normalized_score >= 50:
        return "D"
    return "F"


def normalize_deals(raw_df: pd.DataFrame, source_file: str) -> tuple[pd.DataFrame, dict[str, str], list[str]]:
    raw_df = raw_df.dropna(how="all")
    if is_metric_value_export(raw_df):
        return normalize_metric_value_export(raw_df, source_file)

    column_map = build_column_map(list(raw_df.columns))
    imported_at = datetime.utcnow().isoformat(timespec="seconds")
    records = []

    for _, row in raw_df.iterrows():
        deal: dict[str, Any] = {field: None for field in TEXT_FIELDS + NUMERIC_FIELDS}
        deal["source_file"] = source_file
        deal["imported_at"] = imported_at

        for field in TEXT_FIELDS:
            if field in {"source_file", "imported_at"}:
                continue
            value = first_present(row, column_map.get(field))
            deal[field] = None if value is None else clean_text(value)

        for field in NUMERIC_FIELDS:
            deal[field] = parse_number(first_present(row, column_map.get(field)))

        records.append(compute_deal_metrics(deal))

    unmapped_columns = [column for column in raw_df.columns if column not in set(column_map.values())]
    return pd.DataFrame(records), column_map, unmapped_columns


def save_deals(deals_df: pd.DataFrame) -> int:
    if deals_df.empty:
        return 0
    with sqlite3.connect(DB_PATH) as conn:
        deals_df[TEXT_FIELDS + NUMERIC_FIELDS].to_sql("deals", conn, if_exists="append", index=False)
    return len(deals_df)


def load_deals() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        resequence_deal_ids(conn)
        deals = pd.read_sql_query("SELECT * FROM deals ORDER BY id DESC", conn)

    if deals.empty:
        return deals

    # Recalculate saved deals on display so old imports do not keep stale exported metrics.
    recalculated = []
    for record in deals.to_dict("records"):
        recalculated.append(compute_deal_metrics(record))
    return pd.DataFrame(recalculated)


def delete_deal(deal_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
        resequence_deal_ids(conn)


def apply_filters(deals: pd.DataFrame) -> pd.DataFrame:
    filtered = deals.copy()

    st.sidebar.header("Filters")
    if filtered.empty:
        return filtered

    max_price = int(filtered["price"].dropna().max()) if filtered["price"].notna().any() else 0
    price_max = st.sidebar.number_input(
        "Max price",
        min_value=0,
        max_value=max_price if max_price > 0 else None,
        value=0,
        step=10_000,
        help="Leave at 0 to show all prices.",
    )
    cash_flow_min = st.sidebar.number_input("Min cash flow", value=0, step=50, help="Leave at 0 to show all cash flow values.")
    roi_min = (
        st.sidebar.number_input("Min ROI (%)", value=0.0, step=1.0, help="Leave at 0 to show all ROI values.") / 100
    )
    grades = sorted(grade for grade in filtered["investment_grade"].dropna().unique())
    selected_grades = st.sidebar.multiselect("Grade", grades)

    if price_max > 0:
        filtered = filtered[filtered["price"].fillna(0) <= price_max]
    if cash_flow_min != 0:
        filtered = filtered[filtered["monthly_cash_flow"].fillna(-999999) >= cash_flow_min]
    if roi_min != 0:
        filtered = filtered[filtered["cash_on_cash_roi"].fillna(-999999) >= roi_min]
    if selected_grades:
        filtered = filtered[filtered["investment_grade"].isin(selected_grades)]

    return filtered


def show_upload() -> None:
    st.sidebar.header("Import")
    uploaded_file = st.sidebar.file_uploader("Zillow export", type=["csv", "xls", "xlsx"])

    if uploaded_file is None:
        st.sidebar.caption("Upload a CSV/XLS export from the Chrome extension.")
        return

    try:
        raw_df = read_uploaded_file(uploaded_file)
        deals_df, column_map, unmapped_columns = normalize_deals(raw_df, uploaded_file.name)
    except Exception as exc:
        st.sidebar.error(f"Could not parse upload: {exc}")
        return

    st.sidebar.success(f"Ready to save {len(deals_df)} deal(s).")

    preview_columns = ["address", "price", "monthly_cash_flow", "cash_on_cash_roi", "investment_grade"]
    preview = format_deals_for_display(deals_df)
    preview = preview[[DISPLAY_NAMES[column] for column in preview_columns if DISPLAY_NAMES[column] in preview.columns]]
    st.sidebar.dataframe(preview, width="stretch", hide_index=True)

    with st.sidebar.expander("Import details"):
        st.write("Detected fields")
        st.dataframe(
            pd.DataFrame(
                [{"Deal field": field, "Spreadsheet field": column} for field, column in column_map.items()]
            ),
            width="stretch",
            hide_index=True,
        )
        if unmapped_columns:
            st.caption("Unmapped: " + ", ".join(map(str, unmapped_columns)))

    if st.sidebar.button("Save deals", type="primary", width="stretch"):
        saved_count = save_deals(deals_df)
        st.sidebar.success(f"Saved {saved_count} deal(s).")
        st.rerun()


def format_deals_for_display(deals: pd.DataFrame) -> pd.DataFrame:
    if deals.empty:
        return deals

    display = deals.copy()
    money_fields = [
        "price",
        "monthly_rent",
        "zillow_monthly_payment",
        "principal_interest_monthly",
        "down_payment",
        "loan_amount",
        "taxes_monthly",
        "insurance_monthly",
        "hoa_monthly",
        "pmi_monthly",
        "maintenance_monthly",
        "utilities_monthly",
        "electricity_monthly",
        "water_monthly",
        "gas_monthly",
        "internet_monthly",
        "trash_monthly",
        "closing_costs",
        "monthly_expenses",
        "monthly_cash_flow",
        "annual_cash_flow",
        "total_investment",
    ]
    percent_fields = ["cap_rate", "cash_on_cash_roi", "one_percent_rule", "interest_rate", "down_payment_percent"]

    for field in money_fields:
        if field in display:
            display[field] = display[field].map(display_money)
    for field in percent_fields:
        if field in display:
            display[field] = display[field].map(display_percent)

    preferred_columns = [
        "id",
        "address",
        "city",
        "state",
        "price",
        "monthly_expenses",
        "monthly_rent",
        "monthly_cash_flow",
        "cap_rate",
        "cash_on_cash_roi",
        "one_percent_rule",
        "total_investment",
        "investment_grade",
        "property_url",
    ]
    display = display[[column for column in preferred_columns if column in display.columns]]
    return display.rename(columns=DISPLAY_NAMES)


def format_detail_value(field: str, value: Any) -> str:
    if pd.isna(value) or value == "":
        return ""

    money_fields = {
        "price",
        "zestimate",
        "monthly_rent",
        "zillow_monthly_payment",
        "principal_interest_monthly",
        "down_payment",
        "loan_amount",
        "taxes_monthly",
        "insurance_monthly",
        "hoa_monthly",
        "pmi_monthly",
        "maintenance_monthly",
        "utilities_monthly",
        "electricity_monthly",
        "water_monthly",
        "gas_monthly",
        "internet_monthly",
        "trash_monthly",
        "capex_monthly",
        "vacancy_monthly",
        "property_mgmt_monthly",
        "other_expenses_monthly",
        "closing_costs",
        "monthly_expenses",
        "monthly_cash_flow",
        "annual_cash_flow",
        "total_investment",
    }
    percent_fields = {"interest_rate", "down_payment_percent", "cap_rate", "cash_on_cash_roi", "one_percent_rule"}

    if field in money_fields:
        return display_money(value)
    if field in percent_fields:
        return display_percent(value)
    if field in {"beds", "baths", "sqft", "year_built", "loan_term_years"}:
        number = parse_number(value)
        return "" if number is None else f"{number:,.0f}"
    return str(value)


def operating_expenses_for(deal: pd.Series) -> float:
    fields = [
        "taxes_monthly",
        "insurance_monthly",
        "hoa_monthly",
        "pmi_monthly",
        "maintenance_monthly",
        "utilities_monthly",
        "electricity_monthly",
        "water_monthly",
        "gas_monthly",
        "internet_monthly",
        "trash_monthly",
        "capex_monthly",
        "vacancy_monthly",
        "property_mgmt_monthly",
        "other_expenses_monthly",
    ]
    return sum(parse_number(deal.get(field)) or 0 for field in fields)


def grade_breakdown(deal: pd.Series) -> pd.DataFrame:
    price = parse_number(deal.get("price")) or 0
    total_investment = parse_number(deal.get("total_investment")) or 0
    operating_expenses = operating_expenses_for(deal)

    checks = [
        {
            "Metric": "Cap rate",
            "Current": display_percent(deal.get("cap_rate")),
            "Target": "8% excellent, 6% good, 4% average",
            "Pass": (parse_number(deal.get("cap_rate")) or 0) >= 0.04,
            "How to improve": (
                f"At this price, rent needs to support about {display_money(operating_expenses + (price * 0.06 / 12))} "
                "before debt service for a good cap rate."
            ),
        },
        {
            "Metric": "Cash-on-cash ROI",
            "Current": display_percent(deal.get("cash_on_cash_roi")),
            "Target": "8% excellent, 6% good, 4% acceptable",
            "Pass": (parse_number(deal.get("cash_on_cash_roi")) or 0) >= 0.04,
            "How to improve": (
                f"Target at least {display_money(total_investment * 0.06 / 12)} monthly cash flow for a good ROI, "
                "or reduce cash needed at closing."
            ),
        },
        {
            "Metric": "1% rule",
            "Current": display_percent(deal.get("one_percent_rule")),
            "Target": "1.2% excellent, 1% meets, 0.8% close",
            "Pass": (parse_number(deal.get("one_percent_rule")) or 0) >= 0.008,
            "How to improve": f"Monthly rent would need to be about {display_money(price * 0.01)} at this price.",
        },
    ]

    for check in checks:
        check["Status"] = "Good" if check.pop("Pass") else "Bad"

    return pd.DataFrame(checks, columns=["Metric", "Current", "Target", "Status", "How to improve"])


def show_listing_details(deals: pd.DataFrame) -> None:
    st.subheader("Listing Details & Grade")
    if deals.empty:
        st.info("No listing selected because the current filters hide all deals.")
        return

    options = {
        f"#{int(row.id)} - {row.address or 'Unknown address'}": int(row.id)
        for row in deals.sort_values("id", ascending=False).itertuples()
    }
    selected_label = st.selectbox("Choose a listing to inspect", options.keys())
    selected_deal = deals[deals["id"] == options[selected_label]].iloc[0]

    grade = selected_deal.get("investment_grade") or grade_deal(selected_deal.to_dict())
    cash_flow = display_money(selected_deal.get("monthly_cash_flow"))
    roi = display_percent(selected_deal.get("cash_on_cash_roi"))
    cap_rate = display_percent(selected_deal.get("cap_rate"))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Grade", grade)
    col2.metric("Cash Flow", cash_flow)
    col3.metric("ROI", roi)
    col4.metric("Cap Rate", cap_rate)

    st.write("What is bad and what would make it good")
    st.dataframe(grade_breakdown(selected_deal), width="stretch", hide_index=True)

    detail_groups = {
        "Property": [
            "address",
            "city",
            "state",
            "zip_code",
            "property_type",
            "beds",
            "baths",
            "sqft",
            "year_built",
            "price",
            "property_url",
            "analysis_date",
        ],
        "Loan & Purchase": [
            "total_investment",
            "down_payment",
            "down_payment_percent",
            "loan_amount",
            "interest_rate",
            "loan_term_years",
            "zillow_monthly_payment",
            "principal_interest_monthly",
            "closing_costs",
        ],
        "Expenses": [
            "taxes_monthly",
            "insurance_monthly",
            "hoa_monthly",
            "pmi_monthly",
            "maintenance_monthly",
            "utilities_monthly",
            "electricity_monthly",
            "water_monthly",
            "gas_monthly",
            "internet_monthly",
            "trash_monthly",
            "other_expenses_monthly",
            "monthly_expenses",
        ],
        "Performance": [
            "monthly_rent",
            "monthly_cash_flow",
            "annual_cash_flow",
            "cap_rate",
            "cash_on_cash_roi",
            "one_percent_rule",
            "investment_grade",
        ],
    }

    rows = []
    for group, fields in detail_groups.items():
        for field in fields:
            if field in selected_deal.index:
                value = format_detail_value(field, selected_deal.get(field))
                if value:
                    rows.append({"Section": group, "Field": DISPLAY_NAMES.get(field, field.replace("_", " ").title()), "Value": value})

    st.write("All saved listing data")
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def show_metrics(deals: pd.DataFrame) -> None:
    if deals.empty:
        st.info("No deals match the current filters.")
        return

    best_cash_flow = deals["monthly_cash_flow"].max()
    best_roi = deals["cash_on_cash_roi"].max()
    median_cap = deals["cap_rate"].median()
    average_investment = deals["total_investment"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Deals", f"{len(deals):,}")
    col2.metric("Best cash flow", display_money(best_cash_flow))
    col3.metric("Best cash-on-cash ROI", display_percent(best_roi))
    col4.metric("Median cap rate", display_percent(median_cap))
    st.caption(f"Average total investment: {display_money(average_investment)}")


def show_rankings(deals: pd.DataFrame) -> None:
    st.subheader("Rankings")
    tabs = st.tabs(["Cash Flow", "Cap Rate", "Cash-on-Cash ROI", "1% Rule", "Lowest Investment"])
    rankings = [
        ("monthly_cash_flow", False),
        ("cap_rate", False),
        ("cash_on_cash_roi", False),
        ("one_percent_rule", False),
        ("total_investment", True),
    ]

    for tab, (field, ascending) in zip(tabs, rankings):
        with tab:
            ranked = deals.sort_values(field, ascending=ascending, na_position="last").head(10)
            ranked_display = format_deals_for_display(ranked)
            ranked_display.insert(0, "Rank", range(1, len(ranked_display) + 1))
            st.dataframe(ranked_display, width="stretch", hide_index=True)


def show_charts(deals: pd.DataFrame) -> None:
    st.subheader("Charts")
    chart_df = deals.copy()
    chart_df["label"] = chart_df["address"].fillna("Deal #" + chart_df["id"].astype(str))

    listing_options = {
        f"#{int(row.id)} - {row.label}": int(row.id)
        for row in chart_df.sort_values("id", ascending=False).itertuples()
    }
    primary_label = st.selectbox("Listing for monthly cost breakdown", list(listing_options.keys()))
    primary_id = listing_options[primary_label]
    primary_deal = chart_df[chart_df["id"] == primary_id].iloc[0]

    expense_fields = [
        "zillow_monthly_payment",
        "taxes_monthly",
        "insurance_monthly",
        "hoa_monthly",
        "pmi_monthly",
        "maintenance_monthly",
        "utilities_monthly",
        "other_expenses_monthly",
    ]
    expense_rows = [
        {"Expense": DISPLAY_NAMES.get(field, field), "Monthly Cost": parse_number(primary_deal.get(field)) or 0}
        for field in expense_fields
        if (parse_number(primary_deal.get(field)) or 0) != 0
    ]
    if expense_rows:
        st.plotly_chart(
            px.bar(pd.DataFrame(expense_rows), x="Expense", y="Monthly Cost", title="Monthly Cost Breakdown"),
            width="stretch",
            config=PLOTLY_CHART_CONFIG,
        )
    else:
        st.caption("No non-zero monthly expense fields were found for this listing.")

    if len(chart_df) < 2:
        st.info("Save at least two deals to compare listings on another chart.")
        return

    st.subheader("Compare Listings")
    metric_options = {
        "Price": "price",
        "Rental income": "monthly_rent",
        "Monthly payment": "monthly_expenses",
        "Mortgage payment": "zillow_monthly_payment",
        "Monthly cash flow": "monthly_cash_flow",
        "Annual cash flow": "annual_cash_flow",
        "Cap rate": "cap_rate",
        "Cash-on-cash ROI": "cash_on_cash_roi",
        "1% rule": "one_percent_rule",
        "Total investment": "total_investment",
    }
    percent_metrics = {"cap_rate", "cash_on_cash_roi", "one_percent_rule"}
    selected_metric_label = st.selectbox("Comparison metric", list(metric_options.keys()))
    selected_metric = metric_options[selected_metric_label]

    comparison_options = {label: deal_id for label, deal_id in listing_options.items() if deal_id != primary_id}
    comparison_labels = st.multiselect(
        "Compare with",
        list(comparison_options.keys()),
        default=list(comparison_options.keys())[:1],
    )
    selected_ids = [primary_id] + [comparison_options[label] for label in comparison_labels]
    comparison_df = chart_df[chart_df["id"].isin(selected_ids)].copy()

    chart_value_field = f"{selected_metric}_chart_value"
    comparison_df[chart_value_field] = pd.to_numeric(comparison_df[selected_metric], errors="coerce")
    y_axis_title = selected_metric_label
    if selected_metric in percent_metrics:
        comparison_df[chart_value_field] = comparison_df[chart_value_field] * 100
        y_axis_title = f"{selected_metric_label} (%)"

    comparison_df = comparison_df.sort_values(chart_value_field, ascending=False, na_position="last")
    st.plotly_chart(
        px.bar(
            comparison_df,
            x="label",
            y=chart_value_field,
            color="investment_grade",
            hover_data=["price", "monthly_rent", "monthly_cash_flow", "cap_rate", "cash_on_cash_roi"],
            title=f"{selected_metric_label} Comparison",
            labels={"label": "Listing", chart_value_field: y_axis_title, "investment_grade": "Grade"},
        ),
        width="stretch",
        config=PLOTLY_CHART_CONFIG,
    )

    st.write("Selected listing comparison")
    display_columns = [
        "id",
        "address",
        "price",
        "monthly_expenses",
        "monthly_rent",
        "monthly_cash_flow",
        "cap_rate",
        "cash_on_cash_roi",
        "total_investment",
        "investment_grade",
    ]
    st.dataframe(format_deals_for_display(comparison_df[display_columns]), width="stretch", hide_index=True)


def show_delete(deals: pd.DataFrame) -> None:
    st.subheader("Delete a Deal")
    if deals.empty:
        st.info("No saved deals to delete.")
        return

    options = {
        f"#{int(row.id)} - {row.address or 'Unknown address'} ({display_money(row.price)})": int(row.id)
        for row in deals.itertuples()
    }
    selected = st.selectbox("Choose a deal to delete", options.keys())
    if st.button("Delete selected deal"):
        delete_deal(options[selected])
        st.success("Deal deleted.")
        st.rerun()


def show_empty_state() -> None:
    st.info("No saved deals yet. Upload a Zillow export from the sidebar to get started.")


def apply_page_style() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        div[data-testid="stMetric"] {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"],
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #f8fafc !important;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            font-weight: 700;
        }
        h1, h2, h3 {
            letter-spacing: -0.02em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Zillow Analytics", page_icon=":house:", layout="wide")
    apply_page_style()
    init_db()

    show_upload()

    st.title("Zillow Analytics")
    st.caption("Compare Zillow extension exports by cash flow, ROI, cap rate, and total cash needed.")

    deals = load_deals()
    filtered_deals = apply_filters(deals)

    if deals.empty:
        show_empty_state()
        return

    overview_tab, rankings_tab, charts_tab, manage_tab = st.tabs(["Overview", "Rankings", "Charts", "Manage"])

    with overview_tab:
        show_metrics(filtered_deals)
        st.subheader("Saved Deals")
        if filtered_deals.empty:
            st.info("No deals match the filters in the sidebar.")
        else:
            st.dataframe(format_deals_for_display(filtered_deals), width="stretch", hide_index=True)
            show_listing_details(filtered_deals)

    with rankings_tab:
        if filtered_deals.empty:
            st.info("No ranked deals match the current filters.")
        else:
            show_rankings(filtered_deals)

    with charts_tab:
        if filtered_deals.empty:
            st.info("No chart data matches the current filters.")
        else:
            show_charts(filtered_deals)

    with manage_tab:
        show_delete(deals)


if __name__ == "__main__":
    main()
