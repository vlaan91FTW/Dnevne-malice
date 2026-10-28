import json
import os
import requests
import time
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
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        return " ".join(soup.stripped_strings)[:5000]
    except:
        return "Ni mogoče naložiti strani."

def get_menu_with_retry(restaurant_name, text, retries=3):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Si kulinarični asistent. Restavracija: '{restaurant_name}'. Izlušči dnevni meni: {text}. Vrni JSON: {{'menu': [{{'main': '...', 'detail': '...', 'price': '...'}}]}}"
    
    for i in range(retries):
        try:
            response = model.generate_content(prompt)
            return json.loads(response.text.replace("```json", "").replace("```", ""))
        except Exception as e:
            print(f"Poskus {i+1} neuspešen za {restaurant_name}: {e}")
            time.sleep(30) # Počakaj 30s pred ponovnim poskusom
    return {"menu": [{"main": "Meni trenutno ni na voljo", "detail": "Preverite kasneje", "price": ""}]}

def main():
    results = []
    for r in RESTAURANTS_CONFIG:
        print(f"Obdelujem: {r['name']}...")
        text = fetch_page_text(r["url"])
        data = get_menu_with_retry(r["name"], text)
        r.update(data)
        results.append(r)
        time.sleep(10) # Varnostna pavza med restavracijami
        
    with open("menus.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("=== KONČANO ===")

if __name__ == "__main__":
    main()
