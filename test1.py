import requests
import json
import os

# ביטול פרוקסי
os.environ['no_proxy'] = '*'

def get_jerusalem_building_info(street_name, house_num):
    # כתובת ה-Query של שכבת המבנים/כתובות בירושלים
    url = "https://gisviewer.jerusalem.muni.il/arcgis/rest/services/BaseLayers/MapServer/10/query"
    
    # שאילתת SQL פשוטה שמתאימה ל-ArcGIS
    # אנחנו מחפשים שדה שנקרא Street_Name או דומה לו
    # הערה: אם זה לא מוצא, ננסה שמות שדות אחרים
    where_clause = f"Street_Name LIKE '%{street_name}%' AND House_Number = {house_num}"
    
    params = {
        'f': 'json',
        'where': '1=1', # נתחיל מחיפוש כללי כדי לראות אם יש תגובה
        'text': f"{street_name} {house_num}", # חיפוש טקסט חופשי ב-ArcGIS
        'outFields': '*',
        'returnGeometry': 'false',
        'spatialRel': 'esriSpatialRelIntersects'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://gisviewer.jerusalem.muni.il/'
    }

    print(f"🔍 שולח שאילתה ל-ArcGIS...")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if 'features' in data and len(data['features']) > 0:
                print("✅ הצלחה! נמצא מידע:")
                # מדפיס את התוצאה הראשונה שמצאנו
                attrs = data['features'][0]['attributes']
                print(json.dumps(attrs, indent=2, ensure_ascii=False))
                return attrs
            else:
                print("⚠️ לא נמצאו תוצאות בפורמט הזה. מנסה גרסה פשוטה יותר...")
                # אם לא מצא, ננסה רק עם ה-Text
                params['where'] = f"1=1"
                response = requests.get(url, params=params, headers=headers)
                print(response.json())
        else:
            print(f"❌ שגיאה בשרת ArcGIS: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ שגיאה: {e}")

if __name__ == "__main__":
    get_jerusalem_building_info("יפו", 212)
