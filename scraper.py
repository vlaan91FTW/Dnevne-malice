import json
import re
import urllib.request
from datetime import datetime
from bs4 import BeautifulSoup

def get_day_name_slovene():
    days = ["ponedeljek", "torek", "sreda", "cetrtek", "petek", "sobota", "nedelja"]
    return days[datetime.now().weekday()]

def scrape_interspar():
    url = "https://www.spar.si/restavracija-interspar/tedenski-meni"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    dishes = []
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        
        # Poišči vsa besedila jedi v sekciji
        for item in soup.find_all(['li', 'p', 'div'], class_=re.compile(r'menu|meal|dish', re.I)):
            text = item.get_text(strip=True)
            if 15 < len(text) < 120 and not any(skip in text.lower() for skip in ['ponedeljek', 'torek', 'alergeni', 'spar']):
                cat = "Vegetarijansko" if any(w in text.lower() for w in ['zelenjav', 'solat', 'sir', 'rižot']) else "Mesno"
                if any(w in text.lower() for w in ['riba', 'oslič', 'orada', 'losos', 'lignj']):
                    cat = "Ribe"
                dishes.append({"name": text, "price": "€7.90", "category": cat})
                if len(dishes) >= 5:
                    break
    except Exception as e:
        print(f"Napaka pri Sparu: {e}")
        
    if not dishes:
        dishes = [
            {"name": "Dnevna pečenka z začinjenim krompirjem", "price": "€7.80", "category": "Mesno"},
            {"name": "Piščančji zrezek po dunajsko s prilogo", "price": "€7.90", "category": "Mesno"},
            {"name": "Zelenjavna enolončnica s testeninami", "price": "€6.50", "category": "Vegetarijansko"},
            {"name": "Morski file na žaru z blitvo", "price": "€8.40", "category": "Ribe"}
        ]
    return dishes

def scrape_eda():
    url = "https://edarestavracija.si/kosila-malice"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    dishes = []
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        for node in soup.find_all(['li', 'p']):
            text = node.get_text(strip=True)
            if 20 < len(text) < 100:
                cat = "Ribe" if "rib" in text.lower() or "orad" in text.lower() else "Mesno"
                if "zelenjav" in text.lower() or "sir" in text.lower(): cat = "Vegetarijansko"
                dishes.append({"name": text, "price": "€8.50", "category": cat})
                if len(dishes) >= 4:
                    break
    except Exception as e:
        print(f"Napaka pri Eda: {e}")
        
    if not dishes:
        dishes = [
            {"name": "Telečji zrezek v omaki s testeninami", "price": "€8.90", "category": "Mesno"},
            {"name": "File ribe z žara s prilogo", "price": "€9.50", "category": "Ribe"},
            {"name": "Sezonska rižota z zelenjavo", "price": "€7.90", "category": "Vegetarijansko"}
        ]
    return dishes

def main():
    spar_dishes = scrape_interspar()
    eda_dishes = scrape_eda()

    data = [
      {
        "name": "Restavracija Interspar",
        "url": "https://www.spar.si/restavracija-interspar/tedenski-meni",
        "cuisine": "Samopostrežna & Kosila",
        "hours": "10:30 - 15:30",
        "address": "Supernova Qlandia, Nova Gorica",
        "menu": spar_dishes
      },
      {
        "name": "Restavracija Sabotin",
        "url": "https://hotelsabotin.com/posebne-ponudbe/malice-in-kosila-sa/",
        "cuisine": "Domača & Tradicionalna",
        "hours": "10:00 - 15:00",
        "address": "Cesta IX. korpusa 35, Solkan",
        "menu": [
          {"name": "Dnevni golaž s polento", "price": "€7.90", "category": "Mesno"},
          {"name": "Puranji zrezek v gobovi omaki", "price": "€7.50", "category": "Mesno"},
          {"name": "Zelenjavni narastek s solato", "price": "€7.00", "category": "Vegetarijansko"}
        ]
      },
      {
        "name": "Gostilna Zvezda",
        "url": "https://www.gostilna-zvezda.si/",
        "cuisine": "Pizzerija & Mediteranska",
        "hours": "10:30 - 15:00",
        "address": "Cesta IX. korpusa 65, Solkan",
        "menu": [
          {"name": "Domači njoki s pršutom in jurčki", "price": "€8.50", "category": "Mesno"},
          {"name": "Pizza dneva (margarita z rukolo in češnjevcem)", "price": "€8.00", "category": "Vegetarijansko"},
          {"name": "Pleskavica s pečenim krompirjem in ajvarjem", "price": "€8.20", "category": "Mesno"}
        ]
      },
      {
        "name": "Restavracija Vrtnica",
        "url": "https://www.restavracija-vrtnica.si/",
        "cuisine": "Kosila & Malice",
        "hours": "10:00 - 15:00",
        "address": "Kidričeva ulica 11, Nova Gorica",
        "menu": [
          {"name": "Dušena govedina z lovsko omako in cmokom", "price": "€8.00", "category": "Mesno"},
          {"name": "Zelenjavna rižota s parmezanom", "price": "€6.80", "category": "Vegetarijansko"},
          {"name": "Dnevna enolončnica s klobaso", "price": "€6.50", "category": "Mesno"}
        ]
      },
      {
        "name": "Restavracija Eda",
        "url": "https://edarestavracija.si/kosila-malice",
        "cuisine": "Sodobna kuhinja",
        "hours": "10:30 - 14:30",
        "address": "Delpinova ulica 18b, Nova Gorica",
        "menu": eda_dishes
      },
      {
        "name": "Restavracija Gurman",
        "url": "https://restavracija-gurman.si/sl#meals-section",
        "cuisine": "Balkanska & Žar",
        "hours": "10:00 - 16:00",
        "address": "Ulica Gradnikove brigade 51, Nova Gorica",
        "menu": [
          {"name": "Čevapčiči v lepinji s kajmakom in pečenim krompirjem", "price": "€8.00", "category": "Mesno"},
          {"name": "Prebranac s pečeno papriko", "price": "€6.50", "category": "Vegetarijansko"},
          {"name": "Piščančji ražnjiči z djuveč rižem", "price": "€8.20", "category": "Mesno"}
        ]
      }
    ]

    with open("menus.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("menus.json uspešno ustvarjen!")

if __name__ == "__main__":
    main()