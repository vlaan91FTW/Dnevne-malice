import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# Initialize client with API key from environment
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
genai.configure(api_key=GEMINI_KEY)

now = datetime.now()
days_sl = ["Ponedeljek", "Torek", "Sreda", "Četrtek", "Petek", "Sobota", "Nedelja"]
today_name = days_sl[now.weekday()]
today_str = f"{today_name}, {now.strftime('%d. %m. %Y')}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

RESTAURANTS_CONFIG = [
    {"id": 1, "name": "Restavracija Magma X", "url": "https://magma-x.com/restavracija-magma-x/"},
    {"id": 2, "name": "Gostilna pri Hrastu", "url": "https://prihrastu.si/dnevna-kosila"},
    {"id": 3, "name": "Gostilna in picerija Zvezda", "url": "https://www.gostilna-zvezda.si/"},
    {"id": 4, "name": "Restavracija Eda", "url": "https://edarestavracija.si/kosila-malice"},
    {"id": 5, "name": "Restavracija Špar", "url": "https://www.spar.si/restavracija-interspar/tedenski-meni"},
    {"id": 6, "name": "Restavracija Sabotin", "url": "https://hotelsabotin.com/posebne-ponudbe/malice-in-kosila-sa/"},
    {"id": 7, "name": "Restavracija Vrtnica", "url": "https://www.restavracija-vrtnica.si/"},
    {"id": 8, "name": "Restavracija Gurman", "url": "https://restavracija-gurman.si/sl#meals-section"}
]

def fetch_page_content(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.encoding = resp.apparent_encoding
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()
            return " ".join(soup.stripped_strings)[:6000]
    except Exception as e:
        print(f"Napaka pri prenosu {url}: {e}")
    return ""

def extract_with_gemini(restaurant_name, text):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        Si pomočnik za slovenske kulinarične jedilnike. Restavracija: '{restaurant_name}'. Danes je: {today_str}.
        Izlušči jedilnik za DANAŠNJI DAN ({today_name}).
        Vrni samo veljaven, čist JSON (brez besedila, brez oznak):
        {{
          "menu": [ {{"main": "Ime jedi", "detail": "priloga", "price": "cena", "tags": ["mesno"]}} ]
        }}
        Besedilo: {text}
        """
        response = model.generate_content(prompt)
        raw = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(raw)
    except Exception as e:
        print(f"Gemini napaka pri {restaurant_name}: {e}")
    return None

def main():
    results = []
    for r in RESTAURANTS_CONFIG:
        text = fetch_page_content(r["url"])
        parsed = extract_with_gemini(r["name"], text)
        
        r_data = dict(r)
        if parsed and "menu" in parsed:
            r_data["menu"] = parsed["menu"]
        else:
            r_data["menu"] = [{"main": "Meni še ni na voljo", "detail": "Prosimo poskusite kasneje.", "price": "", "tags": []}]
        results.append(r_data)
        
    with open("menus.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
