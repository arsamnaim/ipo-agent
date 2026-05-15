import requests
import os
from groq import Groq
from bs4 import BeautifulSoup

# ============ YOUR KEYS ============
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
# ===================================

groq_client = Groq(api_key=GROQ_API_KEY)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})
    print("Message sent to Telegram!")

def get_ipo_data():
    url = "https://www.chittorgarh.com/report/ipo-subscription-status-live-data/93/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    ipos = []
    table = soup.find("table")
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 6:
                name = cols[0].get_text(strip=True)
                overall = cols[2].get_text(strip=True)
                qib = cols[3].get_text(strip=True)
                nii = cols[4].get_text(strip=True)
                retail = cols[5].get_text(strip=True)
                ipos.append({
                    "name": name,
                    "subscription": overall,
                    "qib": qib,
                    "nii": nii,
                    "retail": retail,
                    "gmp": "N/A"
                })
    return ipos

def get_gmp():
    url = "https://www.chittorgarh.com/report/ipo-gmp-grey-market-premium/95/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    gmp_data = {}
    table = soup.find("table")
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                name = cols[0].get_text(strip=True)
                gmp = cols[2].get_text(strip=True)
                gmp_data[name] = gmp
    return gmp_data

def analyze_with_groq(ipos):
    if not ipos:
        return "No active IPOs found today."
    ipo_text = ""
    for ipo in ipos:
        ipo_text += f"{ipo['name']}: Overall {ipo['subscription']}x, QIB {ipo['qib']}x, NII {ipo['nii']}x, Retail {ipo['retail']}x, GMP {ipo['gmp']}\n"
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"You are an Indian stock market expert. Analyze these IPOs and give a short recommendation for each (Apply / Avoid / Neutral) with one reason:\n{ipo_text}"}]
    )
    return response.choices[0].message.content

def main():
    print("Fetching IPO data...")
    ipos = get_ipo_data()

    gmp_data = get_gmp()
    for ipo in ipos:
        for key in gmp_data:
            if ipo["name"].lower() in key.lower():
                ipo["gmp"] = gmp_data[key]

    print(f"Found {len(ipos)} IPOs")

    if not ipos:
        send_telegram("📊 <b>IPO Daily Update</b>\n\nNo active IPOs open today.")
        return

    ipo_text = ""
    for ipo in ipos:
        ipo_text += f"""
📌 <b>{ipo['name']}</b>
Overall: {ipo['subscription']}x
├ QIB (Institutions): {ipo['qib']}x
├ NII (HNI): {ipo['nii']}x
└ Retail: {ipo['retail']}x
💰 GMP: {ipo['gmp']}
"""

    analysis = analyze_with_groq(ipos)
    message = f"📊 <b>IPO Daily Update</b>\n{ipo_text}\n🤖 <b>AI Analysis:</b>\n{analysis}"
    send_telegram(message)
    print("Done!")

main()
