import os
import cloudscraper
from flask import Flask

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID')

sent_ids = set()


def send_telegram_message(message):
  url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
  payload = {
      'chat_id': TELEGRAM_CHAT_ID,
      'text': message,
      'parse_mode': 'Markdown',
  }
  try:
    scraper = cloudscraper.create_scraper()
    scraper.post(url, json=payload, timeout=10)
  except Exception as e:
    print(f'Error sending Telegram message: {e}')


def check_bse_filings():
  api_url = 'https://api.bseindia.com/BSEIndiaAPI/api/AnnSubCategoryGetData?strCat=-1&strPrevDate=&strScrip=&strSearch=P&strToDate=&strType=C'

  try:
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True,
        }
    )

    response = scraper.get(api_url, timeout=15)

    # Yahan hum status code aur response ka thoda sa hissa print karenge
    if response.status_code != 200:
      return (
          f'BSE Error! Status Code: {response.status_code} | Text:'
          f' {response.text[:200]}',
          200,
      )

    if not response.text or len(response.text) < 10:
      return 'BSE returned empty response.', 200

    if not response.text.strip().startswith(
        '{'
    ) and not response.text.strip().startswith('['):
      return (
          f'Cloudflare/BSE Blocked! Response snippet:'
          f' {response.text[:300].strip()}',
          200,
      )

    try:
      data = response.json()
    except Exception as json_err:
      return (
          f'Failed to parse JSON: {str(json_err)} | Response:'
          f' {response.text[:150]}',
          500,
      )

    announcements = data.get('Table', [])

    global sent_ids
    if not sent_ids:
      for item in announcements:
        filing_id = str(
            item.get('NEWSID') or item.get('ROW_ID') or item.get('Id')
        )
        if filing_id:
          sent_ids.add(filing_id)
      return (
          'BSE Bot Initialized Successfully! Historical filings cached.',
          200,
      )

    new_filings_count = 0
    for item in announcements:
      filing_id = str(
          item.get('NEWSID') or item.get('ROW_ID') or item.get('Id')
      )
      if not filing_id:
        continue

      if filing_id not in sent_ids:
        sent_ids.add(filing_id)
        new_filings_count += 1

        heading = item.get('HEADLINE', 'No Headline')
        scrip_name = item.get('SLONGNAME', 'Unknown Company')
        dt = item.get('NEWS_DT', '')

        msg = (
            f'🚨 *New BSE Filing Alert!*\n\n*Company:* {scrip_name}\n*Headline:*'
            f' {heading}\n*Time:* {dt}'
        )
        send_telegram_message(msg)

    return (
        f'Checked successfully. New filings found sent: {new_filings_count}',
        200,
    )

  except Exception as e:
      return f'Error occurred: {str(e)}', 500


@app.route('/check-bse')
def webhook_check():
  result, status_code = check_bse_filings()
  return result, status_code


if __name__ == '__main__':
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)