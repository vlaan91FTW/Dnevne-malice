import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

now = datetime.now()
days_sl = ["Ponedeljek", "Torek", "Sreda", "Četrtek", "Petek", "Sobota", "Nedelja"]
today_name = days_sl[now.weekday()]
today_str = f"{today_name}, {now.strftime('%d. %m. %Y')}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

RESTAURANTS_CONFIG = [
    {
        "id": 1,
        "name": "Restavracija Magma X",
        "aliases": "magmax magma-x restavracija magma kromberk",
        "url": "https://magma-x.com/restavracija-magma-x/",
        "mapsUrl": "https://maps.google.com/?q=Restavracija+Magma+X+Nova+Gorica",
        "phone": "+386 8 200 48 20",
        "cuisine": "Pizzerija & Žar",
        "hours": "11:00 - 15:00",
        "address": "Industrijska cesta 11, Kromberk",
        "bannerImage": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=700&q=80",
        "nearCenter": True,
        "has_image_flyer": False
    },
    {
        "id": 2,
        "name": "Gostilna pri Hrastu (Restavracija Hrast)",
        "aliases": "pri hrastu hrast restavracija hrast kromberk",
        "url": "https://prihrastu.si/dnevna-kosila",
        "mapsUrl": "https://maps.google.com/?q=Gostilna+pri+Hrastu+Nova+Gorica",
        "phone": "+386 5 302 72 10",
        "cuisine": "Gourmet & Tradicionalna",
        "hours": "11:00 - 22:00",
        "address": "Kromberška cesta 2, Nova Gorica",
        "bannerImage": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=700&q=80",
        "nearCenter": True,
        "has_image_flyer": False
    },
    {
        "id": 3,
        "name": "Gostilna in picerija Zvezda",
        "aliases": "zvezda solkan pizzerija zvezda",
        "url": "https://www.gostilna-zvezda.si/",
        "mapsUrl": "https://maps.google.com/?q=Gostilna+Zvezda+Solkan",
        "phone": "+386 5 996 53 97",
        "cuisine": "Mediteranska & Pizzerija",
        "hours": "10:30 - 15:00",
        "address": "Cesta IX. korpusa 65, Solkan",
        "bannerImage": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=700&q=80",
        "nearCenter": False,
        "has_image_flyer": False
    },
    {
        "id": 4,
        "name": "Restavracija Eda",
        "aliases": "eda center eda restavracija",
        "url": "https://edarestavracija.si/kosila-malice",
        "mapsUrl": "https://maps.google.com/?q=Eda+Center+Nova+Gorica",
        "phone": "+386 51 352 492",
        "cuisine": "Sodobna & Hitra kosila",
        "hours": "10:00 - 14:00",
        "address": "Delpinova ulica 18b (Eda Center)",
        "bannerImage": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=700&q=80",
        "nearCenter": True,
        "has_image_flyer": False
    },
    {
        "id": 5,
        "name": "Restavracija Špar",
        "aliases": "spar špar restavracija spar restavracija špar interspar supernova qlandia",
        "url": "https://www.spar.si/restavracija-interspar/tedenski-meni",
        "mapsUrl": "https://maps.google.com/?q=Supernova+Interspar+Nova+Gorica",
        "phone": "+386 5 330 84 00",
        "cuisine": "Samopostrežna & Kosila",
        "hours": "10:30 - 15:30",
        "address": "Supernova Qlandia, Nova Gorica",
        "bannerImage": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=700&q=80",
        "nearCenter": True,
        "has_image_flyer": True
    },
    {
        "id": 6,
        "name": "Restavracija Sabotin",
        "aliases": "sabotin hotel solkan hit",
        "url": "https://hotelsabotin.com/posebne-ponudbe/malice-in-kosila-sa/",
        "mapsUrl": "https://maps.google.com/?q=Hotel+Sabotin+Solkan",
        "phone": "+386 5 336 50 00",
        "cuisine": "Tradicionalna gostilna",
        "hours": "10:00 - 15:00",
        "address": "Cesta IX. korpusa 35, Solkan",
        "bannerImage": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=700&q=80",
        "nearCenter": False,
        "has_image_flyer": False
    },
    {
        "id": 7,
        "name": "Restavracija Vrtnica",
        "aliases": "vrtnica nova gorica restavracija vrtnica",
        "url": "https://www.restavracija-vrtnica.si/",
        "mapsUrl": "https://maps.google.com/?q=Restavracija+Vrtnica+Nova+Gorica",
        "phone": "+386 5 330 08 20",
        "cuisine": "Domača kosila & Enolončnice",
        "hours": "10:00 - 15:00",
        "address": "Kidričeva ulica 11, Nova Gorica",
        "bannerImage": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=700&q=80",
        "nearCenter": True,
        "has_image_flyer": False
    },
    {
        "id": 8,
        "name": "Restavracija Gurman",
        "aliases": "gurman catering zar pleskavica restavracija gurman",
        "url": "https://restavracija-gurman.si/sl#meals-section",
        "mapsUrl": "https://maps.google.com/?q=Restavracija+Gurman+Nova+Gorica",
        "phone": "+386 5 30 21 941",
        "cuisine": "Balkanski žar & Domača",
        "hours": "10:00 - 16:00",
        "address": "Ulica Gradnikove brigade 51",
        "bannerImage": "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd?auto=format&fit=crop&w=700&q=80",
        "nearCenter": True,
        "has_image_flyer": False
    }
]

