import json
import urllib.request
import zipfile
import io
import xml.etree.ElementTree as ET
from datetime import datetime

URL_GOUV = "https://donnees.roulez-eco.fr/opendata/instantane"

def fetch_fuel_averages():
    try:
        req = urllib.request.Request(URL_GOUV, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            zip_bytes = resp.read()
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            xml_name = zf.namelist()[0]
            with zf.open(xml_name) as f:
                tree = ET.parse(f)
                root = tree.getroot()

        totals = {"Gazole": [], "SP95": [], "E10": [], "SP98": [], "E85": []}
        for pdv in root.findall("pdv"):
            for prix in pdv.findall("prix"):
                nom = prix.attrib.get("nom")
                val = prix.attrib.get("valeur")
                if nom in totals and val:
                    p = float(val)
                    if 0.5 < p < 3.5:
                        totals[nom].append(p)

        averages = {
            k: round(sum(v) / len(v), 3) if v else 1.75
            for k, v in totals.items()
        }
    except Exception:
        averages = {"Gazole": 1.68, "SP95": 1.79, "E10": 1.75, "SP98": 1.85, "E85": 0.89}

    averages["Electrique_kWh"] = 0.2516
    averages["updated_at"] = datetime.now().strftime("%d/%m/%Y")
    return averages

if __name__ == "__main__":
    data = fetch_fuel_averages()
    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
