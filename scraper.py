import json
import os
import time
import requests
from bs4 import BeautifulSoup
from google import genai
from datetime import datetime

# Setup - Uporaba novega google-genai SDK
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

RESTAURANTS_CONFIG = [
    {"id": 1, "name": "Restavracija Magma X", "url": "https://magma-x.com/restavracija-magma-x/"},
    {"id": 2, "name": "Gostilna pri Hrastu", "url": "https://prihrastu.si/dnevna-kosila"},
    {"id": 3, "name": "Gostilna in picerija Zvezda", "url": "https://www.gostilna-zvezda.si/"},
    {"id": 4, "name": "Restavracija Eda", "url": "https://edarestavracija.si/kosila-malice"},
    {"id": 5, "name": "Restavracija Špar", "url": "https://pojedina.com/r/nova-gorica-interspar/"},
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
    print(f"=== ZAGON BATCH ROBOTA ({datetime.now().strftime('%d.%m.%Y')}) ===")
    
    all_data_context = []
    for r in RESTAURANTS_CONFIG:
        print(f"Berem: {r['name']}...")
        text = fetch_page_text(r['url'])
        all_data_context.append({"id": r["id"], "name": r["name"], "content": text})

    now = datetime.now()
    dan = "petek"
    if now.weekday() < 5:  # ponedeljek(0) - petek(4)
        dan = ["ponedeljek", "torek", "sreda", "četrtek", "petek"][now.weekday()]
    else:
        dan = "petek"  # sobota/nedelja -> petek

    prompt = f"""
    Si kulinarični asistent. Izlušči MENI za dan {dan} za vse naštete restavracije iz spodnjih podatkov. Vsako restavracijo orientiraj le na dan '{dan}' (objavljeni tedenski meniji veljajo za ta dan).
    Vrni izključno JSON seznam objektov v formatu:
    [
      {{"id": 1, "menu": [ {{"main": "Ime jedi", "detail": "priloga", "price": "cena", "tags": ["mesno"]}} ]}},
      ...
    ]
    Če menija ne najdeš za ta dan, vrni: "menu": [{{"main": "Meni za dan {dan} ni objavljen", "detail": "Preverite kasneje", "price": "", "tags": []}}]
    
    Podatki: {json.dumps(all_data_context)}
    """

    max_retries = 5
    retry_delay = 15
    success = False
    last_error = None
    last_model = None

    for model_name in ["gemini-3.8-flash", "gemini-flash-latest"]:
        if success:
            break
        for attempt in range(max_retries):
            try:
                print(f"Poskušam z AI obdelavo ({model_name}) (poskus {attempt + 1}/{max_retries})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                raw_json = response.text.strip().replace("```json", "").replace("```", "")
                extracted_menus = json.loads(raw_json)
                
                menu_lookup = {item['id']: item['menu'] for item in extracted_menus}
                
                results = []
                for r in RESTAURANTS_CONFIG:
                    r_data = dict(r)
                    r_data['menu'] = menu_lookup.get(r['id'], [{"main": "Napaka pri branju", "detail": "", "price": "", "tags": []}])
                    results.append(r_data)
                
                with open("menus.json", "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print("=== KONČANO: menus.json posodobljen! ===")
                success = True
                break
                
            except Exception as e:
                error_str = str(e)
                last_error = error_str
                last_model = model_name
                print(f"Napaka pri AI obdelavi ({model_name}) (poskus {attempt + 1}): {error_str}")
                retryable = any(k in error_str for k in ["503", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "429", "overloaded", "high demand", "disconnected", "timeout", "deadline"])
                if retryable and attempt < max_retries - 1:
                    delay = retry_delay
                    retry_delay = min(retry_delay * 2, 120)
                    print(f"PREOBREMENJENI ZAHTEV (retryable). Čakam {delay} sekund pred ponovnim poskusom...")
                    time.sleep(delay)
                else:
                    break
        
    if not success:
        print(f"=== NAPAKA: AI obdelava ni uspela. Zadnja napaka: {last_error} (model: {last_model}) ===")

if __name__ == "__main__":
    main()
