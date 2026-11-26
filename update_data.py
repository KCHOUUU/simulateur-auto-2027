import json
import os
import re
import html
import unicodedata
import datetime
import urllib.request
import zipfile
import io
import xml.etree.ElementTree as ET

DEPARTMENTS = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes", "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes",
    "09": "Ariège", "10": "Aube", "11": "Aude", "12": "Aveyron",
    "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal", "16": "Charente",
    "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "2A": "Corse-du-Sud",
    "2B": "Haute-Corse", "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse",
    "24": "Dordogne", "25": "Doubs", "26": "Drôme", "27": "Eure",
    "28": "Eure-et-Loir", "29": "Finistère", "30": "Gard", "31": "Haute-Garonne",
    "32": "Gers", "33": "Gironde", "34": "Hérault", "35": "Ille-et-Vilaine",
    "36": "Indre", "37": "Indre-et-Loire", "38": "Isère", "39": "Jura",
    "40": "Landes", "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire",
    "44": "Loire-Atlantique", "45": "Loiret", "46": "Lot", "47": "Lot-et-Garonne",
    "48": "Lozère", "49": "Maine-et-Loire", "50": "Manche", "51": "Marne",
    "52": "Haute-Marne", "53": "Mayenne", "54": "Meurthe-et-Moselle", "55": "Meuse",
    "56": "Morbihan", "57": "Moselle", "58": "Nièvre", "59": "Nord",
    "60": "Oise", "61": "Orne", "62": "Pas-de-Calais", "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques", "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales",
    "67": "Bas-Rhin", "68": "Haut-Rhin", "69": "Rhône", "70": "Haute-Saône",
    "71": "Saône-et-Loire", "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie",
    "75": "Paris", "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines",
    "79": "Deux-Sèvres", "80": "Somme", "81": "Tarn", "82": "Tarn-et-Garonne",
    "83": "Var", "84": "Vaucluse", "85": "Vendée", "86": "Vienne",
    "87": "Haute-Vienne", "88": "Vosges", "89": "Yonne", "90": "Territoire de Belfort",
    "91": "Essonne", "92": "Hauts-de-Seine", "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne", "95": "Val-d'Oise"
}

def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")

# 1. Extraction nationale + départementale + Top 3 stations les moins chères
today_fr = datetime.date.today().strftime("%d/%m/%Y")
today_iso = datetime.date.today().isoformat()

prices = {
    "Gazole": 1.68,
    "SP95": 1.79,
    "E10": 1.75,
    "SP98": 1.85,
    "E85": 0.89,
    "Electrique_kWh": 0.2516,
    "updated_at": today_fr
}

FUEL_KEYS = ["Gazole", "SP95", "E10", "SP98", "E85"]
nat_totals = {k: [] for k in FUEL_KEYS}
dept_stations = {code: {k: [] for k in FUEL_KEYS} for code in DEPARTMENTS}

try:
    url = "https://donnees.roulez-eco.fr/opendata/instantane"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        z = zipfile.ZipFile(io.BytesIO(resp.read()))
        xml_name = z.namelist()[0]
        root = ET.fromstring(z.read(xml_name))
        for pdv in root.findall("pdv"):
            cp = (pdv.attrib.get("cp") or "").strip()
            dept = None
            if len(cp) >= 2:
                if cp.startswith("20"):
                    dept = "2B" if cp >= "20200" else "2A"
                elif cp[:2] in DEPARTMENTS:
                    dept = cp[:2]

            ville = (pdv.findtext("ville") or "").strip().title()
            adresse = (pdv.findtext("adresse") or "").strip()

            for p in pdv.findall("prix"):
                nom = p.attrib.get("nom")
                val = p.attrib.get("valeur")
                if nom in nat_totals and val:
                    v = float(val)
                    if 0.4 < v < 3.5:
                        nat_totals[nom].append(v)
                        if dept:
                            dept_stations[dept][nom].append({
                                "p": round(v, 3),
                                "v": ville,
                                "a": adresse,
                                "cp": cp
                            })

        for k, vals in nat_totals.items():
            if len(vals) > 50:
                prices[k] = round(sum(vals) / len(vals), 3)
except Exception as e:
    print("Fallback prix utilisé:", e)

with open("prices.json", "w", encoding="utf-8") as f:
    json.dump(prices, f, ensure_ascii=False, indent=2)

# Construction de departments.json (moyennes locales + Top 3 stations moins chères par carburant)
departments_data = {}
for code, name in DEPARTMENTS.items():
    dslug = f"{slugify(name)}-{code.lower()}"
    avg_fuels = {"Electrique_kWh": prices["Electrique_kWh"]}
    top3_fuels = {}
    station_count = 0
    for k in FUEL_KEYS:
        st_list = dept_stations[code][k]
        if st_list:
            st_list.sort(key=lambda x: x["p"])
            avg_fuels[k] = round(sum(x["p"] for x in st_list) / len(st_list), 3)
            top3_fuels[k] = st_list[:3]
            station_count = max(station_count, len(st_list))
        else:
            avg_fuels[k] = prices[k]
            top3_fuels[k] = []
    departments_data[code] = {
        "code": code,
        "name": name,
        "slug": dslug,
        "count": station_count,
        "prices": avg_fuels,
        "top3": top3_fuels
    }

with open("departments.json", "w", encoding="utf-8") as f:
    json.dump({"updated_at": today_fr, "departments": departments_data}, f, ensure_ascii=False)

FUEL_LABELS = {
    "Gazole": "Diesel (Gazole)",
    "E10": "Essence SP95-E10",
    "SP95": "Essence SP95",
    "SP98": "Essence SP98",
    "E85": "Superéthanol E85",
    "Electrique_kWh": "100 % Électrique"
}

FUEL_UNITS = {
    "Gazole": "L/100 km",
    "E10": "L/100 km",
    "SP95": "L/100 km",
    "SP98": "L/100 km",
    "E85": "L/100 km",
    "Electrique_kWh": "kWh/100 km"
}

