import requests
import csv
from datetime import datetime

TODAY = datetime.utcnow().strftime("%Y-%m-%d")

# =========================
# ⚡ POWER (Nasdaq)
# =========================
def fetch_power():

    SYMBOLS = {
        "ENO_Q": "ENOQ1",
        "SYHEL_Q": "SYHELQ1"
    }

    rows = []

    for name, symbol in SYMBOLS.items():
        print(f"⚡ {name}")

        try:
            url = f"https://api.nasdaq.com/api/quote/{symbol}/historical?limit=2"

            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }

            r = requests.get(url, headers=headers, timeout=10)
           data = r.json()

            rows_data = []
            if data.get("data") and data["data"].get("tradesTable"):
                rows_data = data["data"]["tradesTable"].get("rows", [])


            if len(rows_data) >= 2:
                today_price = float(rows_data[0]["close"].replace(",", ""))
                prev_price = float(rows_data[1]["close"].replace(",", ""))

                change = today_price - prev_price
                pct = (change / prev_price) * 100
            else:
                today_price, change, pct = None, None, None

        except Exception as e:
            print(f"⚠️ power fail {name}: {e}")
            today_price, change, pct = None, None, None

        rows.append([name, symbol, today_price, change, pct, TODAY])

    with open("latest_power.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "symbol", "price", "change", "pct", "date"])
        writer.writerows(rows)

    return rows


# =========================
# 🔥 FUEL
# =========================
def fetch_fuel():

    SYMBOLS = {
        "WTI": "cl.f",
        "BRENT": "cb.f",
        "GAS": "tg.f",
        "CO2": "ev.f",
        "COAL": "lu.f"
    }

    headers = {"User-Agent": "Mozilla/5.0"}
    rows = []

    for name, symbol in SYMBOLS.items():
        print(f"🔥 {name}")

        try:
            url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
            r = requests.get(url, headers=headers, timeout=10)

            if "Close" not in r.text:
                raise Exception("Blocked")

            lines = r.text.strip().split("\n")

            if len(lines) >= 3:
                last = lines[-1].split(",")
                prev = lines[-2].split(",")

                price = float(last[4])
                prev_price = float(prev[4])

                change = price - prev_price
                pct = (change / prev_price) * 100
            else:
                price, change, pct = None, None, None

        except:
            price, change, pct = None, None, None

        rows.append([name, symbol, price, change, pct, TODAY])

    with open("latest_fuel.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "symbol", "price", "change", "pct", "date"])
        writer.writerows(rows)

    return rows


# =========================
# 📊 YHDISTETTY DATA
# =========================
def build_summary(power, fuel):

    rows = []

    for r in power + fuel:
        rows.append(r)

    with open("market_summary.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "symbol", "price", "change", "pct", "date"])
        writer.writerows(rows)


# =========================
# 📄 REPORT GENERATOR
# =========================
def build_report(power, fuel):

    def fmt(row):
        if row[2] is None:
            return f"{row[0]}: N/A"
        return f"{row[0]}: {row[2]:.2f} ({row[4]:+.2f}%)"

    lines = []
    lines.append(f"📊 MARKET REPORT {TODAY}\n")

    lines.append("⚡ POWER")
    for r in power:
        lines.append(fmt(r))

    lines.append("\n🔥 FUELS")
    for r in fuel:
        lines.append(fmt(r))

    # 🔥 Smart insight
    lines.append("\n📈 INSIGHT")

    try:
        co2 = next(x for x in fuel if x[0] == "CO2")[4]
        gas = next(x for x in fuel if x[0] == "GAS")[4]

        if co2 and gas:
            if co2 > 0:
                lines.append("CO2 rising → bullish power")
            if gas > 0:
                lines.append("Gas rising → pushing power prices up")
    except:
        pass

    with open("market_report.txt", "w") as f:
        f.write("\n".join(lines))


# =========================
# ▶ RUN
# =========================
if __name__ == "__main__":

    power = fetch_power()
    fuel = fetch_fuel()

    build_summary(power, fuel)
    build_report(power, fuel)

    print("✅ DONE")
