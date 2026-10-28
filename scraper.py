import json
import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime

# Setup
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
genai.configure(api_key=GEMINI_KEY)

now = datetime.now()
days_sl = ["Ponedeljek", "Torek", "Sreda", "Četrtek", "Petek", "Sobota", "Nedelja"]
today_name = days_sl[now.weekday()]
today_str = f"{today_name}, {now.strftime('%d. %m. %Y')}"

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

def fetch_page_text(url):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        return " ".join(soup.stripped_strings)[:3000]
    except:
        return "Ni mogoče naložiti strani."

def main():
    print(f"=== ZAGON OPTIMIZIRANEGA BATCH ROBOTA ({today_str}) ===")
    
    # 1. Zberi vsebino vseh strani
    all_data_context = ""
    for r in RESTAURANTS_CONFIG:
        print(f"Berem: {r['name']}...")
        page_text = fetch_page_text(r['url'])
        all_data_context += f"\n--- RESTAVRACIJA: {r['name']} (ID: {r['id']}) ---\n{page_text}\n"

    # 2. Pošlji en sam skupni prompt
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    Si kulinarični asistent. Danes je {today_str}.
    Iz spodnjih besedil izlušči DANAŠNJE menije za vse restavracije.
    
    Vrni izključno JSON seznam objektov v tem formatu:
    [
      {{
        "id": 1,
        "menu": [ {{"main": "Ime jedi", "detail": "priloga", "price": "cena", "tags": ["mesno"]}} ]
      }},
      ...
    ]
    
    Če za katero restavracijo ne najdeš menija za danes, za to restavracijo vrni:
    "menu": [{{"main": "Meni za danes še ni objavljen", "detail": "Preverite kasneje", "price": "", "tags": []}}]

    Besedila strani:
    {all_data_context}
    """

    results = []
    try:
        response = model.generate_content(prompt)
        raw_json = response.text.strip().replace("```json", "").replace("```", "")
        extracted_menus = json.loads(raw_json)
        
        # Mapiraj rezultate nazaj na konfiguracijo
        menu_lookup = {item['id']: item['menu'] for item in extracted_menus}
        
        for r in RESTAURANTS_CONFIG:
            r_data = dict(r)
            r_data['menu'] = menu_lookup.get(r['id'], [{"main": "Napaka pri branju", "detail": "", "price": "", "tags": []}])
            results.append(r_data)
            
    except Exception as e:
        print(f"Kritična napaka pri AI obdelavi: {e}")
        # V primeru napake vrni prazne menije
        for r in RESTAURANTS_CONFIG:
            r_data = dict(r)
            r_data['menu'] = [{"main": "Meni trenutno ni na voljo", "detail": "Google kvota presežena ali napaka.", "price": "", "tags": []}]
            results.append(r_data)

    # 3. Shrani
    with open("menus.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("=== KONČANO: menus.json posodobljen z enim klicem! ===")

if __name__ == "__main__":
    main()
