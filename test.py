import os
import requests
import ssl
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest # <--- הוספנו את זה

# 1. ביטול SSL גלובלי (למקרה שזה יעזור)
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

os.environ['no_proxy'] = '*'

# --- פונקציית ה-GIS ---
def get_building_info(address_text):
    try:
        parts = address_text.rsplit(' ', 1)
        street, number = parts[0], parts[1] if len(parts) > 1 else ""
        url = "https://gisviewer.jerusalem.muni.il/arcgis/rest/services/BaseLayers/MapServer/10/query"
        params = {
            'where': f"StreetName1 LIKE '%{street}%' AND BldNum LIKE '{number}%'",
            'outFields': 'StreetName1,BldNum,NUM_FLOORS,NUM_APTS_C,NUM_BUSNS_',
            'f': 'json', 'returnGeometry': 'false'
        }
        # כאן verify=False עוקף את ה-SSL מול העירייה
        response = requests.get(url, params=params, timeout=10, verify=False)
        return response.json().get('features', [{}])[0].get('attributes')
    except: return None

# --- לוגיקת הבוט ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    sent_msg = await update.message.reply_text(f"🔍 בודק עבור: {user_text}...")
    res = get_building_info(user_text)
    if res:
        reply = (f"🏠 **כתובת:** {res.get('StreetName1')} {res.get('BldNum')}\n"
                 f"🏢 **קומות:** {res.get('NUM_FLOORS', 0)}\n"
                 f"🔢 **דירות:** {res.get('NUM_APTS_C', 0)}\n"
                 f"🛍️ **עסקים:** {res.get('NUM_BUSNS_', 0)}")
    else:
        reply = "❌ לא נמצא בניין."
    await sent_msg.edit_text(reply, parse_mode='Markdown')

# --- הרצה עם ביטול SSL מפורש ב-HTTPX ---
if __name__ == "__main__":
    TOKEN = "8765279442:AAHnabskYsxwLgtsR5JMfqx8GjpeC93HrnI"
    
    print("🚀 מתניע בוט במצב 'עקיפת SSL'...")

    # כאן אנחנו יוצרים בקשה מיוחדת שאומרת ל-HTTPX: "אל תבדוק SSL"
    proxy_request = HTTPXRequest(connect_timeout=15, read_timeout=15)
    # אנחנו נגדיר ל-Client של ה-Request לא לבדוק אימות
    # (הערה: בגרסאות מסוימות זה נעשה דרך ה-Builder)
    
    app = ApplicationBuilder().token(TOKEN).request(proxy_request).build()
    
    # פתרון קסם אחרון: הזרקת SSL Context מבוטל לתוך הבוט
    app.bot._request._client._transport._pool._ssl_context = ssl._create_unverified_context()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("✅ הבוט רץ! (אם עדיין יש שגיאה, ה-Firewall חוסם את הכתובת פיזית)")
    app.run_polling()