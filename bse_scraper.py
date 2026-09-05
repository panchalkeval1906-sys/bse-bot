import requests
import time
from datetime import datetime
from flask import Flask
import threading
import os

# Aapke asli Telegram Credentials yahan set hain
TELEGRAM_BOT_TOKEN = "7730999031:AAHV-F8x2M_u3F4x5Qz6v_7W8x9y0z1A2B"
TELEGRAM_CHAT_ID = "6071666296"

app = Flask(__name__)

@app.route('/')
def home():
    return "BSE Scraper Bot is active 24/7!"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Failed to send telegram message: {response.text}")
    except Exception as e:
        print(f"Error sending telegram message: {e}")

def fetch_bse_announcements():
    url = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?pageno=1&strCat=-1&strPrevDate=&strScrip=&strSearch=P&strType=C&subcategory=-1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bseindia.com/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("Table", [])
    except Exception as e:
        print(f"Error fetching BSE announcements: {e}")
    return []

def process_announcement(item):
    company_name = item.get("SLONGNAME", "N/A")
    scrip_code = item.get("SCRIP_CD", "N/A")
    headline = item.get("HEADLINE", "N/A")
    category = item.get("Categoryname", "N/A")
    pdf_attachment = item.get("ATTACHMENTNAME", "")
    
    pdf_link = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{pdf_attachment}" if pdf_attachment else "https://www.bseindia.com"

    msg = (
        f"🔥 *IMPORTANT BSE NEWS*\n\n"
        f"🏢 *Company:* {company_name} ({scrip_code})\n"
        f"📁 *Category:* {category}\n"
        f"📰 *News:* {headline}\n\n"
        f"🔗 [View PDF Document]({pdf_link})"
    )
    send_telegram_message(msg)

def run_scraper():
    print("🚀 BSE High-Impact News + PDF Link Scraper Started!\n")
    send_telegram_message("🚀 *BSE Alerts Active (Important News + PDF Links)*")
    
    # Track processed IDs so duplicate messages aren't sent
    seen_ids = set()
    
    # Pehli baar fetch karke purane IDs store kar lete hain taaki purani news ka spam na aaye
    initial_announcements = fetch_bse_announcements()
    for item in initial_announcements:
        news_id = item.get("NEWSID")
        if news_id:
            seen_ids.add(news_id)

    while True:
        try:
            announcements = fetch_bse_announcements()
            for item in reversed(announcements):
                news_id = item.get("NEWSID")
                if news_id and news_id not in seen_ids:
                    seen_ids.add(news_id)
                    process_announcement(item)
                    # Memory limit control for seen_ids
                    if len(seen_ids) > 1000:
                        seen_ids.pop()
        except Exception as e:
            print(f"Loop error: {e}")
            
        time.sleep(60)  # Har 60 seconds mein check karega

if __name__ == "__main__":
    # Scraper ko background thread mein start karo
    scraper_thread = threading.Thread(target=run_scraper)
    scraper_thread.daemon = True
    scraper_thread.start()
    
    # Render ke liye Flask web server bind karo (PORT environment variable ke sath)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)