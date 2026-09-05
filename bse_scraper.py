import requests
import time

# --- CONFIGURATION (PRE-FILLED) ---
TELEGRAM_BOT_TOKEN = "8818481447:AAHTzKl0t2vshf1Cgr2_1sbvTy6Uh1dd680"
TELEGRAM_CHAT_ID = "6071666296"
CHECK_INTERVAL = 10  # Seconds

# Sirf in keywords waali IMPORTANT filings ke hi alerts aayenge
HIGH_IMPACT_KEYWORDS = [
    "ORDER", "AWARD", "CONTRACT", "MERGER", "ACQUISITION", 
    "BONUS", "SPLIT", "RIGHTS", "WARRANT", "PREFERENTIAL", 
    "FINANCIAL RESULTS", "OUTCOME OF BOARD MEETING", "AGREEMENT",
    "BUYBACK", "COMMISSIONING", "APPROVAL", "JOINT VENTURE", "EBITDA"
]

seen_announcements = set()

def get_fresh_session():
    s = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.bseindia.com/",
        "Origin": "https://www.bseindia.com"
    }
    s.headers.update(headers)
    try:
        s.get("https://www.bseindia.com/", timeout=5)
    except Exception:
        pass
    return s

session = get_fresh_session()

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram Error: {e}")

def fetch_bse_announcements():
    global session
    url = "https://api.bseindia.com/BseIndiaAPI/api/AnnList/w?pageno=1&strCat=-1&strPrevDate=&strScrip=&strSearch=P&strToDate=&strType=C"
    try:
        response = session.get(url, timeout=10, allow_redirects=False)
        
        if response.status_code in (301, 302):
            session = get_fresh_session()
            response = session.get(url, timeout=10, allow_redirects=False)

        if response.status_code == 200:
            data = response.json()
            return data.get("Table", [])
    except Exception as e:
        print(f"Connection reset, refreshing session...")
        session = get_fresh_session()
    return []

def process_announcement(item):
    news_id = item.get("NEWSID")
    if not news_id or news_id in seen_announcements:
        return

    seen_announcements.add(news_id)

    headline = item.get("NEWSSUB", "")
    
    # Filter: Skip normal announcements, process ONLY High-Impact ones
    is_high_impact = any(kw in headline.upper() for kw in HIGH_IMPACT_KEYWORDS)
    if not is_high_impact:
        return

    company_name = item.get("SLONGNAME", "N/A")
    scrip_code = item.get("SCRIP_CD", "N/A")
    category = item.get("CATEGORYNAME", "General")
    pdf_name = item.get("ATTACHMENTNAME", "")
    pdf_link = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{pdf_name}" if pdf_name else "N/A"

    # Message format with short news + optional PDF Link
    msg = (
        f"🔥 *IMPORTANT BSE NEWS*\n\n"
        f"🏢 *Company:* {company_name} ({scrip_code})\n"
        f"📂 *Category:* {category}\n"
        f"📢 *News:* {headline}\n\n"
        f"🔗 [View PDF Document]({pdf_link})"
    )

    send_telegram_message(msg)

def run_scraper():
    print("🚀 BSE High-Impact News + PDF Link Scraper Started!\n")
    send_telegram_message("🚀 *BSE Alerts Active (Important News + PDF Links)*")
    
    while True:
        announcements = fetch_bse_announcements()
        for item in reversed(announcements):
            process_announcement(item)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_scraper()