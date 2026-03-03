import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# פונקציית ה-GIS
def get_building_info(address_text):
    try:
        parts = address_text.rsplit(' ', 1)
        street = parts[0]
        number = parts[1] if len(parts) > 1 else ""
        
        url = "https://gisviewer.jerusalem.muni.il/arcgis/rest/services/BaseLayers/MapServer/10/query"
        params = {
            'where': f"StreetName1 LIKE '%{street}%' AND BldNum LIKE '{number}%'",
            'outFields': 'StreetName1,BldNum,NUM_FLOORS,NUM_APTS_C,NUM_BUSNS_',
            'f': 'json', 
            'returnGeometry': 'false'
        }
        # verify=False רק כי ה-GIS של העירייה לפעמים עושה בעיות, לא טלגרם
        response = requests.get(url, params=params, timeout=10, verify=False)
        data = response.json()
        features = data.get('features', [])
        return features[0]['attributes'] if features else None
    except Exception as e:
        print(f"GIS Error: {e}")
        return None

# לוגיקת הבוט
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    res = get_building_info(user_text)
    
    if res:
        reply = (f"🏠 **כתובת:** {res.get('StreetName1')} {res.get('BldNum')}\n"
                 f"🏢 **מספר קומות:** {res.get('NUM_FLOORS', 0)}\n"
                 f"🔢 **מספר דירות:** {res.get('NUM_APTS_C', 0)}\n"
                 f"🛍️ **מספר עסקים:** {res.get('NUM_BUSNS_', 0)}")
    else:
        reply = "❌ לא מצאתי בניין בכתובת הזו."
    
    await update.message.reply_text(reply, parse_mode='Markdown')

if __name__ == "__main__":
    # נשתמש במשתנה סביבה עבור הטוקן (יותר בטוח ב-Render)
    TOKEN = os.environ.get("TELEGRAM_TOKEN", "8765279442:AAHnabskYsxwLgtsR5JMfqx8GjpeC93HrnI")
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🚀 הבוט עולה לאוויר ב-Render...")
    app.run_polling()