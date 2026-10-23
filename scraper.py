import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Preveri ali je na voljo brezplačni Gemini API ključ
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
        "url": "https://magma-x.com/restavracija-magma-x/",
        "mapsUrl": "https://maps.google.com/?q=Restavracija+Magma+X+Nova+Gorica",
        "phone": "+386 8 200 48 20",
        "cuisine": "Pizzerija & Žar",
        "hours": "11:00 - 15:00",
        "address": "Industrijska cesta 11, Kromberk",
        "bannerImage": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=700&q=80",
        "nearCenter": False
    },
    {
        "id": 2,
        "name": "Gostilna pri Hrastu",
        "url": "https://prihrastu.si/dnevna-kosila",
        "mapsUrl": "https://maps.google.com/?q=Gostilna+pri+Hrastu+Nova+Gorica",
        "phone": "+386 5 302 72 10",
        "cuisine": "Gourmet & Tradicionalna",
        "hours": "11:00 - 22:00",
        "address": "Kromberška cesta 2, Nova Gorica",
        "bannerImage": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=700&q=80",
        "nearCenter": True
    },
    {
        "id": 3,
        "name": "Restavracija Eda",
        "url": "https://edarestavracija.si/kosila-malice",
        "mapsUrl": "https://maps.google.com/?q=Eda+Center+Nova+Gorica",
        "phone": "+386 51 352 492",
        "cuisine": "Sodobna & Hitra kosila",
        "hours": "10:00 - 14:00",
        "address": "Delpinova ulica 18b (Eda Center)",
        "bannerImage": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=700&q=80",
        "nearCenter": True
    },
    {
        "id": 4,
        "name": "Restavracija Interspar",
        "url": "https://www.spar.si/restavracija-interspar/tedenski-meni",
        "mapsUrl": "https://maps.google.com/?q=Supernova+Interspar+Nova+Gorica",
        "phone": "+386 5 330 84 00",
        "cuisine": "Samopostrežna & Kosila",
        "hours": "10:30 - 15:30",
        "address": "Supernova Qlandia, Nova Gorica",
        "bannerImage": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=700&q=80",
        "nearCenter": True
    },
    {
        "id": 5,
        "name": "Restavracija Sabotin",
        "url": "https://hotelsabotin.com/posebne-ponudbe/malice-in-kosila-sa/",
        "mapsUrl": "https://maps.google.com/?q=Hotel+Sabotin+Solkan",
        "phone": "+386 5 336 50 00",
        "cuisine": "Tradicionalna gostilna",
        "hours": "10:00 - 15:00",
        "address": "Cesta IX. korpusa 35, Solkan",
        "bannerImage": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=700&q=80",
        "nearCenter": False
    },
    {
        "id": 6,
        "name": "Gostilna Zvezda",
        "url": "https://www.gostilna-zvezda.si/",
        "mapsUrl": "https://maps.google.com/?q=Gostilna+Zvezda+Solkan",
        "phone": "+386 5 300 58 40",
        "cuisine": "Mediteranska & Pizzerija",
        "hours": "10:30 - 15:00",
        "address": "Cesta IX. korpusa 65, Solkan",
        "bannerImage": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=700&q=80",
        "nearCenter": False
    },
    {
        "id": 7,
        "name": "Restavracija Vrtnica",
        "url": "https://www.restavracija-vrtnica.si/",
        "mapsUrl": "https://maps.google.com/?q=Restavracija+Vrtnica+Nova+Gorica",
        "phone": "+386 5 330 08 20",
        "cuisine": "Domača kosila & Enolončnice",
        "hours": "10:00 - 15:00",
        "address": "Kidričeva ulica 11, Nova Gorica",
        "bannerImage": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=700&q=80",
        "nearCenter": True
    },
    {
        "id": 8,
        "name": "Restavracija Gurman",
        "url": "https://restavracija-gurman.si/sl#meals-section",
        "mapsUrl": "https://maps.google.com/?q=Restavracija+Gurman+Nova+Gorica",
        "phone": "+386 5 30 21 941",
        "cuisine": "Balkanski žar & Domača",
        "hours": "10:00 - 16:00",
        "address": "Ulica Gradnikove brigade 51",
        "bannerImage": "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd?auto=format&fit=crop&w=700&q=80",
        "nearCenter": True
    }
]

def fetch_page_text(url):
    """Prenese spletno stran in vrne zgolj čisto besedilo."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.encoding = resp.apparent_encoding
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()
            text = " ".join(soup.stripped_strings)
            return text[:4500]  # Vzemi prvih 4500 znakov
    except Exception as e:
        print(f"Napaka pri prenosu {url}: {e}")
    return ""

def ask_gemini_to_extract(restaurant_name, text):
    """Pošlje besedilo strani Gemini modelu, da izlušči današnje jedi."""
    if not GEMINI_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
Tukaj je surovo besedilo s spletne strani restavracije '{restaurant_name}'.
Danes je {today_str}.
Naloga: Poišči današnje dnevne malice in kosila za {today_name} ali datum {now.strftime('%d.%m')}.
Vrni izključno veljaven JSON seznam (brez markdown besedila ```json), v tej obliki:
[
  {{
    "main": "Ime glavne jedi",
    "detail": "priloga, solata, juha ali opis (če obstaja)",
    "price": "npr. 8,50 €",
    "tags": ["mesno"]
  }}
]
Dovoljeni tagi v polju 'tags' so: "mesno", "vegi", "riba", "zlica", "solata".
Če na strani ni današnjega jedilnika ali ga ne najdeš, vrni prazen seznam: [].
Besedilo strani:
{text}
"""
        response = model.generate_content(prompt)
        raw = response.text.strip()
        # Odstrani morebitne markdown oznake
        raw = re.sub(r"^```(?:json)?", "", raw)
        raw = re.sub(r"```$", "", raw).strip()
        parsed = json.loads(raw)
        if isinstance(parsed, list) and len(parsed) > 0:
            return parsed
    except Exception as e:
        print(f"Gemini napaka pri {restaurant_name}: {e}")
    return None

def main():
    print(f"Zagon osveževanja za dan: {today_str}")
    results = []

    for r in RESTAURANTS_CONFIG:
        print(f"Berem: {r['name']}...")
        page_text = fetch_page_text(r["url"])
        dishes = None

        if page_text and GEMINI_KEY:
            dishes = ask_gemini_to_extract(r["name"], page_text)

        # Če AI ni našel ali ni ključa, pripravi pošteno obvestilo
        if not dishes or len(dishes) == 0:
            dishes = [
                {
                    "main": "Dnevna ponudba se nahaja na spletni strani",
                    "detail": "Kliknite spodnji gumb za neposreden ogled svežega menija",
                    "price": "",
                    "tags": ["mesno"]
                }
            ]

        r_data = dict(r)
        # Shranimo jedi pod ključ "menu"
        r_data["menu"] = dishes
        results.append(r_data)

    with open("menus.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("menus.json uspešno shranjen!")

if __name__ == "__main__":
    main()
