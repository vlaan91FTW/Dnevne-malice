import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

now = datetime.now()
days_sl = ["Ponedeljek", "Torek", "Sreda", "Četrtek", "Petek", "Sobota", "Nedelja"]
today_name = days_sl[now.weekday()]
today_str = f"{today_name}, {now.strftime('%d. %m. %Y')}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "sl,en-US;q=0.7,en;q=0.3"
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
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"  [OPOZORILO] Status koda {resp.status_code} za {url}")
            return "", None
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        image_data = None
        if look_for_image:
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if re.search(r"jedilnik|meni|malic|kosil", src, re.I):
                    if not src.startswith("http"):
                        src = requests.compat.urljoin(url, src)
                    try:
                        img_resp = requests.get(src, headers=HEADERS, timeout=12)
                        if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                            image_data = img_resp.content
                            print(f"  [SLIKA] Najdena slika menija ({len(image_data)} bajtov)")
                            break
                    except Exception as ie:
                        print(f"  [SLIKA NAPAKA] {ie}")

        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        
        text = " ".join(soup.stripped_strings)
        return text[:8000], image_data
    except Exception as e:
        print(f"  [NAPAKA PRI PRENOSU] {url}: {e}")
        return "", None

def extract_with_gemini(client, target_model, restaurant_name, text, image_bytes=None):
    prompt = f"""
Si pomočnik za slovenske kulinarične jedilnike.
Restavracija: '{restaurant_name}'.
Danes je: {today_str}.

Tvoja naloga je, da iz podanega gradiva izluščiš jedilnik za DANAŠNJI DAN ({today_name}) 
ter za celoten teden (1=Ponedeljek, 2=Torek, 3=Sreda, 4=Četrtek, 5=Petek), če je na voljo.

Vrni IZKLJUČNO veljaven JSON objekt v naslednji obliki:
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
    "1": [],
    "2": [],
    "3": [],
    "4": [],
    "5": []
  }}
}}

Pravila:
- Dovoljeni tagi: "mesno", "vegi", "riba", "zlica", "solata".
- Polje "menu" mora vsebovati točno današnje jedi za {today_name}.
- Če za danes ni objavljenih jedi, naj bo "menu" prazen seznam: [].

Gradivo:
{text}
"""
    contents = [prompt]
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

    try:
        response = client.models.generate_content(
            model=target_model,
            contents=contents
        )
        if response and response.text:
            raw = response.text.strip()
            raw = re.sub(r"^```(?:json)?", "", raw, flags=re.MULTILINE)
            raw = re.sub(r"```$", "", raw, flags=re.MULTILINE).strip()
            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
    except Exception as e:
        print(f"  [AI NAPAKA] {e}")

    return None

def main():
    print(f"=== ZAGON ROBOTA ({today_str}) ===")
    
    if not GEMINI_KEY:
        print("[KRITIČNA NAPAKA] GEMINI_API_KEY NI NASTAVLJEN V OKOLJU!")
        return

    print(f"[OK] GEMINI_API_KEY zaznan (dolžina: {len(GEMINI_KEY)} znakov).")
    
    try:
        client = genai.Client(api_key=GEMINI_KEY)
    except Exception as ce:
        print(f"[KRITIČNA NAPAKA PRI ZAGONU ODJEMALCA]: {ce}")
        return

    # Ugotovimo kateri model je na voljo (privzeto gemini-3.8-flash, kot zahteva Google)
    chosen_model = "gemini-3.8-flash"
    try:
        available_models = [m.name for m in client.models.list()]
        for m in available_models:
            if "3.8-flash" in m:
                chosen_model = m
                break
    except Exception as e:
        print(f"  [Opomba: Uporabljam privzeti model {chosen_model}]")

    print(f"[MODEL] Uporabljam model: {chosen_model}")

    results = []

    for r in RESTAURANTS_CONFIG:
        print(f"\nObdelujem: {r['name']}...")
        text, img_bytes = fetch_page_content(r["url"], look_for_image=r.get("has_image_flyer", False))
        
        parsed = None
        if text or img_bytes:
            parsed = extract_with_gemini(client, chosen_model, r["name"], text, img_bytes)

        r_data = dict(r)
        
        if parsed and isinstance(parsed, dict) and parsed.get("menu"):
            r_data["menu"] = parsed.get("menu", [])
            r_data["weeklyMenu"] = parsed.get("weeklyMenu", {})
            print(f"  -> Uspešno najdenih {len(r_data['menu'])} jedi za danes.")
        else:
            print(f"  -> Ni najdenih jedi za danes. Uporabljam obvestilo.")
            r_data["menu"] = [
                {
                    "main": "Meni za danes še ni objavljen na spletni strani",
                    "detail": "Restavracija menije običajno posodobi med 10.00 in 11.00 uro. Kliknite spodnji gumb za ogled uradne strani.",
                    "price": "",
                    "tags": ["mesno"]
                }
            ]
            r_data["weeklyMenu"] = {}

        results.append(r_data)

    with open("menus.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n=== ZAKLJUČENO: menus.json je posodobljen! ===")

if __name__ == "__main__":
    main()
