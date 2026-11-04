import json
import os
import re
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

def scrape_magma_x_menu(dan_name=None):
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
            course_el = meal.select_one("div.field--name-field-ime-obroka div.field__item")
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

def scrape_zvezda_menu(dan_name):
    try:
        resp = requests.get(RESTAURANTS_CONFIG[2]["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        now = datetime.now()
        today_date_str = f"{now.day}.{now.month:02d}.{now.year}"
        menu_views = soup.select("div.menuView")
        selected_menu_view = None
        for mv in menu_views:
            container = mv.parent
            dt = container.find("div", class_="dateTime") if container.name == "div" else None
            if not dt:
                continue
            h3 = dt.find("h3")
            if not h3:
                continue
            heading = h3.get_text(" ", strip=True)
            found_today = False
            for d in re.findall(r"\d{1,2}\.\d{1,2}\.\d{4}", heading):
                parts = d.split(".")
                if len(parts) == 3:
                    dd, mm, yyyy = int(parts[0]), int(parts[1]), int(parts[2])
                    if (dd, mm, yyyy) == (now.day, now.month, now.year):
                        found_today = True
            if found_today or today_date_str in heading:
                selected_menu_view = mv
                break
        if not selected_menu_view:
            return None
        menu_view = selected_menu_view
        items = []
        for menu_item in menu_view.select("div.menuItem"):
            title_el = menu_item.select_one("h4")
            title = title_el.get_text(strip=True) if title_el else "Jedlo"
            main = ""
            detail = ""
            price = ""
            main_el = menu_item.select_one("p.menuDesc")
            if main_el:
                main = main_el.get_text(strip=True)
            boxes = menu_item.select("div.bottomItem > div.desertOrPrice")
            for box in boxes:
                p_el = box.find("p")
                if not p_el:
                    continue
                txt = p_el.get_text(strip=True)
                cls = p_el.get("class") or []
                if "priceTag" in cls:
                    price = txt.replace("€", "").replace(",", ".").strip()
                elif not detail:
                    detail = txt
            if not main and not detail:
                continue
            items.append({
                "main": main,
                "detail": detail,
                "price": price,
                "tags": []
            })
        return items
    except Exception as e:
        print(f"Napaka pri dejanskem branju Gostilne in picerije Zvezde: {e}")
        return None

def scrape_eda_menu(dan_name):
    try:
        resp = requests.get(RESTAURANTS_CONFIG[3]["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        slides = soup.select("div.swiper-slide")
        now = datetime.now()
        selected_slide = None
        for slide in slides:
            time_el = slide.select_one("time.datetime")
            if not time_el:
                continue
            label = time_el.get_text(strip=True)
            m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", label)
            if not m:
                continue
            if (int(m.group(1)), int(m.group(2)), int(m.group(3))) == (now.day, now.month, now.year):
                selected_slide = slide
                break
        if not selected_slide:
            return None
        items = []
        content = selected_slide.select_one("div.views-field-field-ponudba")
        if not content:
            return None
        for p in content.select("p"):
            strong_els = p.find_all("strong")
            em_els = p.find_all("em")
            price_str = ""
            name = ""
            diet = ""
            for s in strong_els:
                txt = s.get_text(strip=True)
                pm = re.search(r"([\d.,]+)\s*€", txt)
                if pm:
                    price_str = pm.group(0).strip()
                    clean = re.sub(r"[\d.,]+\s*€", "", txt).strip()
                    if not name and clean:
                        name = clean
                elif not name:
                    name = txt.strip()
                else:
                    diet = txt.strip()
            desc = ""
            if em_els:
                desc = em_els[-1].get_text(strip=True)
            if not name and price_str:
                full = p.get_text(" ", strip=True)
                full = re.sub(r"[\d.,]+\s*€", "", full).strip(" .-")
                name = full
            if not name:
                continue
            items.append({
                "main": name,
                "detail": desc,
                "price": price_str.replace(",", ".").strip() if price_str else "",
                "tags": []
            })
        return items
    except Exception as e:
        print(f"Napaka pri dejanskem branju Restavracije Ede: {e}")
        return None

def scrape_spar_menu(dan_name):
    try:
        resp = requests.get(RESTAURANTS_CONFIG[4]["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        for li in soup.find_all("li"):
            txt = li.get_text(" ", strip=True)
            pm = re.match(r"^(.*),\s+([\d.,]+)\s*€", txt)
            if pm:
                items.append({
                    "main": pm.group(1).strip(),
                    "detail": "",
                    "price": pm.group(2) + " €",
                    "tags": []
                })
        return items
    except Exception as e:
        print(f"Napaka pri dejanskem branju Restavracije Špar: {e}")
        return None

def scrape_sabotin_menu(dan_name):
    try:
        resp = requests.get(RESTAURANTS_CONFIG[5]["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        if not table:
            return None
        rows = table.find_all("tr")
        now = datetime.now()
        weekdays = ["ponedeljek", "torek", "sreda", "četrtek", "petek", "sobota", "nedelja"]
        wanted = weekdays[now.weekday()] if now.weekday() < 5 else "petek"
        selected_row = None
        for row in rows:
            cells = row.find_all("td")
            if not cells:
                continue
            first = cells[0].get_text(" ", strip=True)
            first_lower = first.lower()
            if first_lower.startswith(wanted + ",") and f"{wanted}, {now.day}" in first_lower:
                selected_row = row
                break
        if not selected_row:
            return None
        cells = selected_row.find_all("td")
        items = []
        meal_columns = ["Kosilo", "Malica", "Vege malica"]
        for i, meal_name in enumerate(meal_columns, start=1):
            if i >= len(cells):
                break
            cell = cells[i]
            raw_text = cell.get_text("\n", strip=True)
            lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
            if not lines:
                continue
            items.append({
                "main": lines[0],
                "detail": ", ".join(lines[1:]) if len(lines) > 1 else "",
                "price": "",
                "tags": []
            })
        return items
    except Exception as e:
        print(f"Napaka pri dejanskem branju Restavracije Sabotina: {e}")
        return None

def scrape_vrtnica_menu(dan_name):
    try:
        resp = requests.get(RESTAURANTS_CONFIG[6]["url"], headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        now = datetime.now()
        weekdays = ["ponedeljek", "torek", "sreda", "četrtek", "petek", "sobota", "nedelja"]
        today_weekday = weekdays[now.weekday()]
        selected_menu = None
        for group in soup.select("div.owl-carousel > div"):
            dt = group.find("div", class_="dateTime")
            if not dt:
                continue
            day_text = " ".join(s.get_text(" ", strip=True) for s in dt.find_all("span"))
            tokens = re.split(r"[\s,]+", day_text.strip().rstrip("."))
            wd_token = tokens[0].lower() if tokens else ""
            group_weekday = today_weekday if wd_token == "danes" else wd_token
            if group_weekday != dan_name:
                continue
            menu_block = group.find("div", class_="daillyMenu")
            if menu_block is None:
                continue
            selected_menu = menu_block
            break
        if selected_menu is None:
            return None
        sections = selected_menu.find_all("div")
        daily_section = None
        for sec in sections:
            h2 = sec.find("h2")
            if h2 and "Dnevni menu" in h2.get_text(" ", strip=True):
                daily_section = sec
                break
        if daily_section is None and sections:
            daily_section = sections[0]
        if daily_section is None:
            return None
        items = []
        for li in daily_section.find_all("li"):
            name = ""
            detail = ""
            price = ""
            price_found = False
            for span in li.find_all("span"):
                txt = span.get_text(" ", strip=True)
                pm = re.search(r"([\d.,]+)\s*€", txt)
                if pm:
                    price = pm.group(1) + " €"
                    price_found = True
                    continue
                if not name and txt:
                    name = txt
                elif txt and not detail:
                    detail = txt
            if not name or not price_found:
                continue
            items.append({
                "main": name.strip(),
                "detail": detail.strip(),
                "price": price,
                "tags": []
            })
        return items
    except Exception as e:
        print(f"Napaka pri dejanskem branju Restavracije Vrtnice: {e}")
        return None

DETERMINISTIC_SCRAPERS = {
    1: scrape_magma_x_menu,
    2: scrape_prijhrastu_menu,
    3: scrape_zvezda_menu,
    4: scrape_eda_menu,
    5: scrape_spar_menu,
    6: scrape_sabotin_menu,
    7: scrape_vrtnica_menu,
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
        # (a zapisujemo le za tiste, ki nimanje deterministic ni zabilo)
        fallback_results = []
        for r in RESTAURANTS_CONFIG:
            fallback_results.append({
                "id": r["id"],
                "name": r["name"],
                "url": r["url"],
                "menu": deterministic_menus.get(r["id"], [
                    {
                        "main": "Ker podatki trenutno niso na voljo, meni še ni naložen. Prosimo, poskusite kasneje",
                        "detail": "",
                        "price": "",
                        "tags": []
                    }
                ])
            })
        with open("menus.json", "w", encoding="utf-8") as f:
            json.dump(fallback_results, f, ensure_ascii=False, indent=2)
        print("=== ZAUSADEK: menus.json posodobljen z lokalnim fallback-om ===")

if __name__ == "__main__":
    main()
