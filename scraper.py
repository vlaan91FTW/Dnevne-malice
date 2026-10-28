import json
import os
import requests
import time
from bs4 import BeautifulSoup
from google import genai

# Setup
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
client = genai.Client(api_key=GEMINI_KEY)

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
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        return " ".join(soup.stripped_strings)[:3000]
    except:
        return "Ni mogoče naložiti strani."

def main():
    print(f"=== ZAGON BATCH ROBOTA ===")
    
    # 1. Zberi vsebino vseh strani
    all_data_context = []
    for r in RESTAURANTS_CONFIG:
        print(f"Berem: {r['name']}...")
        text = fetch_page_text(r['url'])
        all_data_context.append({"id": r["id"], "name": r["name"], "content": text})

    # 2. Pošlji en sam skupni prompt
    prompt = f"""
    Si kulinarični asistent. Izlušči DANAŠNJE menije za vse naštete restavracije iz spodnjih podatkov.
    Za vsako restavracijo vrni JSON objekt s poljem 'id' in 'menu'.
    Vrni izključno JSON seznam objektov v tem formatu:
    [
      {{"id": 1, "menu": [ {{"main": "Ime jedi", "detail": "priloga", "price": "cena", "tags": ["mesno"]}} ]}},
      ...
    ]
    Če menija ne najdeš, vrni: "menu": [{{"main": "Meni za danes še ni objavljen", "detail": "Preverite kasneje", "price": "", "tags": []}}]
    
    Podatki restavracij: {json.dumps(all_data_context)}
    """

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        raw_json = response.text.strip().replace("```json", "").replace("```", "")
        extracted_menus = json.loads(raw_json)
        
        # Mapiraj rezultate
        menu_lookup = {item['id']: item['menu'] for item in extracted_menus}
        
        results = []
        for r in RESTAURANTS_CONFIG:
            r_data = dict(r)
            r_data['menu'] = menu_lookup.get(r['id'], [{"main": "Napaka pri branju", "detail": "", "price": "", "tags": []}])
            results.append(r_data)
            
        with open("menus.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("=== KONČANO: menus.json posodobljen! ===")

    except Exception as e:
        print(f"Kritična napaka pri AI obdelavi: {e}")

if __name__ == "__main__":
    main()
