import os
import requests
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. הגדרת לוגים - זה יודפס ב-Railway Console
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_building_info(address_text):
    logger.info(f"🛰️ פונה ל-GIS עבור הכתובת: {address_text}")
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
        
        # הוספת טיימאאוט ברור כדי שלא יתקע לנצח
        response = requests.get(url, params=params, timeout=15, verify=False)
        logger.info(f"📥 התקבלה תגובה מה-GIS (סטטוס: {response.status_code})")
        
        data = response.json()
        features = data.get('features', [])
        
        if features:
            logger.info("✅ נמצאו נתונים ב-GIS")
            return features[0]['attributes']
        
        logger.warning("❓ לא נמצאו תוצאות ב-GIS לכתובת זו")
        return None
    except Exception as e:
        logger.error(f"❌ שגיאה בפנייה ל-GIS: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_name = update.message.from_user.first_name
    
    logger.info(f"📩 הודעה חדשה מ-{user_name}: {user_text}")
    
    sent_msg = await update.message.reply_text("🔍 בודק בנתוני העירייה, רק רגע...")
    
    res = get_building_info(user_text)
    
    if res:
        reply = (f"🏠 **כתובת:** {res.get('StreetName1')} {res.get('BldNum')}\n"
                 f"🏢 **מספר קומות:** {res.get('NUM_FLOORS', 0)}\n"
                 f"🔢 **מספר דירות:** {res.get('NUM_APTS_C', 0)}\n"
                 f"🛍️ **מספר עסקים:** {res.get('NUM_BUSNS_', 0)}")
    else:
        reply = "❌ מצטער, לא מצאתי מידע על הבניין הזה ב-GIS."
    
    await sent_msg.edit_text(reply, parse_mode='Markdown')
    logger.info(f"📤 תשובה נשלחה למשתמש {user_name}")

if __name__ == "__main__":
    TOKEN = os.environ.get("TELEGRAM_TOKEN", "8765279442:AAHnabskYsxwLgtsR5JMfqx8GjpeC93HrnI")
    
    logger.info("🚀 הבוט מתחיל לעבוד...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    app.run_polling()