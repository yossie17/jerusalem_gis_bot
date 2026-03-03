import os
import requests
import logging
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. הגדרת לוגים להדפסה ב-Railway Console
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
        # הפרדת רחוב ממספר בית (מניח שהמספר הוא המילה האחרונה)
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
        
        # ביצוע הבקשה עם טיימאאוט של 15 שניות
        # verify=False נדרש כי לפעמים תעודת ה-SSL של העירייה לא מזוהה בעננים
        response = requests.get(url, params=params, timeout=15, verify=False)
        
        duration = time.time() - start_time
        logger.info(f"⏱️ GIS Response received in {duration:.2f} seconds (Status: {response.status_code})")
        
        data = response.json()
        features = data.get('features', [])