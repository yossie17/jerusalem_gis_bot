import os
import requests
import logging
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. הגדרת לוגים
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. פונקציית פנייה ל-GIS
def get_building_info(address_text):
    start_time = time.time()
    logger.info(f"🛰️ GIS Request Start: {address_text}")
    
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
        
        response = requests.get(url, params=params, timeout=15, verify=False)
        duration = time.time() - start_time
        logger.info(f"⏱️ GIS Response in {duration:.2f}s (Status: {response.status_code})")
        
        data = response.json()
        features = data.get('features', [])
        
        if features:
            logger.info(f"✅ נמצאו נתונים")
            return features[0]['attributes']
        
        logger.warning(f"❓ לא נמצאו תוצאות")
        return None

    except Exception as e:
        logger.error(f"❌ שגיאה ב-GIS: {e}")
        return None

# 3. טיפול בהודעות
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    logger.info(f"📩 הודעה: {user_text}")
    
    sent_msg = await update.message.reply_text("🔍 בודק בנתוני העירייה...")
    res = get_building_info(user_text)
    
    if res:
        reply = (f"✅ **נמצאו נתונים!**\n\n"
                 f"🏠 **כתובת:** {res.get('StreetName1')} {res.get('BldNum')}\n"
                 f"🏢 **קומות:** {res.get('NUM_FLOORS', 0)}\n"
                 f"🔢 **דירות:** {res.get('NUM_APTS_C', 0)}\n"
                 f"🛍️ **עסקים:** {res.get('NUM_BUSNS_', 0)}")
    else:
        reply = f"❌ לא מצאתי מידע על '{user_text}'."
    
    await sent_msg.edit_text(reply, parse_mode='Markdown')

# 4. הרצה
if __name__ == "__main__":
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    
    if not TOKEN:
        logger.error("❌ חסר TELEGRAM_TOKEN ב-Railway Variables!")
    else:
        logger.info("🚀 הבוט עולה...")
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.run_polling()