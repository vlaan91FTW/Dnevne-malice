import json
import os
import requests
from bs4 import BeautifulSoup
from google import genai

# Modern initialization
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

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
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return " ".join(soup.stripped_strings)[:5000]
    except:
        return ""

def get_menu(restaurant_name, text):
    prompt = f"Si kulinarični asistent. Restavracija: '{restaurant_name}'. Izlušči dnevni meni iz tega besedila: {text}. Vrni strogo JSON: {{'menu': [{{'main': '...', 'detail': '...', 'price': '...'}}]}}"
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return json.loads(response.text.replace("```json", "").replace("```", ""))
    except:
        return {"menu": [{"main": "Meni še ni na voljo", "detail": "Poskusite kasneje", "price": ""}]}

def main():
    results = []
    for r in RESTAURANTS_CONFIG:
        text = fetch_page_text(r["url"])
        data = get_menu(r["name"], text)
        r.update(data)
        results.append(r)
    with open("menus.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
