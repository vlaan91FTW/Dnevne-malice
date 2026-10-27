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
        resp =