# 2. Base complète : 170+ modèles (avec prix indicatif moyen pour le duel 8 ans)
# Format: (Marque, Nom, Energie, Conso, Fixes €/an, Boîtier E85, Catégorie, Prix achat ref €)
RAW_MODELS = [
    ("Peugeot", "Peugeot 108", "E10", 4.9, 840, 790, "Citadine", 11500),
    ("Peugeot", "Peugeot 208", "E10", 5.4, 1050, 890, "Citadine", 18900),
    ("Peugeot", "Peugeot 208 Diesel", "Gazole", 4.4, 1090, 0, "Citadine", 17500),
    ("Peugeot", "Peugeot e-208", "Electrique_kWh", 15.2, 870, 0, "Électrique", 26500),
    ("Peugeot", "Peugeot 2008", "E10", 6.0, 1160, 890, "SUV", 23900),
    ("Peugeot", "Peugeot e-2008", "Electrique_kWh", 16.4, 930, 0, "Électrique", 31500),
    ("Peugeot", "Peugeot 308", "E10", 5.8, 1190, 920, "Compacte", 25900),
    ("Peugeot", "Peugeot 308 Diesel", "Gazole", 4.8, 1230, 0, "Compacte", 24500),
    ("Peugeot", "Peugeot 408", "E10", 6.1, 1290, 950, "Berline", 32900),
    ("Peugeot", "Peugeot 508", "Gazole", 5.3, 1380, 0, "Berline", 29500),
    ("Peugeot", "Peugeot 3008", "Gazole", 5.8, 1320, 0, "SUV", 27900),
    ("Peugeot", "Peugeot 3008 Hybride", "E10", 5.6, 1310, 950, "SUV", 35900),
    ("Peugeot", "Peugeot e-3008", "Electrique_kWh", 17.5, 1020, 0, "Électrique", 42900),
    ("Peugeot", "Peugeot 5008", "Gazole", 6.1, 1380, 0, "Familiale", 31500),
    ("Peugeot", "Peugeot Rifter", "Gazole", 5.7, 1150, 0, "Familiale", 24900),

    ("Renault", "Renault Twingo", "E10", 5.1, 860, 790, "Citadine", 12500),
    ("Renault", "Renault Twingo E-Tech", "Electrique_kWh", 14.5, 790, 0, "Électrique", 16500),
    ("Renault", "Renault Zoe", "Electrique_kWh", 15.6, 840, 0, "Électrique", 15900),
    ("Renault", "Renault 5 E-Tech", "Electrique_kWh", 14.9, 860, 0, "Électrique", 27900),
    ("Renault", "Renault Clio 4", "E10", 5.6, 980, 850, "Citadine", 11900),
    ("Renault", "Renault Clio 5", "Gazole", 4.6, 1120, 0, "Citadine", 17900),
    ("Renault", "Renault Clio 5 Essence", "E10", 5.4, 1040, 890, "Citadine", 18500),
    ("Renault", "Renault Clio 5 Hybride", "E10", 4.4, 1080, 0, "Citadine", 22900),
    ("Renault", "Renault Captur", "E10", 6.1, 1140, 890, "SUV", 22900),
    ("Renault", "Renault Captur Hybride", "E10", 4.8, 1160, 0, "SUV", 26900),
    ("Renault", "Renault Symbioz", "E10", 4.9, 1190, 0, "SUV", 31900),
    ("Renault", "Renault Mégane 4", "Gazole", 4.9, 1180, 0, "Compacte", 17500),
    ("Renault", "Renault Mégane E-Tech", "Electrique_kWh", 15.8, 930, 0, "Électrique", 31900),
    ("Renault", "Renault Arkana", "E10", 5.1, 1220, 0, "SUV", 28900),
    ("Renault", "Renault Austral", "E10", 5.2, 1290, 0, "SUV", 34900),
    ("Renault", "Renault Rafale", "E10", 5.4, 1380, 0, "SUV", 42900),
    ("Renault", "Renault Scénic E-Tech", "Electrique_kWh", 16.9, 980, 0, "Électrique", 37900),
    ("Renault", "Renault Espace 6", "E10", 5.6, 1360, 0, "Familiale", 41900),
    ("Renault", "Renault Kangoo", "Gazole", 5.6, 1120, 0, "Familiale", 24500),

    ("Citroën", "Citroën C1", "E10", 4.8, 820, 790, "Citadine", 10500),
    ("Citroën", "Citroën C3", "E10", 5.5, 960, 850, "Citadine", 15900),
    ("Citroën", "Citroën ë-C3", "Electrique_kWh", 15.1, 820, 0, "Électrique", 22900),
    ("Citroën", "Citroën C3 Aircross", "E10", 6.0, 1080, 890, "SUV", 20500),
    ("Citroën", "Citroën C4", "E10", 5.8, 1120, 890, "Compacte", 22900),
    ("Citroën", "Citroën ë-C4", "Electrique_kWh", 15.9, 890, 0, "Électrique", 27900),
    ("Citroën", "Citroën C4 X", "E10", 5.9, 1140, 890, "Berline", 24500),
    ("Citroën", "Citroën C5 Aircross", "Gazole", 5.7, 1280, 0, "SUV", 26900),
    ("Citroën", "Citroën C5 X", "E10", 6.4, 1340, 950, "Berline", 29500),
    ("Citroën", "Citroën Berlingo", "Gazole", 5.6, 1140, 0, "Familiale", 23900),

    ("Dacia", "Dacia Spring", "Electrique_kWh", 13.2, 760, 0, "Électrique", 16900),
    ("Dacia", "Dacia Sandero", "E10", 5.6, 920, 850, "Citadine", 13900),
    ("Dacia", "Dacia Sandero Stepway", "E10", 5.9, 960, 850, "Citadine", 15900),
    ("Dacia", "Dacia Logan", "E10", 5.5, 900, 850, "Berline", 12500),
    ("Dacia", "Dacia Duster", "Gazole", 5.3, 1080, 0, "SUV", 19900),
    ("Dacia", "Dacia Duster Hybride", "E10", 5.1, 1090, 0, "SUV", 25900),
    ("Dacia", "Dacia Jogger", "E10", 6.0, 1020, 890, "Familiale", 18900),
    ("Dacia", "Dacia Bigster", "E10", 5.5, 1140, 0, "SUV", 27900),

    ("DS", "DS 3", "E10", 5.9, 1210, 920, "SUV", 24900),
    ("DS", "DS 4", "E10", 6.1, 1340, 950, "Compacte", 31900),
    ("DS", "DS 7", "Gazole", 5.9, 1460, 0, "SUV", 34900),

    ("Volkswagen", "Volkswagen Up!", "E10", 4.9, 850, 790, "Citadine", 11900),
    ("Volkswagen", "Volkswagen Polo", "E10", 5.6, 1080, 920, "Citadine", 19900),
    ("Volkswagen", "Volkswagen Golf 7", "Gazole", 4.9, 1210, 0, "Compacte", 16500),
    ("Volkswagen", "Volkswagen Golf 8", "E10", 5.9, 1280, 950, "Compacte", 27900),
    ("Volkswagen", "Volkswagen Golf 8 TDI", "Gazole", 4.7, 1310, 0, "Compacte", 28900),
    ("Volkswagen", "Volkswagen T-Cross", "E10", 6.0, 1160, 920, "SUV", 23500),
    ("Volkswagen", "Volkswagen Taigo", "E10", 5.9, 1170, 920, "SUV", 24500),
    ("Volkswagen", "Volkswagen T-Roc", "E10", 6.4, 1250, 950, "SUV", 27900),
    ("Volkswagen", "Volkswagen Tiguan", "Gazole", 6.0, 1390, 0, "SUV", 33900),
    ("Volkswagen", "Volkswagen Touareg", "Gazole", 8.2, 1950, 0, "SUV", 54900),
    ("Volkswagen", "Volkswagen Passat", "Gazole", 5.2, 1360, 0, "Berline", 29900),
    ("Volkswagen", "Volkswagen Touran", "Gazole", 5.6, 1290, 0, "Familiale", 28500),
    ("Volkswagen", "Volkswagen ID.3", "Electrique_kWh", 15.6, 920, 0, "Électrique", 29900),
    ("Volkswagen", "Volkswagen ID.4", "Electrique_kWh", 17.2, 990, 0, "Électrique", 36900),
    ("Volkswagen", "Volkswagen ID.5", "Electrique_kWh", 17.0, 1020, 0, "Électrique", 39900),
    ("Volkswagen", "Volkswagen ID.7", "Electrique_kWh", 15.9, 1090, 0, "Électrique", 48900),
    ("Volkswagen", "Volkswagen ID.Buzz", "Electrique_kWh", 20.5, 1140, 0, "Électrique", 49900),

    ("Audi", "Audi A1", "E10", 5.8, 1290, 950, "Citadine", 23900),
    ("Audi", "Audi A3", "E10", 6.1, 1460, 990, "Compacte", 30900),
    ("Audi", "Audi A3 TDI", "Gazole", 4.9, 1490, 0, "Compacte", 31500),
    ("Audi", "Audi A4", "Gazole", 5.4, 1580, 0, "Berline", 33900),
    ("Audi", "Audi A5", "Gazole", 5.6, 1660, 0, "Berline", 37900),
    ("Audi", "Audi A6", "Gazole", 6.0, 1820, 0, "Berline", 44900),
    ("Audi", "Audi Q2", "E10", 6.3, 1390, 980, "SUV", 28500),
    ("Audi", "Audi Q3", "E10", 6.8, 1540, 990, "SUV", 36900),
    ("Audi", "Audi Q4 e-tron", "Electrique_kWh", 17.6, 1140, 0, "Électrique", 43900),
    ("Audi", "Audi Q5", "Gazole", 6.6, 1740, 0, "SUV", 45900),
    ("Audi", "Audi Q7", "Gazole", 8.4, 2100, 0, "SUV", 62900),
    ("Audi", "Audi Q8 e-tron", "Electrique_kWh", 22.0, 1420, 0, "Électrique", 64900),

    ("BMW", "BMW Série 1", "E10", 6.3, 1520, 990, "Compacte", 31500),
    ("BMW", "BMW Série 1 Diesel", "Gazole", 5.0, 1550, 0, "Compacte", 31900),
    ("BMW", "BMW Série 2 Active Tourer", "E10", 6.4, 1480, 990, "Familiale", 33900),
    ("BMW", "BMW Série 3", "Gazole", 5.4, 1650, 0, "Berline", 37900),
    ("BMW", "BMW Série 4", "E10", 7.1, 1790, 1050, "Berline", 44900),
    ("BMW", "BMW Série 5", "Gazole", 5.9, 1890, 0, "Berline", 49900),
    ("BMW", "BMW X1", "E10", 6.6, 1540, 990, "SUV", 38900),
    ("BMW", "BMW X2", "E10", 6.7, 1580, 990, "SUV", 39900),
    ("BMW", "BMW X3", "Gazole", 6.5, 1780, 0, "SUV", 47900),
    ("BMW", "BMW X5", "Gazole", 7.9, 2150, 0, "SUV", 66900),
    ("BMW", "BMW iX1", "Electrique_kWh", 17.2, 1140, 0, "Électrique", 42900),
    ("BMW", "BMW i4", "Electrique_kWh", 16.8, 1220, 0, "Électrique", 49900),

    ("Mercedes", "Mercedes Classe A", "E10", 6.2, 1550, 990, "Compacte", 32500),
    ("Mercedes", "Mercedes Classe A Diesel", "Gazole", 5.0, 1580, 0, "Compacte", 32900),
    ("Mercedes", "Mercedes Classe B", "Gazole", 5.3, 1490, 0, "Familiale", 31900),
    ("Mercedes", "Mercedes Classe C", "Gazole", 5.4, 1690, 0, "Berline", 41900),
    ("Mercedes", "Mercedes Classe E", "Gazole", 5.9, 1920, 0, "Berline", 52900),
    ("Mercedes", "Mercedes CLA", "E10", 6.4, 1640, 990, "Berline", 36900),
    ("Mercedes", "Mercedes GLA", "E10", 6.7, 1590, 990, "SUV", 38900),
    ("Mercedes", "Mercedes GLB", "Gazole", 5.9, 1640, 0, "SUV", 40900),
    ("Mercedes", "Mercedes GLC", "Gazole", 6.6, 1840, 0, "SUV", 51900),
    ("Mercedes", "Mercedes EQA", "Electrique_kWh", 17.1, 1160, 0, "Électrique", 43900),
    ("Mercedes", "Mercedes EQB", "Electrique_kWh", 18.0, 1210, 0, "Électrique", 47900),

    ("Toyota", "Toyota Aygo X", "E10", 4.9, 860, 790, "Citadine", 15900),
    ("Toyota", "Toyota Yaris Hybride", "E10", 4.2, 980, 950, "Citadine", 20900),
    ("Toyota", "Toyota Yaris Cross", "E10", 4.7, 1080, 950, "SUV", 25900),
    ("Toyota", "Toyota Corolla Hybride", "E10", 4.6, 1090, 950, "Compacte", 26900),
    ("Toyota", "Toyota C-HR", "E10", 4.9, 1150, 950, "SUV", 30900),
    ("Toyota", "Toyota Prius", "E10", 4.3, 1140, 950, "Berline", 34900),
    ("Toyota", "Toyota RAV4", "E10", 5.8, 1340, 980, "SUV", 36900),
    ("Toyota", "Toyota bZ4X", "Electrique_kWh", 16.8, 990, 0, "Électrique", 37900),
    ("Toyota", "Toyota Hilux", "Gazole", 9.1, 1520, 0, "SUV", 38900),

    ("Tesla", "Tesla Model 3", "Electrique_kWh", 14.8, 950, 0, "Électrique", 35900),
    ("Tesla", "Tesla Model Y", "Electrique_kWh", 16.5, 1050, 0, "Électrique", 40900),
    ("Tesla", "Tesla Model S", "Electrique_kWh", 18.2, 1450, 0, "Électrique", 69900),
    ("Tesla", "Tesla Model X", "Electrique_kWh", 20.4, 1590, 0, "Électrique", 76900),

    ("Ford", "Ford Fiesta", "E10", 5.5, 980, 850, "Citadine", 14500),
    ("Ford", "Ford Focus", "E10", 5.9, 1140, 890, "Compacte", 21900),
    ("Ford", "Ford Puma", "E10", 5.8, 1120, 890, "SUV", 23500),
    ("Ford", "Ford Puma E85", "E85", 7.1, 1120, 0, "SUV", 23900),
    ("Ford", "Ford Kuga", "E10", 6.0, 1260, 950, "SUV", 31900),
    ("Ford", "Ford Kuga E85", "E85", 7.3, 1260, 0, "SUV", 32500),
    ("Ford", "Ford Explorer Électrique", "Electrique_kWh", 16.6, 1020, 0, "Électrique", 41900),
    ("Ford", "Ford Mustang Mach-E", "Electrique_kWh", 18.4, 1180, 0, "Électrique", 44900),
    ("Ford", "Ford Ranger", "Gazole", 9.5, 1590, 0, "SUV", 41900),

    ("Opel", "Opel Corsa", "E10", 5.4, 1010, 890, "Citadine", 17500),
    ("Opel", "Opel Corsa Electric", "Electrique_kWh", 15.1, 860, 0, "Électrique", 24900),
    ("Opel", "Opel Astra", "E10", 5.8, 1160, 920, "Compacte", 24900),
    ("Opel", "Opel Mokka", "E10", 5.9, 1130, 890, "SUV", 22900),
    ("Opel", "Opel Frontera", "E10", 5.7, 1060, 890, "SUV", 23900),
    ("Opel", "Opel Grandland", "E10", 6.2, 1260, 950, "SUV", 31900),

    ("Fiat", "Fiat 500 Hybride", "E10", 5.0, 890, 820, "Citadine", 14900),
    ("Fiat", "Fiat 500 Électrique", "Electrique_kWh", 13.8, 840, 0, "Électrique", 21900),
    ("Fiat", "Fiat 600e", "Electrique_kWh", 15.4, 890, 0, "Électrique", 27900),
    ("Fiat", "Fiat Panda", "E10", 5.2, 830, 790, "Citadine", 11900),
    ("Fiat", "Fiat Tipo", "E10", 6.1, 980, 890, "Compacte", 16900),

    ("Hyundai", "Hyundai i10", "E10", 5.1, 850, 790, "Citadine", 13900),
    ("Hyundai", "Hyundai i20", "E10", 5.5, 990, 890, "Citadine", 17900),
    ("Hyundai", "Hyundai i30", "E10", 6.0, 1120, 920, "Compacte", 22500),
    ("Hyundai", "Hyundai Bayon", "E10", 5.7, 1040, 890, "SUV", 19900),
    ("Hyundai", "Hyundai Kona Hybride", "E10", 4.9, 1120, 0, "SUV", 26900),
    ("Hyundai", "Hyundai Kona Électrique", "Electrique_kWh", 15.5, 920, 0, "Électrique", 31900),
    ("Hyundai", "Hyundai Tucson", "E10", 6.1, 1290, 950, "SUV", 32900),
    ("Hyundai", "Hyundai Ioniq 5", "Electrique_kWh", 17.5, 1040, 0, "Électrique", 38900),
    ("Hyundai", "Hyundai Ioniq 6", "Electrique_kWh", 15.1, 1060, 0, "Électrique", 41900),

    ("Kia", "Kia Picanto", "E10", 5.2, 850, 790, "Citadine", 13900),
    ("Kia", "Kia Ceed", "E10", 6.0, 1110, 920, "Compacte", 21900),
    ("Kia", "Kia XCeed", "E10", 6.2, 1150, 920, "SUV", 23900),
    ("Kia", "Kia Niro Hybride", "E10", 4.8, 1120, 0, "SUV", 27900),
    ("Kia", "Kia Niro EV", "Electrique_kWh", 16.0, 940, 0, "Électrique", 32900),
    ("Kia", "Kia Sportage", "E10", 6.2, 1270, 950, "SUV", 32500),
    ("Kia", "Kia EV3", "Electrique_kWh", 15.6, 930, 0, "Électrique", 34900),
    ("Kia", "Kia EV6", "Electrique_kWh", 17.4, 1080, 0, "Électrique", 39900),

    ("Nissan", "Nissan Micra", "E10", 5.4, 940, 850, "Citadine", 13900),
    ("Nissan", "Nissan Juke", "E10", 5.8, 1120, 890, "SUV", 21900),
    ("Nissan", "Nissan Qashqai", "E10", 6.3, 1220, 920, "SUV", 29900),
    ("Nissan", "Nissan X-Trail", "E10", 6.5, 1340, 950, "SUV", 36900),
    ("Nissan", "Nissan Leaf", "Electrique_kWh", 16.2, 870, 0, "Électrique", 18900),
    ("Nissan", "Nissan Ariya", "Electrique_kWh", 18.0, 1050, 0, "Électrique", 38900),

    ("Skoda", "Skoda Fabia", "E10", 5.4, 980, 890, "Citadine", 17900),
    ("Skoda", "Skoda Scala", "E10", 5.6, 1060, 890, "Compacte", 21500),
    ("Skoda", "Skoda Octavia", "Gazole", 4.8, 1210, 0, "Berline", 26900),
    ("Skoda", "Skoda Superb", "Gazole", 5.3, 1340, 0, "Berline", 33900),
    ("Skoda", "Skoda Kamiq", "E10", 5.8, 1090, 920, "SUV", 22500),
    ("Skoda", "Skoda Karoq", "E10", 6.3, 1210, 950, "SUV", 27900),
    ("Skoda", "Skoda Kodiaq", "Gazole", 6.1, 1360, 0, "SUV", 36900),
    ("Skoda", "Skoda Enyaq", "Electrique_kWh", 16.9, 980, 0, "Électrique", 38900),

    ("SEAT", "SEAT Ibiza", "E10", 5.5, 990, 890, "Citadine", 17900),
    ("SEAT", "SEAT Leon", "E10", 5.9, 1160, 920, "Compacte", 22900),
    ("SEAT", "SEAT Arona", "E10", 5.8, 1080, 890, "SUV", 20900),
    ("SEAT", "SEAT Ateca", "E10", 6.4, 1220, 950, "SUV", 26900),
    ("Cupra", "Cupra Born", "Electrique_kWh", 15.8, 950, 0, "Électrique", 32900),
    ("Cupra", "Cupra Leon", "E10", 6.8, 1380, 990, "Compacte", 32900),
    ("Cupra", "Cupra Formentor", "E10", 6.9, 1420, 990, "SUV", 34900),

    ("Volvo", "Volvo EX30", "Electrique_kWh", 16.2, 990, 0, "Électrique", 36900),
    ("Volvo", "Volvo XC40", "E10", 6.8, 1440, 980, "SUV", 35900),
    ("Volvo", "Volvo XC60", "Gazole", 6.6, 1690, 0, "SUV", 45900),
    ("Volvo", "Volvo XC90", "E10", 8.5, 2050, 0, "SUV", 59900),

    ("Mini", "Mini Cooper", "E10", 6.0, 1280, 950, "Citadine", 25900),
    ("Mini", "Mini Cooper Electric", "Electrique_kWh", 14.9, 990, 0, "Électrique", 29900),
    ("Mini", "Mini Countryman", "E10", 6.6, 1410, 980, "SUV", 33900),

    ("Suzuki", "Suzuki Ignis", "E10", 5.0, 860, 790, "Citadine", 14900),
    ("Suzuki", "Suzuki Swift", "E10", 4.8, 920, 850, "Citadine", 16900),
    ("Suzuki", "Suzuki Vitara", "E10", 5.6, 1080, 890, "SUV", 21900),
    ("Suzuki", "Suzuki S-Cross", "E10", 5.8, 1110, 890, "SUV", 23900),

    ("Mazda", "Mazda 2", "E10", 5.1, 960, 850, "Citadine", 17500),
    ("Mazda", "Mazda 3", "E10", 5.9, 1190, 920, "Compacte", 24900),
    ("Mazda", "Mazda CX-30", "E10", 6.2, 1220, 950, "SUV", 26900),
    ("Mazda", "Mazda CX-5", "E10", 7.1, 1350, 980, "SUV", 31900),
    ("Mazda", "Mazda MX-5", "SP98", 6.8, 1340, 950, "Sportive", 28900),

    ("Honda", "Honda Jazz Hybride", "E10", 4.6, 1020, 0, "Citadine", 22900),
    ("Honda", "Honda Civic Hybride", "E10", 4.9, 1220, 0, "Compacte", 32900),
    ("Honda", "Honda HR-V", "E10", 5.4, 1180, 0, "SUV", 28900),
    ("Honda", "Honda CR-V", "E10", 6.2, 1380, 0, "SUV", 38900),

    ("MG", "MG3 Hybrid+", "E10", 4.6, 940, 0, "Citadine", 19900),
    ("MG", "MG4 Électrique", "Electrique_kWh", 16.0, 880, 0, "Électrique", 24900),
    ("MG", "MG ZS", "E10", 6.6, 990, 890, "SUV", 18900),
    ("MG", "MG HS", "E10", 7.2, 1140, 950, "SUV", 24900),
    ("BYD", "BYD Dolphin", "Electrique_kWh", 15.9, 890, 0, "Électrique", 27900),
    ("BYD", "BYD Atto 3", "Electrique_kWh", 16.5, 960, 0, "Électrique", 33900),
    ("BYD", "BYD Seal", "Electrique_kWh", 16.6, 1060, 0, "Électrique", 41900),
    ("BYD", "BYD Seal U", "Electrique_kWh", 19.2, 1090, 0, "Électrique", 39900),

    ("Alfa Romeo", "Alfa Romeo Junior", "Electrique_kWh", 15.4, 1020, 0, "Électrique", 34900),
    ("Alfa Romeo", "Alfa Romeo Tonale", "E10", 6.5, 1420, 980, "SUV", 34900),
    ("Alfa Romeo", "Alfa Romeo Giulia", "Gazole", 5.7, 1620, 0, "Berline", 36900),
    ("Alfa Romeo", "Alfa Romeo Stelvio", "Gazole", 6.8, 1790, 0, "SUV", 42900),
    ("Jeep", "Jeep Avenger", "E10", 5.8, 1120, 890, "SUV", 24900),
    ("Jeep", "Jeep Renegade", "E10", 6.6, 1190, 920, "SUV", 23900),
    ("Jeep", "Jeep Compass", "E10", 6.8, 1310, 950, "SUV", 29900),
    ("Land Rover", "Range Rover Evoque", "Gazole", 6.9, 1850, 0, "SUV", 44900),
    ("Land Rover", "Land Rover Defender", "Gazole", 8.8, 2150, 0, "SUV", 69900),
    ("Lexus", "Lexus LBX", "E10", 4.7, 1280, 0, "SUV", 32900),
    ("Lexus", "Lexus UX", "E10", 5.3, 1390, 0, "SUV", 34900),
    ("Lexus", "Lexus NX", "E10", 6.0, 1620, 0, "SUV", 48900),
    ("Porsche", "Porsche Macan Électrique", "Electrique_kWh", 19.8, 1850, 0, "Électrique", 82900),
    ("Porsche", "Porsche Taycan", "Electrique_kWh", 20.5, 2100, 0, "Électrique", 89900),
    ("Porsche", "Porsche Cayenne", "SP98", 11.2, 2650, 0, "SUV", 89900),
    ("Porsche", "Porsche 911 Carrera", "SP98", 10.6, 2900, 0, "Sportive", 119000),
    ("Alpine", "Alpine A110", "SP98", 7.4, 1780, 0, "Sportive", 62900),
    ("Alpine", "Alpine A290", "Electrique_kWh", 16.5, 1050, 0, "Électrique", 37900),
    ("Smart", "Smart #1", "Electrique_kWh", 16.8, 990, 0, "Électrique", 34900),
    ("Smart", "Smart #3", "Electrique_kWh", 16.4, 1040, 0, "Électrique", 36900),
    ("Mitsubishi", "Mitsubishi Colt", "E10", 5.3, 990, 890, "Citadine", 17500),
    ("Mitsubishi", "Mitsubishi ASX", "E10", 5.9, 1120, 890, "SUV", 22900),
    ("Polestar", "Polestar 2", "Electrique_kWh", 16.5, 1120, 0, "Électrique", 39900),
    ("Leapmotor", "Leapmotor T03", "Electrique_kWh", 13.8, 780, 0, "Électrique", 17900),
]

