import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# Initialize client with API key from environment
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

now = datetime.now()
days_sl = ["Ponedeljek", "Torek", "Sreda", "Četrtek", "Petek", "Sobota", "Nedelja"]
today_name = days_sl[now.weekday()]
today_str = f"{today_name}, {now.strftime('%d. %m. %Y')}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

RESTAURANTS_CONFIG = [
    {"id": 1, "name": "Restavracija Magma X", "url": "https://magma-x.com/restavracija-magma-x/", "has_image_flyer": False},
    {"id": 2, "name": "Gostilna pri Hrastu", "url": "https://prihrastu.si/dnevna-kosila", "has_image_flyer": False},
    {"id": 3, "name": "Gostilna in picerija Zvezda", "url": "https://www.gostilna-zvezda.si/", "has_image_flyer": False},
    {"id": 4, "name": "Restavracija Eda", "url": "https://edarestavracija.si/kosila-malice", "has_image_flyer": False},
    {"id": 5, "name": "Restavracija Špar", "url": "https://www.spar.si/restavracija-interspar/tedenski-meni", "has_image_flyer": True},
    {"id": 6, "name": "Restavracija Sabotin", "url": "https://hotelsabotin.com/posebne-ponudbe/malice-in-kosila-sa/", "has_image_flyer": False},
    {"id": 7, "name": "Restavracija Vrtnica", "url": "https://www.restavracija-vrtnica.si/", "has_image_flyer": False},
    {"id": 8, "name": "Restavracija Gurman", "url": "https://restavracija-gurman.si/sl#meals-section", "has_image_flyer": False}
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
        prompt = f"""
        Si pomočnik za slovenske kulinarične jedilnike. Restavracija: '{restaurant_name}'. Danes je: {today_str}.
        Izlušči jedilnik za DANAŠNJI DAN ({today_name}) in teden.
        Vrni čist JSON:
        {{
          "menu": [ {{"main": "Ime", "detail": "Opis", "price": "Cena", "tags": ["mesno"]}} ],
          "weeklyMenu": {{ "1": [], "2": [], "3": [], "4": [], "5": [] }}
        }}
        Besedilo: {text}
        """
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
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
        r_data["menu"] = parsed.get("menu", []) if parsed else []
        if not r_data["menu"]:
            r_data["menu"] = [{"main": "Meni še ni na voljo", "detail": "Prosimo poskusite kasneje.", "price": "", "tags": []}]
        results.append(r_data)
    with open("menus.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
