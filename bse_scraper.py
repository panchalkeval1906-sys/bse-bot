import os
import time
import threading
import requests
import datetime
from flask import Flask

app = Flask(__name__)

# Telegram Credentials
TELEGRAM_BOT_TOKEN = "8818481447:AAHTzKl0t2vshflCgr2_lsbVTy6Uhldd6B0"
TELEGRAM_CHAT_ID = "6071666296"

sent_ids = set()

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Telegram Error: {response.text}")
    except Exception as e:
        print(f"Failed to send telegram message: {e}")

def scrape_bse():
    global sent_ids
    print("BSE Scraper background thread started...")
    
    url = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w?strCat=-1&subcategory=-1&strType=C"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bseindia.com/"
    }
    
    # --- INITIALIZATION STEP ---
    # Fetch current filings once on startup so we don't spam old historical messages
    try:
        initial_res = requests.get(url, headers=headers, timeout=15)
        if initial_res.status_code == 200:
            initial_data = initial_res.json().get("Table", [])
            for item in initial_data:
                nid = str(item.get("NEWSID") or item.get("Id") or item.get("DissemDT"))
                if nid:
                    sent_ids.add(nid)
            print(f"Initialized with {len(sent_ids)} existing filings. Now listening for LIVE filings...")
    except Exception as e:
        print(f"Error during initialization: {e}")
    # ---------------------------
    
    while True:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                announcements = data.get("Table", [])
                
                # Check from newest / iterate through items
                for item in announcements:
                    news_id = str(item.get("NEWSID") or item.get("Id") or item.get("DissemDT"))
                    
                    if news_id and news_id not in sent_ids:
                        comp_name = item.get("SLONGNAME", "Unknown Company")
                        headline = item.get("HEADLINE", "No Headline")
                        pdf_url = item.get("ATTACHMENTNAME", "")
                        if pdf_url and not pdf_url.startswith("http"):
                            pdf_url = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{pdf_url}"
                        
                        msg = (
                            f"🚨 *BSE Filing Alert*\n\n"
                            f"🏢 *Company:* {comp_name}\n"
                            f"📌 *Headline:* {headline}\n"
                        )
                        if pdf_url:
                            msg += f"📄 [Download PDF]({pdf_url})"
                        
                        send_telegram_message(msg)
                        sent_ids.add(news_id)
                        
                        if len(sent_ids) > 2000:
                            sent_ids = set(list(sent_ids)[-1000:])
                            
                        time.sleep(1)
            else:
                print(f"BSE API returned status code: {response.status_code}")
                
        except Exception as e:
            print(f"Error in scraper loop: {e}")
            
        time.sleep(60)

@app.route("/")
def home():
    return "BSE Scraper Bot is Running live!"

if __name__ == "__main__":
    t = threading.Thread(target=scrape_bse, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)