MODELS = []
seen_slugs = set()
for brand, name, fuel, conso, fixed, e85_cost, cat, buy_price in RAW_MODELS:
    slug = slugify(name)
    if slug in seen_slugs:
        continue
    seen_slugs.add(slug)
    MODELS.append({
        "slug": slug,
        "brand": brand,
        "name": name,
        "fuel": fuel,
        "conso": conso,
        "fixed": fixed,
        "e85_cost": e85_cost,
        "cat": cat,
        "buy": buy_price
    })

DUELS = [
    ("peugeot-208", "renault-clio-5"),
    ("dacia-sandero", "citroen-c3"),
    ("peugeot-3008", "renault-austral"),
    ("tesla-model-3", "mg4-electrique"),
    ("peugeot-2008", "renault-captur"),
    ("toyota-yaris-hybride", "renault-clio-5"),
    ("volkswagen-golf-8", "peugeot-308"),
    ("audi-a3", "bmw-serie-1"),
    ("dacia-duster", "peugeot-2008"),
    ("tesla-model-y", "peugeot-3008"),
    ("renault-5-e-tech", "peugeot-e-208"),
    ("renault-megane-e-tech", "volkswagen-id-3"),
    ("byd-dolphin", "mg4-electrique"),
    ("hyundai-tucson", "kia-sportage"),
    ("toyota-c-hr", "renault-arkana"),
    ("mercedes-classe-a", "audi-a3"),
    ("dacia-spring", "citroen-e-c3"),
    ("ford-puma-e85", "peugeot-2008"),
    ("cupra-formentor", "volkswagen-t-roc"),
    ("bmw-x1", "audi-q3"),
]

