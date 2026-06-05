import requests
import csv
from datetime import datetime

TODAY = datetime.utcnow().strftime("%Y-%m-%d")


# =========================
# ✅ SAFE REQUEST
# =========================
def safe_get(url, headers=None):
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r
        else:
            print(f"⚠️ HTTP {r.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ request fail: {e}")
        return None


# =========================
# ⚡ POWER (fallback-safe)
# =========================
def fetch_power():

    SYMBOLS = {
        "ENO_Q": "ENOQ1",
        "SYHEL_Q": "SYHELQ1"
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    rows = []

    for name, symbol in SYMBOLS.items():
        print(f"⚡ {name}")

        price, change, pct = None, None, None

        try:
            url = f"https://api.nasdaq.com/api/quote/{symbol}/historical?limit=2"
            r = safe_get(url, headers)

            if r:
                try:
                    data = r.json()
                except:
                    data = {}

                rows_data = []

                if isinstance(data, dict):
                    if data.get("data") and data["data"].get("tradesTable"):
                        rows_data = data["data"]["tradesTable"].get("rows", [])

                if len(rows_data) >= 2:
                    try:
                        p1 = float(rows_data[0]["close"].replace(",", ""))
                        p2 = float(rows_data[1]["close"].replace(",", ""))

                        price = p1
                        change = p1 - p2
                        pct = (change / p2) * 100
                    except:
                        pass

        except Exception as e:
            print(f"⚠️ power fail {name}: {e}")

        rows.append([name, symbol, price, change, pct, TODAY])

    with open("latest_power.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "symbol", "price", "change", "pct", "date"])
        writer.writerows(rows)

    return rows


# =========================
# 🔥 FUEL (safe)
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

        price, change, pct = None, None, None

        try:
            url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
            r = safe_get(url, headers)

            if r and "Close" in r.text:
                lines = r.text.strip().split("\n")

                if len(lines) >= 3:
                    last = lines[-1].split(",")
                    prev = lines[-2].split(",")

                    price = float(last[4])
                    prev_price = float(prev[4])

                    change = price - prev_price
                    pct = (change / prev_price) * 100

        except Exception as e:
            print(f"⚠️ fuel fail {name}: {e}")

        rows.append([name, symbol, price, change, pct, TODAY])

    with open("latest_fuel.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "symbol", "price", "change", "pct", "date"])
        writer.writerows(rows)

    return rows


# =========================
# 📊 SUMMARY
# =========================
def build_summary(power, fuel):

    rows = power + fuel

    with open("market_summary.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "symbol", "price", "change", "pct", "date"])
        writer.writerows(rows)


# =========================
# 📄 REPORT
# =========================
def build_report(power, fuel):

    def fmt(r):
        if r[2] is None:
            return f"{r[0]}: N/A"
        return f"{r[0]}: {r[2]:.2f} ({r[4] or 0:.2f}%)"

    lines = []
    lines.append(f"📊 MARKET REPORT {TODAY}\n")

    lines.append("⚡ POWER")
    for r in power:
        lines.append(fmt(r))

    lines.append("\n🔥 FUELS")
    for r in fuel:
        lines.append(fmt(r))

    # Insight
    lines.append("\n📈 INSIGHT")

    try:
        co2 = next(x for x in fuel if x[0] == "CO2")[4]
        gas = next(x for x in fuel if x[0] == "GAS")[4]

        if co2:
            lines.append("CO2 trend impacting power markets")

        if gas:
            lines.append("Gas trend influencing electricity prices")

    except:
        lines.append("No clear signal")

    with open("market_report.txt", "w") as f:
        f.write("\n".join(lines))


# =========================
# ▶ MAIN
# =========================
if __name__ == "__main__":

    print("🚀 START")

    try:
        power = fetch_power()
    except:
        power = []

    try:
        fuel = fetch_fuel()
    except:
        fuel = []

    try:
        build_summary(power, fuel)
        build_report(power, fuel)
    except Exception as e:
        print(f"⚠️ report fail: {e}")

    print("✅ DONE")