def fetch_page_content(url, look_for_image=False):
    """Prenese spletno stran, poišče morebitne slike jedilnikov ter čisto besedilo."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.encoding = resp.apparent_encoding
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Če stran uporablja sliko (kot Špar)
            image_data = None
            if look_for_image:
                for img in soup.find_all("img"):
                    src = img.get("src", "")
                    if re.search(r"jedilnik|meni|malic|kosil", src, re.I):
                        if not src.startswith("http"):
                            src = requests.compat.urljoin(url, src)
                        try:
                            img_resp = requests.get(src, headers=HEADERS, timeout=10)
                            if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                                image_data = img_resp.content
                                break
                        except Exception:
                            pass

            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()
            text = " ".join(soup.stripped_strings)
            return text[:6000], image_data
    except Exception as e:
        print(f"Napaka pri prenosu {url}: {e}")
    return "", None

def extract_with_gemini(restaurant_name, text, image_bytes=None):
    """Z Gemini AI izlušči jedi v enoten JSON format za cel teden."""
    if not GEMINI_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
Si pomočnik za slovenske kulinarične jedilnike.
Restavracija: '{restaurant_name}'.
Danes je: {today_str}.

Tvoja naloga je, da iz podanega gradiva (besedila ali slike plakata) izluščiš jedilnik za DANAŠNJI DAN ({today_name}) 
181: in po možnosti za ostale dni v tednu (1=Ponedeljek, 2=Torek, 3=Sreda, 4=Četrtek, 5=Petek).

Vrni izključno čist JSON (brez besedila ali markdown oznak ```json) v naslednji strukturi:
{{
  "menu": [
    {{
      "main": "Ime glavne jedi",
      "detail": "priloga, solata, juha ali opis",
      "price": "npr. 8,50 €",
      "tags": ["mesno"]
    }}
  ],
  "weeklyMenu": {{
    "1": [ {{ "main": "...", "detail": "...", "price": "...", "tags": ["mesno"] }} ],
    "2": [ ... ],
    "3": [ ... ],
    "4": [ ... ],
    "5": [ ... ],
    "6": [ ... ]
  }}
}}

Pravila:
- Dovoljeni tagi: "mesno", "vegi", "riba", "zlica", "solata".
- Polje "menu" naj vsebuje točno današnje jedi.
- Polje "weeklyMenu" naj vsebuje celotni teden, če je na strani objavljen celoten tedenski meni.
- Če za določen dan ni podatkov, pusti prazen seznam [].

Gradivo (besedilo):
{text}
"""
        parts = [prompt]
        if image_bytes:
            parts.append({"mime_type": "image/jpeg", "data": image_bytes})

        response = model.generate_content(parts)
        raw = response.text.strip()
        raw = re.sub(r"^```(?:json)?", "", raw)
        raw = re.sub(r"```$", "", raw).strip()
        parsed = json.loads(raw)
        return parsed
    except Exception as e:
        print(f"Gemini napaka pri {restaurant_name}: {e}")
    return None

def main():
    print(f"=== ZAGON AVTOMATSKEGA BRALNIKA ({today_str}) ===")
    results = []

    for r in RESTAURANTS_CONFIG:
        print(f"-> Berem: {r['name']}...")
        text, img_bytes = fetch_page_content(r["url"], look_for_image=r.get("has_image_flyer", False))
        
        parsed = None
        if (text or img_bytes) and GEMINI_KEY:
            parsed = extract_with_gemini(r["name"], text, img_bytes)

        r_data = dict(r)
        
        if parsed and isinstance(parsed, dict):
            r_data["menu"] = parsed.get("menu", [])
            r_data["weeklyMenu"] = parsed.get("weeklyMenu", {})
        else:
            r_data["menu"] = []
            r_data["weeklyMenu"] = {}

        # Če za danes ni bilo najdenih jedi, dodamo prijazno obvestilo
        if not r_data["menu"] or len(r_data["menu"]) == 0:
            r_data["menu"] = [
                {
                    "main": "Meni za danes še ni objavljen na spletni strani",
                    "detail": "Restavracija menije običajno posodobi med 10.00 in 11.00 uro. Kliknite spodaj za ogled uradne strani.",
                    "price": "",
                    "tags": ["mesno"]
                }
            ]

        results.append(r_data)

    with open("menus.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("=== USPEŠNO USTVARJEN IN SHRANJEN menus.json ===")

if __name__ == "__main__":
    main()
