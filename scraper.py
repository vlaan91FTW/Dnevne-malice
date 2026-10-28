import json
import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# Setup
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
genai.configure(api_key=GEMINI_KEY)

RESTAURANTS_CONFIG = [
    {"id": 1, "name": "Restavracija Magma X", "url": "https://magma-x.com/restavracija-magma-x/"},
    {"id": 2, "name": "Gostilna pri Hrastu", "url": "https://prihrastu.si/dnevna-kosila"},
    {"id": 3, "name": "Gostilna in picerija Zvezda", "url": "https://www.gostilna-zvezda.si/"},
    {"id": 4, "name": "Restavracija Eda", "url": "https://edarestavracija.si/kosila-malice"},
    {"id": 5, "name": "Restavracija Špar", "url": "https://www.spar.si/restavracija-interspar/tedenski-meni"},
    {"id": 6, "name": "Restavracija Sabotin", "url": "https://hotelsabotin.com/posebne-ponudbe/malice-in-kosila-sa/"},
    {"id": 7, "name": "Restavracija Vrtnica", "url": "https://www.restavracija-vrtnica.si/"}
]

def fetch_page_text(url):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=20)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return " ".join(soup.stripped_strings)[:5000]
    except:
        return ""

def get_menu(restaurant_name, text):
    # Uporaba modela, ki ga zahteva API
    model = genai.GenerativeModel("gemini-3.8-flash")
    prompt = f"Si kulinarični asistent. Restavracija: '{restaurant_name}'. Izlušči dnevni meni iz tega besedila: {text}. Vrni strogo JSON: {{'menu': [{{'main': '...', 'detail': '...', 'price': '...'}}]}}"
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.replace("```json", "").replace("```", ""))
    except Exception as e:
        print(f"Error for {restaurant_name}: {e}")
        return {"menu": [{"main": "Meni še ni na voljo", "detail": "Poskusite kasneje", "price": ""}]}

def main():
    results = []
    for r in RESTAURANTS_CONFIG:
        print(f"Berem: {r['name']}...")
        text = fetch_page_text(r["url"])
        data = get_menu(r["name"], text)
        r.update(data)
        results.append(r)
    with open("menus.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
