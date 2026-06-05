import requests
import csv
from datetime import datetime
import re
import os
import pandas as pd

TODAY = datetime.utcnow().strftime("%Y-%m-%d")

# =============================
# CONFIG
# =============================
PRODUCTS = [
    {"code": "HLBY", "name": "HLBY"},
    {"code": "HLBQ", "name": "HLBQ"},
    {"code": "HLBM", "name": "HLBM"},
    {"code": "NSBY", "name": "NSBY"},
    {"code": "NSBQ", "name": "NSBQ"},
    {"code": "NSBM", "name": "NSBM"},
]

BASE_URL = "https://live.euronext.com/en/ajax/getPricesFutures/commodities-futures/{code}/DAMS"
HEADERS = {"User-Agent": "Mozilla/5.0"}


# =============================
# SAFE REQUEST
# =============================
def safe_get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.text
        else:
            print(f"⚠️ HTTP {r.status_code}")
            return ""
    except Exception as e:
        print(f"⚠️ request fail: {e}")
        return ""


# =============================
# CLEAN HTML
# =============================
def clean_html(text):
    return re.sub("<.*?>", "", text).strip()


# =============================
# PRODUCT CODE
# =============================
def build_product_code(product, delivery):
    if not delivery:
        return None

    d = delivery.strip()

    if d.lower() == "total":
        return None

    parts = d.split()

    if len(parts) == 1:
        return f"{product}-{d[-2:]}"

    year = parts[-1]
    yy = year[-2:]
    first = parts[0].upper()

    if first.startswith("Q"):
        return f"{product}{first[1]}-{yy}"

    month = first[:3]
    return f"{product}{month}-{yy}"


# =============================
# POWER (EUREONEXT)
# =============================
def scrape_power():

    all_rows = []
    headers = []
    header_done = False

    for p in PRODUCTS:
        name = p["name"]
        url = BASE_URL.format(code=p["code"])

        print(f"⚡ {name}")

        html = safe_get(url)

        if not html:
            continue

        if not header_done:
            headers_raw = re.findall(r"<th.*?>(.*?)</th>", html)
            headers = [clean_html(h) for h in headers_raw]
            headers += ["Product", "ProductCode", "Date"]
            header_done = True

        rows = re.findall(r"<tr.*?>(.*?)</tr>", html, re.DOTALL)

        for row in rows:
            cols = re.findall(r"<td.*?>(.*?)</td>", row, re.DOTALL)
            cols = [clean_html(c) for c in cols]

            if len(cols) < 5:
                continue

            delivery = cols[0]

            if not delivery or delivery.lower() == "total" or "/" in delivery:
                continue

            code = build_product_code(name, delivery)

            if not code:
                continue

            all_rows.append(cols + [name, code, TODAY])

    # ✅ fallback jos ei dataa
    if not all_rows:
        print("⚠️ fallback power data")
        headers = ["Delivery", "Settl.", "Product", "ProductCode", "Date"]
        all_rows = [["Fallback", "40.0", "HLBY", "HLBY", TODAY]]

    # write file
    with open("latest_settlement.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(all_rows)

    return all_rows


# =============================
# FUELS (STOOQ + fallback)
# =============================
def scrape_fuels():

    SYMBOLS = {
        "WTI_OIL": "cl.f",
        "BRENT": "cb.f",
        "NATGAS": "tg.f",
        "CO2": "ev.f",
        "COAL": "lu.f"
    }

    rows = []

    for name, symbol in SYMBOLS.items():
        print(f"🔥 {name}")

        price = None

        try:
            r = requests.get(
                "https://stooq.com/q/l/",
                params={"s": symbol, "f": "sd2t2ohlcv", "e": "csv"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )

            text = r.text

            if "Date" not in text:
                raise Exception("blocked")

            lines = text.splitlines()

            if len(lines) >= 2:
                data = lines[1].split(",")
                if len(data) > 6:
                    val = data[6]
                    if val not in ["", "N/D"]:
                        price = float(val)

        except:
            print("⚠️ fallback fuel")
            fallback = {
                "WTI_OIL": 70,
                "BRENT": 75,
                "NATGAS": 2.5,
                "CO2": 65,
                "COAL": 100
            }
            price = fallback[name]

        rows.append([name, symbol, price, TODAY])

    with open("latest_fuels.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Product", "Symbol", "Price", "Date"])
        writer.writerows(rows)

    return rows


# =============================
# SPARK SPREAD
# =============================
def calculate_spark():

    power = pd.read_csv("latest_settlement.csv")
    fuels = pd.read_csv("latest_fuels.csv")

    power["Settl."] = pd.to_numeric(power.iloc[:, 1], errors="coerce")

    gas = fuels[fuels["Product"] == "NATGAS"]["Price"].iloc[0]

    power["Spark"] = power["Settl."] - gas

    top = power.sort_values("Spark", ascending=False).head(10)

    with open("spark.txt", "w") as f:
        f.write(top.to_string(index=False))


# =============================
# REPORT
# =============================
def generate_report(power, fuels):

    lines = []
    lines.append(f"MARKET REPORT {TODAY}\n\n")

    lines.append("⚡ POWER:\n")
    for r in power[:10]:
        lines.append(f"{r[-2]} → {r[1]}\n")

    lines.append("\n🔥 FUELS:\n")
    for r in fuels:
        lines.append(f"{r[0]}: {r[2]}\n")

    with open("report.txt", "w") as f:
        f.write("".join(lines))


# =============================
# RUN
# =============================
if __name__ == "__main__":

    print("🚀 START")

    try:
        power = scrape_power()
    except Exception as e:
        print(f"⚠️ power fail: {e}")
        power = []

    try:
        fuels = scrape_fuels()
    except Exception as e:
        print(f"⚠️ fuel fail: {e}")
        fuels = []

    try:
        calculate_spark()
    except:
        print("⚠️ spark fail")

    try:
        generate_report(power, fuels)
    except:
        print("⚠️ report fail")

    print("✅ DONE")
