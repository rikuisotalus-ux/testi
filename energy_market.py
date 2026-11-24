import pandas as pd
import csv
from datetime import datetime
import requests

URL = (
    "https://www.cmegroup.com/markets/energy/natural-gas/"
    "dutch-ttf-natural-gas-financial-calendar-month.settlements.html"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def build_product_code(month_str):
    """
    DEC 26 -> TTFDEC-26
    JAN 27 -> TTFJAN-27
    """

    try:
        month, yy = month_str.upper().split()
        return f"TTF{month}-{yy}"
    except Exception:
        return None


def scrape_cme_ttf():

    print("Hakee CME TTF settlementit...")

    session = requests.Session()
    session.headers.update(HEADERS)

    response = session.get(URL, timeout=30)
    response.raise_for_status()

    tables = pd.read_html(response.text)

    if not tables:
        raise Exception("Taulukkoa ei löytynyt")

    settlement_table = None

    for table in tables:
        cols = [str(c).upper() for c in table.columns]

        if "MONTH" in cols and "SETTLE" in cols:
            settlement_table = table
            break

    if settlement_table is None:
        raise Exception("Settlement-taulukkoa ei löytynyt")

    today = datetime.utcnow().strftime("%Y-%m-%d")

    rows = []

    for _, row in settlement_table.iterrows():

        month = str(row["Month"]).strip()

        if month.lower() == "month":
            continue

        rows.append([
            month,
            row.get("Settle"),
            row.get("Open"),
            row.get("High"),
            row.get("Low"),
            row.get("Est. Volume"),
            row.get("Prior Day OI"),
            "TTF",
            build_product_code(month),
            today,
            "CME"
        ])

    header = [
        "Delivery",
        "Settlement",
        "Open",
        "High",
        "Low",
        "Volume",
        "OpenInterest",
        "Product",
        "ProductCode",
        "Date",
        "Source"
    ]

    with open(
        "cme_ttf_settlement.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"Valmis: {len(rows)} riviä")


if __name__ == "__main__":
    scrape_cme_ttf()
