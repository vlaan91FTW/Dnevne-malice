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

def scrape_magma_x_menu():
    try:
        resp = requests.get(RESTAURANTS_CONFIG[0]["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        container = soup.find("div", class_="wpr-price-list")
        items = []
        if container:
            for item in container.find_all("div", class_="wpr-price-list-item"):
                title_el = item.find("span", class_="wpr-price-list-title")
                price_el = item.find("span", class_="wpr-price-list-price")
                desc_el = item.find("div", class_="wpr-price-list-description")
                main = title_el.get_text(strip=True) if title_el else ""
                if not main:
                    continue
                items.append({
                    "main": main,
                    "detail": desc_el.get_text(strip=True) if desc_el else "",
                    "price": price_el.get_text(strip=True) if price_el else "",
                    "tags": []
                })
        return items
    except Exception as e:
        print(f"Napaka pri dejanskem branju Restavracije Magma X: {e}")
        return None

def scrape_prijhrastu_menu(dan_name):
    try:
        resp = requests.get(RESTAURANTS_CONFIG[1]["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("div.views-row")
        wanted = dan_name.lower()
        selected_row = None
        for row in rows:
            time_el = row.select_one("div.views-field-field-dan time")
            if not time_el:
                continue
            day_label = time_el.get_text(strip=True)
            day_name = day_label.split(",")[0].strip().lower()
            if day_name == wanted or (wanted == "petek" and day_name == "petek"):
                selected_row = row
                break
        if not selected_row:
            print(f"Za dan '{dan_name}' ni bilo na voljo vseh stvari... (Gostilna pri Hrastu)")
            return None
        items = []
        meals = selected_row.select("div.paragraph.paragraph--type--obrok")
        if not meals:
            meals = selected_row.select("div.field--name-field-ime-obroka")
        for meal in meals:
            course_el = meal.select_one("div.field--name-field-ime-obroka")
            course = course_el.get_text(strip=True) if course_el else "Jedlo"
            detail_parts = []
            desc_el = meal.select_one("div.field--name-field-podnudba")
            if desc_el:
                for p in desc_el.select("p"):
                    t = p.get_text(strip=True)
                    if t:
                        detail_parts.append(t)
            main = course.strip()
            detail = " / ".join(detail_parts) if detail_parts else ""
            items.append({
                "main": main,
                "detail": detail,
                "price": "",
                "tags": []
            })
        return items
    except Exception as e:
        print(f"Napaka pri dejanskem branju Gostilne pri Hrastu: {e}")
        return None

DETERMINISTIC_SCRAPERS = {
    1: scrape_magma_x_menu,
    2: scrape_prijhrastu_menu,
}

def get_deterministic_menu(r, dan_name):
    scraper_fn = DETERMINISTIC_SCRAPERS.get(r["id"])
    if scraper_fn is None:
        return None
    return scraper_fn(dan_name)

def main():
    print(f"=== ZAGON BATCH ROBOTA ({datetime.now().strftime('%d.%m.%Y')}) ===")

    now = datetime.now()
    dan = "petek"
    if now.weekday() < 5:  # ponedeljek(0) - petek(4)
        dan = ["ponedeljek", "torek", "sreda", "četrtek", "petek"][now.weekday()]
    else:
        dan = "petek"  # sobota/nedelja -> petek

    all_data_context = []
    deterministic_menus = {}
    for r in RESTAURANTS_CONFIG:
        print(f"Berem: {r['name']}...")
        menu_items = get_deterministic_menu(r, dan)
        if menu_items:
            deterministic_menus[r["id"]] = menu_items
            all_data_context.append({"id": r["id"], "name": r["name"], "content": json.dumps(menu_items, ensure_ascii=False)})
            continue
        text = fetch_page_text(r['url'])
        all_data_context.append({"id": r["id"], "name": r["name"], "content": text})

    # Če so vsi restauraciji rešene deterministično, skipamo AI celo
    if len(deterministic_menus) == len(RESTAURANTS_CONFIG):
        results = []
        for r in RESTAURANTS_CONFIG:
            r_data = dict(r)
            r_data['menu'] = deterministic_menus[r["id"]]
            results.append(r_data)
        with open("menus.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("=== KONČANO: menus.json posodobljen! (deterministično, brez AI) ===")
        return

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
                    if r["id"] in deterministic_menus:
                        r_data['menu'] = deterministic_menus[r["id"]]
                    else:
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
        # Na koncu naprej zapnimo lokalni fallback, da stran ostane delovala
        fallback_results = []
        for r in RESTAURANTS_CONFIG:
            fallback_results.append({
                "id": r["id"],
                "name": r["name"],
                "url": r["url"],
                "menu": [
                    {
                        "main": "Meni trenutno ni na voljo",
                        "detail": "Preverite kasneje",
                        "price": "",
                        "tags": []
                    }
                ]
            })
        with open("menus.json", "w", encoding="utf-8") as f:
            json.dump(fallback_results, f, ensure_ascii=False, indent=2)
        print("=== ZAUSADEK: menus.json posodobljen z lokalnim fallback-om ===")

if __name__ == "__main__":
    main()