with open("models.json", "w", encoding="utf-8") as f:
    json.dump(MODELS, f, ensure_ascii=False, indent=2)

os.makedirs("modeles", exist_ok=True)
os.makedirs("duels", exist_ok=True)
os.makedirs("carburant", exist_ok=True)

models_by_slug = {m["slug"]: m for m in MODELS}
valid_duels = [(a, b) for a, b in DUELS if a in models_by_slug and b in models_by_slug]
total_models = len(MODELS)

sitemap_urls = [
    f"  <url><loc>https://simulateur-auto.com/</loc><lastmod>{today_iso}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>",
    f"  <url><loc>https://simulateur-auto.com/modeles/</loc><lastmod>{today_iso}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>",
    f"  <url><loc>https://simulateur-auto.com/carburant/</loc><lastmod>{today_iso}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>",
    f"  <url><loc>https://simulateur-auto.com/mentions-legales.html</loc><changefreq>yearly</changefreq><priority>0.3</priority></url>"
]

# 3. Génération des 170+ pages modèles
MODEL_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Coût réel __NAME__ (2027) — Budget carburant, assurance & entretien</title>
  <meta name="description" content="Combien coûte vraiment une __NAME__ en 2027 ? Budget mensuel (__TOTAL_MONTH__ €/mois), coût au kilomètre (__PER_KM__ €/km) actualisé au __UPDATED_AT__." />
  <link rel="canonical" href="https://simulateur-auto.com/modeles/__SLUG__.html" />
  <link rel="manifest" href="/manifest.json" />
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🚗</text></svg>" />
  <style>
    body { margin:0; background:#050811; color:#f8fafc; font-family:system-ui,-apple-system,sans-serif; line-height:1.6; padding:24px 16px; }
    .wrap { max-width:880px; margin:0 auto; }
    a { color:#38bdf8; text-decoration:none; }
    a:hover { text-decoration:underline; }
    .topbar { display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:18px; font-size:0.9rem; }
    .card { background:rgba(15,23,42,0.88); border:1px solid rgba(148,163,184,0.18); border-radius:18px; padding:24px; margin-bottom:20px; }
    .badge { display:inline-block; background:rgba(34,197,94,0.14); border:1px solid rgba(34,197,94,0.35); color:#4ade80; font-size:0.82rem; font-weight:600; padding:4px 12px; border-radius:999px; }
    .slider-box { background:#090e1a; border:1px solid rgba(148,163,184,0.16); border-radius:12px; padding:16px; margin:18px 0; }
    .slider-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; font-size:0.9rem; }
    .pill { background:rgba(56,189,248,0.14); color:#38bdf8; font-weight:700; padding:2px 10px; border-radius:6px; }
    input[type="range"] { width:100%; accent-color:#38bdf8; cursor:pointer; }
    .grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-top:16px; }
    @media(max-width:650px) { .grid { grid-template-columns:1fr; } }
    .stat { background:#090e1a; padding:16px; border-radius:12px; text-align:center; border:1px solid rgba(148,163,184,0.14); }
    .stat span { display:block; font-size:0.8rem; color:#94a3b8; margin-bottom:4px; }
    .stat strong { font-size:1.45rem; color:#38bdf8; }
    .btn-row { display:flex; flex-wrap:wrap; gap:12px; justify-content:center; margin-top:22px; }
    .btn { display:inline-block; background:linear-gradient(135deg,#0284c7,#1d4ed8); color:#fff; font-weight:700; padding:12px 22px; border-radius:10px; text-decoration:none !important; }
    .btn-sec { display:inline-block; background:rgba(56,189,248,0.12); border:1px solid rgba(56,189,248,0.35); color:#38bdf8; font-weight:600; padding:12px 20px; border-radius:10px; text-decoration:none !important; }
    .chips { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
    .chip { background:#090e1a; border:1px solid rgba(148,163,184,0.18); padding:7px 12px; border-radius:9px; font-size:0.86rem; color:#f8fafc; text-decoration:none !important; }
    .chip:hover { border-color:#38bdf8; color:#38bdf8; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="topbar">
      <a href="/">← Cockpit SimulateurAuto.com</a>
      <a href="/carburant/">Prix stations par département</a>
      <a href="/modeles/">Catalogue (__TOTAL_MODELS__ modèles) →</a>
    </div>

    <div class="card">
      <span class="badge">● Prix officiels à jour au __UPDATED_AT__ (__UNIT_PRICE__ __PRICE_UNIT__)</span>
      <h1 style="margin:12px 0 8px;">Coût réel d'une __NAME__ en 2027</h1>
      <p style="color:#94a3b8;margin-top:0;">Marque <strong>__BRAND__</strong> • Catégorie <strong>__CAT__</strong> • <strong>__FUEL_LABEL__</strong> • Conso <strong>__CONSO__ __CONSO_UNIT__</strong> • Frais fixes estimés <strong>__FIXED__ €/an</strong>.</p>

      <div class="slider-box">
        <div class="slider-head">
          <span>Ajustez votre kilométrage annuel :</span>
          <span class="pill" id="km-val">15 000 km / an</span>
        </div>
        <input type="range" id="km-slider" min="3000" max="45000" step="500" value="15000" />
      </div>

      <div class="grid">
        <div class="stat"><span>Budget total / mois</span><strong id="stat-month" style="color:#4ade80;">__TOTAL_MONTH__ €</strong></div>
        <div class="stat"><span>Énergie / an</span><strong id="stat-energy">__ENERGY_15K__ €</strong></div>
        <div class="stat"><span>Coût réel / km</span><strong id="stat-km">__PER_KM__ €</strong></div>
      </div>

      <div class="btn-row">
        <a href="#affiliation-assurance" class="btn" rel="nofollow sponsored">Réduire l'assurance de ma __NAME__ →</a>
        <a id="cockpit-link" href="/?fuel=__FUEL_KEY__&conso=__CONSO__&fixed=__FIXED__&km=15000" class="btn-sec">Ouvrir dans le cockpit (Choc Salaire & PNG) →</a>
      </div>
    </div>

    __ROI_BLOCK__
    __DUELS_BLOCK__

    <div class="card">
      <h2 style="margin-top:0;font-size:1.1rem;">Autres modèles __BRAND__ & concurrents (__CAT__)</h2>
      <div class="chips">__OTHER_LINKS__</div>
    </div>
  </div>

  <script>
    const CONSO = __CONSO__;
    const UNIT_PRICE = __UNIT_PRICE__;
    const FIXED = __FIXED__;
    const E85_COST = __E85_COST__;
    const E85_PRICE = __E85_PRICE__;
    const FUEL_KEY = "__FUEL_KEY__";

    const slider = document.getElementById("km-slider");
    function updateSim() {
      const km = parseInt(slider.value, 10);
      document.getElementById("km-val").textContent = km.toLocaleString("fr-FR") + " km / an";
      const energy = (km / 100) * CONSO * UNIT_PRICE;
      const total = energy + FIXED;
      document.getElementById("stat-month").textContent = Math.round(total / 12).toLocaleString("fr-FR") + " €";
      document.getElementById("stat-energy").textContent = Math.round(energy).toLocaleString("fr-FR") + " €";
      document.getElementById("stat-km").textContent = (total / km).toFixed(2) + " €";
      document.getElementById("cockpit-link").href = "/?fuel=" + FUEL_KEY + "&conso=" + CONSO + "&fixed=" + FIXED + "&km=" + km;

      if (E85_COST > 0) {
        const e85Energy = (km / 100) * (CONSO * 1.18) * E85_PRICE;
        const eco = Math.max(1, Math.round(energy - e85Energy));
        const mois = Math.round((E85_COST / eco) * 12);
        const gain5 = (eco * 5) - E85_COST;
        document.getElementById("e85-eco").textContent = "+" + eco.toLocaleString("fr-FR") + " €";
        document.getElementById("e85-mois").textContent = mois + " mois";
        document.getElementById("e85-5ans").textContent = (gain5 >= 0 ? "+" : "") + gain5.toLocaleString("fr-FR") + " €";
      }
    }
    slider.addEventListener("input", updateSim);
  </script>
</body>
</html>
"""

for m in MODELS:
    unit_price = prices.get(m["fuel"], 1.75)
    energy_15k = round((15000 / 100) * m["conso"] * unit_price)
    total_year = energy_15k + m["fixed"]
    total_month = round(total_year / 12)
    per_km = round(total_year / 15000, 2)
    price_unit = "€/kWh" if m["fuel"] == "Electrique_kWh" else "€/L"

    roi_block = ""
    if m["e85_cost"] > 0:
        e85_energy = round((15000 / 100) * (m["conso"] * 1.18) * prices["E85"])
        eco_an = max(1, energy_15k - e85_energy)
        mois_roi = round((m["e85_cost"] / eco_an) * 12)
        gain_5 = (eco_an * 5) - m["e85_cost"]
        roi_block = f"""
    <div class="card">
      <h2 style="margin-top:0;">Rentabilité boîtier Superéthanol E85 sur {m['name']}</h2>
      <p style="color:#94a3b8;margin-top:0;">Avec un boîtier homologué estimé à <strong>{m['e85_cost']} €</strong> et l'E85 à <strong>{prices['E85']} €/L</strong> aujourd'hui (surconsommation +18 % incluse) :</p>
      <div class="grid">
        <div class="stat"><span>Économie carburant / an</span><strong id="e85-eco" style="color:#4ade80;">+{eco_an} €</strong></div>
        <div class="stat"><span>Rentabilisé en</span><strong id="e85-mois">{mois_roi} mois</strong></div>
        <div class="stat"><span>Gain net sur 5 ans</span><strong id="e85-5ans" style="color:#4ade80;">+{gain_5} €</strong></div>
      </div>
    </div>"""

    related_duels = []
    for s1, s2 in valid_duels:
        if m["slug"] in (s1, s2):
            m1, m2 = models_by_slug[s1], models_by_slug[s2]
            related_duels.append(f'<a class="chip" href="/duels/{s1}-vs-{s2}.html">Duel : {m1["name"]} vs {m2["name"]} →</a>')
    duels_block = ""
    if related_duels:
        duels_block = f"""
    <div class="card">
      <h2 style="margin-top:0;font-size:1.1rem;">Duels comparatifs avec {m['name']}</h2>
      <div class="chips">{''.join(related_duels)}</div>
    </div>"""

    same_brand = [o for o in MODELS if o["slug"] != m["slug"] and o["brand"] == m["brand"]][:5]
    same_cat = [o for o in MODELS if o["slug"] != m["slug"] and o["brand"] != m["brand"] and o["cat"] == m["cat"]][:5]
    other_links = "".join([f'<a class="chip" href="/modeles/{o["slug"]}.html">{o["name"]}</a>' for o in (same_brand + same_cat)])

    out = (MODEL_TEMPLATE
        .replace("__NAME__", m["name"])
        .replace("__SLUG__", m["slug"])
        .replace("__BRAND__", m["brand"])
        .replace("__CAT__", m["cat"])
        .replace("__FUEL_KEY__", m["fuel"])
        .replace("__FUEL_LABEL__", FUEL_LABELS[m["fuel"]])
        .replace("__CONSO__", str(m["conso"]))
        .replace("__CONSO_UNIT__", FUEL_UNITS[m["fuel"]])
        .replace("__FIXED__", str(m["fixed"]))
        .replace("__UNIT_PRICE__", str(unit_price))
        .replace("__PRICE_UNIT__", price_unit)
        .replace("__UPDATED_AT__", today_fr)
        .replace("__TOTAL_MONTH__", str(total_month))
        .replace("__ENERGY_15K__", str(energy_15k))
        .replace("__PER_KM__", f"{per_km:.2f}")
        .replace("__E85_COST__", str(m["e85_cost"]))
        .replace("__E85_PRICE__", str(prices["E85"]))
        .replace("__ROI_BLOCK__", roi_block)
        .replace("__DUELS_BLOCK__", duels_block)
        .replace("__OTHER_LINKS__", other_links)
        .replace("__TOTAL_MODELS__", str(total_models))
    )

    with open(f"modeles/{m['slug']}.html", "w", encoding="utf-8") as f:
        f.write(out)

    sitemap_urls.append(
        f"  <url><loc>https://simulateur-auto.com/modeles/{m['slug']}.html</loc><lastmod>{today_iso}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>"
    )

# 4. Génération des 20 pages DUELS
DUEL_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>__N1__ vs __N2__ (2027) — Comparatif coût réel, carburant & budget sur 5 ans</title>
  <meta name="description" content="Match budget 2027 : __N1__ ou __N2__ ? Comparez le coût mensuel, carburant et frais fixes avec les prix officiels du __UPDATED_AT__." />
  <link rel="canonical" href="https://simulateur-auto.com/duels/__DSLUG__.html" />
  <link rel="manifest" href="/manifest.json" />
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🚗</text></svg>" />
  <style>
    body { margin:0; background:#050811; color:#f8fafc; font-family:system-ui,-apple-system,sans-serif; line-height:1.6; padding:24px 16px; }
    .wrap { max-width:900px; margin:0 auto; }
    a { color:#38bdf8; text-decoration:none; }
    .topbar { display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:18px; font-size:0.9rem; }
    .card { background:rgba(15,23,42,0.88); border:1px solid rgba(148,163,184,0.18); border-radius:18px; padding:24px; margin-bottom:20px; }
    .badge { display:inline-block; background:rgba(34,197,94,0.14); border:1px solid rgba(34,197,94,0.35); color:#4ade80; font-size:0.82rem; font-weight:600; padding:4px 12px; border-radius:999px; }
    .slider-box { background:#090e1a; border:1px solid rgba(148,163,184,0.16); border-radius:12px; padding:16px; margin:16px 0; }
    input[type="range"] { width:100%; accent-color:#38bdf8; cursor:pointer; }
    .duel-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px; }
    @media(max-width:650px) { .duel-grid { grid-template-columns:1fr; } }
    .car-box { background:#090e1a; border:1px solid rgba(148,163,184,0.16); border-radius:14px; padding:18px; }
    .car-box h2 { margin:0 0 6px; font-size:1.2rem; color:#38bdf8; }
    .price-big { font-size:1.8rem; font-weight:800; color:#4ade80; margin:10px 0; }
    .line { display:flex; justify-content:space-between; font-size:0.9rem; color:#94a3b8; padding:6px 0; border-bottom:1px solid rgba(148,163,184,0.1); }
    .line strong { color:#f8fafc; }
    .verdict { margin-top:18px; padding:16px; border-radius:12px; background:rgba(34,197,94,0.13); border:1px solid rgba(34,197,94,0.35); text-align:center; font-weight:700; color:#4ade80; }
    .btn { display:inline-block; background:linear-gradient(135deg,#0284c7,#1d4ed8); color:#fff; font-weight:700; padding:12px 22px; border-radius:10px; margin-top:16px; }
    .chips { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
    .chip { background:#090e1a; border:1px solid rgba(148,163,184,0.18); padding:7px 12px; border-radius:9px; font-size:0.86rem; color:#f8fafc; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="topbar">
      <a href="/">← Cockpit SimulateurAuto.com</a>
      <a href="/modeles/">Catalogue des __TOTAL_MODELS__ modèles →</a>
    </div>

    <div class="card">
      <span class="badge">● Match actualisé au __UPDATED_AT__</span>
      <h1 style="margin:12px 0 6px;">__N1__ vs __N2__ : laquelle coûte le moins cher ?</h1>
      <p style="color:#94a3b8;margin-top:0;">Déplacez le curseur selon votre kilométrage annuel pour voir le vrai gagnant financier sur 1 an et 5 ans.</p>

      <div class="slider-box">
        <div style="display:flex;justify-content:space-between;margin-bottom:8px;font-size:0.9rem;">
          <span>Kilométrage annuel testé :</span>
          <strong id="km-val" style="color:#38bdf8;">15 000 km / an</strong>
        </div>
        <input type="range" id="km-slider" min="3000" max="45000" step="500" value="15000" />
      </div>

      <div class="duel-grid">
        <div class="car-box">
          <h2>__N1__</h2>
          <div style="font-size:0.84rem;color:#94a3b8;">__F1_LABEL__ • __C1__ __U1__</div>
          <div class="price-big" id="m1-month">— €/mois</div>
          <div class="line"><span>Énergie / an</span><strong id="m1-energy">— €</strong></div>
          <div class="line"><span>Fixes (assurance + entretien)</span><strong>__FX1__ €/an</strong></div>
          <div class="line"><span>Coût réel / km</span><strong id="m1-km">— €</strong></div>
          <p style="margin:12px 0 0;font-size:0.86rem;"><a href="/modeles/__S1__.html">Voir la fiche complète __N1__ →</a></p>
        </div>

        <div class="car-box">
          <h2>__N2__</h2>
          <div style="font-size:0.84rem;color:#94a3b8;">__F2_LABEL__ • __C2__ __U2__</div>
          <div class="price-big" id="m2-month">— €/mois</div>
          <div class="line"><span>Énergie / an</span><strong id="m2-energy">— €</strong></div>
          <div class="line"><span>Fixes (assurance + entretien)</span><strong>__FX2__ €/an</strong></div>
          <div class="line"><span>Coût réel / km</span><strong id="m2-km">— €</strong></div>
          <p style="margin:12px 0 0;font-size:0.86rem;"><a href="/modeles/__S2__.html">Voir la fiche complète __N2__ →</a></p>
        </div>
      </div>

      <div class="verdict" id="verdict">Calcul en cours...</div>

      <div style="text-align:center;">
        <a href="#affiliation-assurance" class="btn" rel="nofollow sponsored">Comparer l'assurance de ces deux modèles →</a>
      </div>
    </div>

    <div class="card">
      <h2 style="margin-top:0;font-size:1.1rem;">Autres duels populaires</h2>
      <div class="chips">__OTHER_DUELS__</div>
    </div>
  </div>

  <script>
    const M1 = { name: "__N1__", conso: __C1__, price: __P1__, fixed: __FX1__ };
    const M2 = { name: "__N2__", conso: __C2__, price: __P2__, fixed: __FX2__ };
    const slider = document.getElementById("km-slider");

    function updateDuel() {
      const km = parseInt(slider.value, 10);
      document.getElementById("km-val").textContent = km.toLocaleString("fr-FR") + " km / an";
      const e1 = (km / 100) * M1.conso * M1.price;
      const t1 = e1 + M1.fixed;
      const e2 = (km / 100) * M2.conso * M2.price;
      const t2 = e2 + M2.fixed;

      document.getElementById("m1-month").textContent = Math.round(t1 / 12).toLocaleString("fr-FR") + " €/mois";
      document.getElementById("m1-energy").textContent = Math.round(e1).toLocaleString("fr-FR") + " €";
      document.getElementById("m1-km").textContent = (t1 / km).toFixed(2) + " €";

      document.getElementById("m2-month").textContent = Math.round(t2 / 12).toLocaleString("fr-FR") + " €/mois";
      document.getElementById("m2-energy").textContent = Math.round(e2).toLocaleString("fr-FR") + " €";
      document.getElementById("m2-km").textContent = (t2 / km).toFixed(2) + " €";

      const diff = Math.round(Math.abs(t1 - t2));
      const winner = t1 < t2 ? M1.name : M2.name;
      const v = document.getElementById("verdict");
      if (diff < 20) {
        v.textContent = "Égalité quasi parfaite entre " + M1.name + " et " + M2.name + " à " + km.toLocaleString("fr-FR") + " km/an.";
      } else {
        v.textContent = "Gagnant budget : " + winner + " — économie de " + diff.toLocaleString("fr-FR") + " € / an (soit " + (diff * 5).toLocaleString("fr-FR") + " € sur 5 ans).";
      }
    }
    slider.addEventListener("input", updateDuel);
    updateDuel();
  </script>
</body>
</html>
"""

for s1, s2 in valid_duels:
    m1, m2 = models_by_slug[s1], models_by_slug[s2]
    dslug = f"{s1}-vs-{s2}"
    other_duels_html = "".join([
        f'<a class="chip" href="/duels/{a}-vs-{b}.html">{models_by_slug[a]["name"]} vs {models_by_slug[b]["name"]}</a>'
        for a, b in valid_duels if f"{a}-vs-{b}" != dslug
    ][:10])
    dhtml = (DUEL_TEMPLATE
        .replace("__DSLUG__", dslug)
        .replace("__UPDATED_AT__", today_fr)
        .replace("__TOTAL_MODELS__", str(total_models))
        .replace("__S1__", m1["slug"]).replace("__N1__", m1["name"]).replace("__C1__", str(m1["conso"]))
        .replace("__P1__", str(prices.get(m1["fuel"], 1.75))).replace("__FX1__", str(m1["fixed"]))
        .replace("__F1_LABEL__", FUEL_LABELS[m1["fuel"]]).replace("__U1__", FUEL_UNITS[m1["fuel"]])
        .replace("__S2__", m2["slug"]).replace("__N2__", m2["name"]).replace("__C2__", str(m2["conso"]))
        .replace("__P2__", str(prices.get(m2["fuel"], 1.75))).replace("__FX2__", str(m2["fixed"]))
        .replace("__F2_LABEL__", FUEL_LABELS[m2["fuel"]]).replace("__U2__", FUEL_UNITS[m2["fuel"]])
        .replace("__OTHER_DUELS__", other_duels_html)
    )
    with open(f"duels/{dslug}.html", "w", encoding="utf-8") as f:
        f.write(dhtml)

    sitemap_urls.append(
        f"  <url><loc>https://simulateur-auto.com/duels/{dslug}.html</loc><lastmod>{today_iso}</lastmod><changefreq>daily</changefreq><priority>0.85</priority></url>"
    )

# 5. Génération des 96 pages DÉPARTEMENTS (Radar Carburant + Top 3 stations moins chères)
DEPT_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Prix carburants __DNAME__ (__CODE__) aujourd'hui (2027) — Stations les moins chères</title>
  <meta name="description" content="Prix moyen du Gazole (__P_GAZOLE__ €), SP95-E10 (__P_E10__ €) et E85 (__P_E85__ €) dans le département __DNAME__ (__CODE__) au __UPDATED_AT__ et Top 3 des stations moins chères." />
  <link rel="canonical" href="https://simulateur-auto.com/carburant/__DSLUG__.html" />
  <link rel="manifest" href="/manifest.json" />
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>⛽</text></svg>" />
  <style>
    body { margin:0; background:#050811; color:#f8fafc; font-family:system-ui,-apple-system,sans-serif; line-height:1.6; padding:24px 16px; }
    .wrap { max-width:920px; margin:0 auto; }
    a { color:#38bdf8; text-decoration:none; }
    .topbar { display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:18px; font-size:0.9rem; }
    .card { background:rgba(15,23,42,0.88); border:1px solid rgba(148,163,184,0.18); border-radius:18px; padding:24px; margin-bottom:20px; }
    .badge { display:inline-block; background:rgba(34,197,94,0.14); border:1px solid rgba(34,197,94,0.35); color:#4ade80; font-size:0.82rem; font-weight:600; padding:4px 12px; border-radius:999px; }
    .grid5 { display:grid; grid-template-columns:repeat(5,1fr); gap:10px; margin-top:16px; }
    @media(max-width:740px) { .grid5 { grid-template-columns:repeat(2,1fr); } }
    .stat { background:#090e1a; padding:14px 10px; border-radius:12px; text-align:center; border:1px solid rgba(148,163,184,0.14); }
    .stat span { display:block; font-size:0.78rem; color:#94a3b8; }
    .stat strong { font-size:1.3rem; color:#38bdf8; }
    .fuel-block { margin-bottom:18px; }
    .fuel-block h3 { margin:0 0 8px; font-size:1.05rem; color:#38bdf8; }
    .st-row { display:flex; justify-content:space-between; align-items:center; gap:10px; background:#090e1a; border:1px solid rgba(148,163,184,0.14); padding:10px 14px; border-radius:10px; margin-bottom:6px; font-size:0.9rem; }
    .st-price { font-weight:800; color:#4ade80; font-size:1.02rem; white-space:nowrap; }
    .btn { display:inline-block; background:linear-gradient(135deg,#0284c7,#1d4ed8); color:#fff; font-weight:700; padding:12px 22px; border-radius:10px; margin-top:14px; }
    .chips { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
    .chip { background:#090e1a; border:1px solid rgba(148,163,184,0.18); padding:6px 11px; border-radius:8px; font-size:0.84rem; color:#f8fafc; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="topbar">
      <a href="/">← Cockpit SimulateurAuto.com</a>
      <a href="/carburant/">Tous les 96 départements →</a>
    </div>

    <div class="card">
      <span class="badge">● Relevé officiel du __UPDATED_AT__ • __COUNT__ stations analysées</span>
      <h1 style="margin:12px 0 6px;">Prix des carburants dans le __DNAME__ (__CODE__)</h1>
      <p style="color:#94a3b8;margin-top:0;">Moyennes départementales constatées aujourd'hui et classement des stations-service les moins chères.</p>

      <div class="grid5">
        <div class="stat"><span>Gazole</span><strong>__P_GAZOLE__ €</strong></div>
        <div class="stat"><span>SP95-E10</span><strong>__P_E10__ €</strong></div>
        <div class="stat"><span>SP95</span><strong>__P_SP95__ €</strong></div>
        <div class="stat"><span>SP98</span><strong>__P_SP98__ €</strong></div>
        <div class="stat"><span>E85</span><strong style="color:#4ade80;">__P_E85__ €</strong></div>
      </div>

      <div style="text-align:center;margin-top:16px;">
        <a href="/?dept=__CODE__" class="btn">Simuler mon budget auto avec les prix du __CODE__ →</a>
      </div>
    </div>

    <div class="card">
      <h2 style="margin-top:0;">Top 3 des stations les moins chères (__DNAME__)</h2>
      __TOP3_HTML__
    </div>

    <div class="card">
      <h2 style="margin-top:0;font-size:1.1rem;">Autres départements</h2>
      <div class="chips">__OTHER_DEPTS__</div>
    </div>
  </div>
</body>
</html>
"""

all_dept_items = list(departments_data.values())
for idx_d, d in enumerate(all_dept_items):
    blocks = []
    for fk, flabel in [("Gazole", "Diesel (Gazole)"), ("E10", "Essence SP95-E10"), ("E85", "Superéthanol E85"), ("SP98", "Essence SP98")]:
        st_rows = d["top3"].get(fk, [])
        if not st_rows:
            continue
        rows_html = "".join([
            f'<div class="st-row"><div><strong>#{i+1} {html.escape(s["v"])} ({html.escape(s["cp"])})</strong><br><span style="color:#94a3b8;font-size:0.82rem;">{html.escape(s["a"])}</span></div><div class="st-price">{s["p"]:.3f} €/L</div></div>'
            for i, s in enumerate(st_rows)
        ])
        blocks.append(f'<div class="fuel-block"><h3>{flabel}</h3>{rows_html}</div>')

    top3_section = "".join(blocks) if blocks else '<p style="color:#94a3b8;">Données détaillées des stations temporairement indisponibles aujourd\'hui. Moyennes nationales appliquées.</p>'
    neighbors = [all_dept_items[(idx_d + offset) % len(all_dept_items)] for offset in range(1, 13)]
    other_depts_html = "".join([f'<a class="chip" href="/carburant/{n["slug"]}.html">{n["name"]} ({n["code"]})</a>' for n in neighbors])

    dept_html = (DEPT_TEMPLATE
        .replace("__DNAME__", d["name"])
        .replace("__CODE__", d["code"])
        .replace("__DSLUG__", d["slug"])
        .replace("__UPDATED_AT__", today_fr)
        .replace("__COUNT__", str(d["count"]))
        .replace("__P_GAZOLE__", f"{d['prices']['Gazole']:.3f}")
        .replace("__P_E10__", f"{d['prices']['E10']:.3f}")
        .replace("__P_SP95__", f"{d['prices']['SP95']:.3f}")
        .replace("__P_SP98__", f"{d['prices']['SP98']:.3f}")
        .replace("__P_E85__", f"{d['prices']['E85']:.3f}")
        .replace("__TOP3_HTML__", top3_section)
        .replace("__OTHER_DEPTS__", other_depts_html)
    )
    with open(f"carburant/{d['slug']}.html", "w", encoding="utf-8") as f:
        f.write(dept_html)

    sitemap_urls.append(
        f"  <url><loc>https://simulateur-auto.com/carburant/{d['slug']}.html</loc><lastmod>{today_iso}</lastmod><changefreq>daily</changefreq><priority>0.75</priority></url>"
    )

# Index des 96 départements /carburant/index.html
dept_cards_html = "".join([
    f'<a class="dcard" href="/carburant/{d["slug"]}.html"><strong>{d["code"]} — {d["name"]}</strong><span>Gazole {d["prices"]["Gazole"]:.3f} € • E10 {d["prices"]["E10"]:.3f} € • E85 {d["prices"]["E85"]:.3f} €</span></a>'
    for d in all_dept_items
])

DEPT_INDEX_HTML = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Radar Prix Carburants par Département (2027) — SimulateurAuto.com</title>
  <meta name="description" content="Comparez les prix moyens du Gazole, SP95-E10 et E85 dans les 96 départements français au {today_fr} et trouvez les stations les moins chères." />
  <link rel="canonical" href="https://simulateur-auto.com/carburant/" />
  <link rel="manifest" href="/manifest.json" />
  <style>
    body {{ margin:0; background:#050811; color:#f8fafc; font-family:system-ui,-apple-system,sans-serif; padding:24px 16px; line-height:1.5; }}
    .wrap {{ max-width:1040px; margin:0 auto; }}
    a {{ color:#38bdf8; text-decoration:none; }}
    input {{ width:100%; box-sizing:border-box; padding:13px 15px; border-radius:12px; border:1px solid rgba(148,163,184,0.22); background:#0f172a; color:#fff; font-size:1rem; margin:16px 0; }}
    .grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }}
    @media(max-width:820px) {{ .grid {{ grid-template-columns:repeat(2,1fr); }} }}
    @media(max-width:540px) {{ .grid {{ grid-template-columns:1fr; }} }}
    .dcard {{ display:block; background:rgba(15,23,42,0.88); border:1px solid rgba(148,163,184,0.16); border-radius:12px; padding:14px; color:#f8fafc; }}
    .dcard:hover {{ border-color:#38bdf8; }}
    .dcard strong {{ display:block; font-size:1rem; margin-bottom:4px; }}
    .dcard span {{ font-size:0.82rem; color:#94a3b8; }}
  </style>
</head>
<body>
  <div class="wrap">
    <p><a href="/">← Retour au Cockpit SimulateurAuto.com</a></p>
    <h1 style="margin:8px 0 4px;">Radar Carburants : 96 Départements ({today_fr})</h1>
    <p style="color:#94a3b8;margin-top:0;">Cliquez sur votre département pour voir les stations les moins chères aujourd'hui.</p>
    <input type="text" id="dq" placeholder="Tapez un numéro ou nom de département (ex : 62, Nord, Paris, Lyon, 13...)" />
    <div class="grid" id="dgrid">{dept_cards_html}</div>
  </div>
  <script>
    const inp = document.getElementById("dq");
    const cards = Array.from(document.querySelectorAll(".dcard"));
    inp.addEventListener("input", () => {{
      const q = inp.value.trim().toLowerCase();
      cards.forEach(c => {{ c.style.display = c.textContent.toLowerCase().includes(q) ? "block" : "none"; }});
    }});
  </script>
</body>
</html>
"""
with open("carburant/index.html", "w", encoding="utf-8") as f:
    f.write(DEPT_INDEX_HTML)

# 6. Catalogue /modeles/index.html
cards_data = []
brands_set = sorted({m["brand"] for m in MODELS})
for m in MODELS:
    p = prices.get(m["fuel"], 1.75)
    month = round((((15000 / 100) * m["conso"] * p) + m["fixed"]) / 12)
    cards_data.append({
        "slug": m["slug"],
        "brand": m["brand"],
        "name": m["name"],
        "cat": m["cat"],
        "fuel": m["fuel"],
        "fuelLabel": FUEL_LABELS[m["fuel"]],
        "conso": m["conso"],
        "unit": FUEL_UNITS[m["fuel"]],
        "month": month
    })

brand_options_html = '<option value="ALL">Toutes les marques (' + str(len(brands_set)) + ')</option>' + "".join(
    [f'<option value="{b}">{b}</option>' for b in brands_set]
)

duels_cards_html = "".join([
    f'<a class="duel-link" href="/duels/{a}-vs-{b}.html"><span><strong>{models_by_slug[a]["name"]}</strong> vs <strong>{models_by_slug[b]["name"]}</strong></span> <span>→</span></a>'
    for a, b in valid_duels
])

CATALOG_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Catalogue complet (__TOTAL_MODELS__ modèles auto & Duels 2027) — SimulateurAuto.com</title>
  <meta name="description" content="Comparez le coût réel mensuel de __TOTAL_MODELS__ modèles sur 32 marques actualisé au __UPDATED_AT__." />
  <link rel="canonical" href="https://simulateur-auto.com/modeles/" />
  <link rel="manifest" href="/manifest.json" />
  <style>
    body { margin:0; background:#050811; color:#f8fafc; font-family:system-ui,-apple-system,sans-serif; padding:24px 16px; line-height:1.5; }
    .wrap { max-width:1060px; margin:0 auto; }
    a { color:#38bdf8; text-decoration:none; }
    .controls { display:grid; grid-template-columns:1.6fr 1fr 1fr; gap:10px; margin:16px 0; }
    @media(max-width:720px) { .controls { grid-template-columns:1fr; } }
    .search-bar, select { width:100%; box-sizing:border-box; padding:13px 14px; border-radius:12px; border:1px solid rgba(148,163,184,0.22); background:#0f172a; color:#fff; font-size:0.96rem; }
    .filters { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px; }
    .fbtn { background:#0f172a; color:#cbd5e1; border:1px solid rgba(148,163,184,0.2); padding:8px 14px; border-radius:9px; cursor:pointer; font-size:0.86rem; }
    .fbtn.active { background:rgba(56,189,248,0.16); border-color:#38bdf8; color:#38bdf8; font-weight:700; }
    .count { color:#94a3b8; font-size:0.88rem; margin-bottom:14px; }
    .grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
    @media(max-width:860px) { .grid { grid-template-columns:repeat(2,1fr); } }
    @media(max-width:540px) { .grid { grid-template-columns:1fr; } }
    .mcard { display:block; background:rgba(15,23,42,0.88); border:1px solid rgba(148,163,184,0.16); border-radius:14px; padding:16px; color:#f8fafc; transition:0.2s; }
    .mcard:hover { border-color:#38bdf8; transform:translateY(-2px); }
    .mcard h3 { margin:0 0 4px; font-size:1.03rem; }
    .meta { font-size:0.81rem; color:#94a3b8; }
    .budget { margin-top:10px; font-size:1.25rem; font-weight:800; color:#4ade80; }
    .duel-list { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:14px; }
    @media(max-width:650px) { .duel-list { grid-template-columns:1fr; } }
    .duel-link { display:flex; justify-content:space-between; background:rgba(15,23,42,0.88); border:1px solid rgba(148,163,184,0.16); padding:13px 16px; border-radius:11px; color:#f8fafc; font-size:0.9rem; }
    .duel-link:hover { border-color:#38bdf8; }
  </style>
</head>
<body>
  <div class="wrap">
    <p><a href="/">← Retour au Cockpit SimulateurAuto.com</a></p>
    <h1 style="margin:8px 0 4px;">Catalogue complet : __TOTAL_MODELS__ modèles & Duels (2027)</h1>
    <p style="color:#94a3b8;margin-top:0;">Budgets mensuels calculés pour 15 000 km/an avec les prix officiels du __UPDATED_AT__.</p>

    <div class="controls">
      <input type="text" id="q" class="search-bar" placeholder="Rechercher un modèle ou une marque (ex : 208, Golf, BMW, BYD...)" />
      <select id="brand-filter">__BRAND_OPTIONS__</select>
      <select id="cat-filter">
        <option value="ALL">Toutes les catégories</option>
        <option value="Citadine">Citadine</option>
        <option value="Compacte">Compacte</option>
        <option value="SUV">SUV</option>
        <option value="Berline">Berline</option>
        <option value="Familiale">Familiale</option>
        <option value="Électrique">100 % Électrique</option>
        <option value="Sportive">Sportive</option>
      </select>
    </div>

    <div class="filters">
      <button class="fbtn active" data-f="ALL">Toutes énergies</button>
      <button class="fbtn" data-f="E10">Essence / Hybride</button>
      <button class="fbtn" data-f="Gazole">Diesel</button>
      <button class="fbtn" data-f="Electrique_kWh">100 % Électrique</button>
      <button class="fbtn" data-f="E85">E85 Flexifuel</button>
      <button class="fbtn" data-f="SP98">SP98 / Sport</button>
    </div>

    <div class="count" id="count-txt"></div>
    <div id="list" class="grid"></div>

    <h2 style="margin-top:40px;">Les 20 Duels les plus comparés</h2>
    <div class="duel-list">__DUELS_HTML__</div>
  </div>

  <script>
    const DATA = __CARDS_JSON__;
    let currentFuel = "ALL";
    const qInput = document.getElementById("q");
    const brandSel = document.getElementById("brand-filter");
    const catSel = document.getElementById("cat-filter");
    const list = document.getElementById("list");
    const countTxt = document.getElementById("count-txt");

    function render() {
      const q = qInput.value.trim().toLowerCase();
      const b = brandSel.value;
      const c = catSel.value;
      const filtered = DATA.filter(m => {
        const matchFuel = currentFuel === "ALL" || m.fuel === currentFuel;
        const matchBrand = b === "ALL" || m.brand === b;
        const matchCat = c === "ALL" || m.cat === c;
        const matchText = !q || m.name.toLowerCase().includes(q) || m.brand.toLowerCase().includes(q) || m.cat.toLowerCase().includes(q) || m.fuelLabel.toLowerCase().includes(q);
        return matchFuel && matchBrand && matchCat && matchText;
      });
      countTxt.textContent = filtered.length + " modèle(s) affiché(s) sur " + DATA.length;
      list.innerHTML = filtered.map(m => `
        <a class="mcard" href="/modeles/${m.slug}.html">
          <h3>${m.name}</h3>
          <div class="meta">${m.brand} • ${m.cat} • ${m.fuelLabel} • ${m.conso} ${m.unit}</div>
          <div class="budget">${m.month} € <span style="font-size:0.8rem;color:#94a3b8;font-weight:500;">/ mois</span></div>
        </a>
      `).join("") || '<p style="color:#94a3b8;">Aucun modèle trouvé.</p>';
    }

    document.querySelectorAll(".fbtn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".fbtn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentFuel = btn.dataset.f;
        render();
      });
    });
    qInput.addEventListener("input", render);
    brandSel.addEventListener("change", render);
    catSel.addEventListener("change", render);
    render();
  </script>
</body>
</html>
"""

with open("modeles/index.html", "w", encoding="utf-8") as f:
    f.write(
        CATALOG_HTML
        .replace("__TOTAL_MODELS__", str(total_models))
        .replace("__UPDATED_AT__", today_fr)
        .replace("__BRAND_OPTIONS__", brand_options_html)
        .replace("__CARDS_JSON__", json.dumps(cards_data, ensure_ascii=False))
        .replace("__DUELS_HTML__", duels_cards_html)
    )

# 7. Mise à jour de sitemap.xml
sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(sitemap_urls) + "\n</urlset>\n"
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_xml)

print(f"Mise à jour V3 Élite réussie : {total_models} modèles + {len(valid_duels)} duels + {len(all_dept_items)} départements + sitemap ({len(sitemap_urls)} URLs)")
