import requests
import csv
from datetime import datetime

TODAY = datetime.utcnow().strftime("%Y-%m-%d")


# =========================
# SAFE REQUEST
# =========================
def fetch_yahoo(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}

        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()

        result = data.get("quoteResponse", {}).get("result", [])

        if not result:
            return None, None, None

        d = result[0]

        price = d.get("regularMarketPrice")
        change = d.get("regularMarketChange")
        pct = d.get("regularMarketChangePercent")

        return price, change, pct

    except Exception as e:
        print(f"⚠️ {symbol} fail: {e}")
        return None, None, None


# =========================
# ENERGY DATA
# =========================
def fetch_energy():

    SYMBOLS = {
        "BRENT": "BZ=F",
        "WTI": "CL=F",
        "GAS_TTF": "NG=F",
        "CO2": "KRBN",
        "POWER_PROXY": "PXE"
    }

    rows = []

    for name, symbol in SYMBOLS.items():
        print(f"🔎 {name}")

        price, change, pct = fetch_yahoo(symbol)

        rows.append([name, symbol, price, change, pct, TODAY])

    with open("energy_market.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "symbol", "price", "change", "pct", "date"])
        writer.writerows(rows)

    return rows


# =========================
# ANALYSIS
# =========================
def build_report(rows):

    lines = []
    lines.append(f"📊 ENERGY MARKET REPORT {TODAY}\n")

    fuels = {}
    power = None

    for r in rows:
        name, _, price, change, pct, _ = r

        if price is None:
            lines.append(f"{name}: N/A")
        else:
            lines.append(f"{name}: {price:.2f} ({pct:.2f}%)")

        fuels[name] = pct

        if name == "POWER_PROXY":
            power = pct

    # =========================
    # SMART INSIGHT
    # =========================
    lines.append("\n📈 MARKET INSIGHT")

    try:
        gas = fuels.get("GAS_TTF")
        co2 = fuels.get("CO2")

        if gas is not None and co2 is not None:

            if gas > 0 and co2 > 0:
                lines.append("🔥 Bullish power: gas & CO2 rising")

            elif gas < 0 and co2 < 0:
                lines.append("⚡ Bearish power: fuel costs falling")

            else:
                lines.append("⚖️ Mixed fuel signals")

    except:
        lines.append("No clear signal")

    # =========================
    # TREND SUMMARY
    # =========================
    lines.append("\n📊 TREND VIEW")

    for name, pct in fuels.items():
        if pct is None:
            continue

        if pct > 1:
            trend = "⬆ strong up"
        elif pct > 0:
            trend = "↗ up"
        elif pct < -1:
            trend = "⬇ strong down"
        elif pct < 0:
            trend = "↘ down"
        else:
            trend = "→ flat"

        lines.append(f"{name}: {trend}")

    with open("market_report.txt", "w") as f:
        f.write("\n".join(lines))


# =========================
# MAIN
# =========================
if __name__ == "__main__":

    print("🚀 ENERGY JOB START")

    try:
        data = fetch_energy()
    except:
        data = []

    try:
        build_report(data)
    except Exception as e:
        print(f"⚠️ report fail: {e}")

    print("✅ DONE")
