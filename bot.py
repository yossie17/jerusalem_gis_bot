import os
import requests
import logging
import time
# מניעת התראות SSL בלוגים (בגלל verify=False)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# 1. הגדרת לוגים - לצפייה ב-Railway Console
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. פונקציית פנייה ל-GIS של עיריית ירושלים
def get_building_info(address_text):
    start_time = time.time()
    logger.info(f"🛰️ GIS Request Start: {address_text}")
    
    try:
        # ניתוח הכתובת - רחוב ומספר
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
        
        # הוספת Headers כדי לעקוף חסימת 403 (התחזות לדפדפן)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://gisviewer.jerusalem.muni.il/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15, verify=False)
        duration = time.time() - start_time
        
        logger.info(f"⏱️ GIS Response in {duration:.2f}s (Status: {response.status_code})")
        
        if response.status_code != 200:
            logger.error(f"❌ שגיאת שרת: {response.status_code}")
            return None

        data = response.json()
        features = data.get('features', [])
        
        if features:
            logger.info(f"✅ נמצאו נתונים ב-GIS")
            return features[0]['attributes']
        
        logger.warning(f"❓ לא נמצאו תוצאות לכתובת: {address_text}")
        return None

    except Exception as e:
        logger.error(f"❌ שגיאה בעיבוד הבקשה: {e}")
        return None

# 3. טיפול בפקודת /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("👋 פקודת /start התקבלה")
    await update.message.reply_text(
        "שלום! אני בוט ה-GIS של ירושלים. 🏛️\n"
        "שלחו לי שם רחוב ומספר (למשל: יפו 212) ואשלוף לכם נתונים על המבנה."
    )

# 4. טיפול בהודעות טקסט (חיפוש כתובת)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    logger.info(f"📩 הודעה חדשה: {user_text}")
    
    # הודעת "בדיקה" כדי שהמשתמש לא יחשוב שהבוט תקוע
    sent_msg = await update.message.reply_text("🔍 בודק בנתוני העירייה, רק רגע...")
    
    res = get_building_info(user_text)
    
    if res:
        reply = (f"🏠 **פרטי המבנה:**\n\n"
                 f"📍 **כתובת:** {res.get('StreetName1')} {res.get('BldNum')}\n"
                 f"🏢 **מספר קומות:** {res.get('NUM_FLOORS', 0)}\n"
                 f"🔢 **מספר דירות:** {res.get('NUM_APTS_C', 0)}\n"
                 f"🛍️ **מספר עסקים:** {res.get('NUM_BUSNS_', 0)}")
    else:
        reply = f"❌ מצטער, לא מצאתי נתונים עבור '{user_text}'. וודאו שהכתובת נכונה (למשל: יפו 212)."
    
    await sent_msg.edit_text(reply, parse_mode='Markdown')

# 5. הרצת האפליקציה
if __name__ == "__main__":
    # משיכת הטוקן ממשתני הסביבה של Railway
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    
    if not TOKEN:
        logger.error("❌ חסר TELEGRAM_TOKEN ב-Variables!")
    else:
        logger.info("🚀 הבוט מתניע ב-Railway...")
        app = ApplicationBuilder().token(TOKEN).build()
        
        # הוספת מטפלים (Handlers)
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        # התחלת האזנה להודעות
        app.run_polling()