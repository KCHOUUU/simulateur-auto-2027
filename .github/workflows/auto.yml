import json
import os
import datetime
import urllib.request
import zipfile
import io
import xml.etree.ElementTree as ET

# 1. Récupération des prix officiels (avec sécurité anti-panne)
prices = {
    "Gazole": 1.68,
    "SP95": 1.79,
    "E10": 1.75,
    "SP98": 1.85,
    "E85": 0.89,
    "Electrique_kWh": 0.2516,
    "updated_at": datetime.date.today().strftime("%d/%m/%Y")
}

try:
    url = "https://donnees.roulez-eco.fr/opendata/instantane"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        z = zipfile.ZipFile(io.BytesIO(resp.read()))
        xml_name = z.namelist()[0]
        root = ET.fromstring(z.read(xml_name))
        totals = {"Gazole": [], "SP95": [], "E10": [], "SP98": [], "E85": []}
        for pdv in root.findall("pdv"):
            for p in pdv.findall("prix"):
                nom = p.attrib.get("nom")
                val = p.attrib.get("valeur")
                if nom in totals and val:
                    v = float(val)
                    if 0.4 < v < 3.5:
                        totals[nom].append(v)
        for k, vals in totals.items():
            if len(vals) > 50:
                prices[k] = round(sum(vals) / len(vals), 3)
except Exception as e:
    print("Fallback prix utilisé:", e)

with open("prices.json", "w", encoding="utf-8") as f:
    json.dump(prices, f, ensure_ascii=False, indent=2)

# 2. Base des 12 modèles les plus recherchés en France (SEO Programmatique)
MODELS = [
    {"slug": "peugeot-208", "name": "Peugeot 208", "fuel": "E10", "conso": 5.4, "fixed": 1050, "e85_cost": 890},
    {"slug": "renault-clio-5", "name": "Renault Clio 5", "fuel": "Gazole", "conso": 4.6, "fixed": 1120, "e85_cost": 0},
    {"slug": "dacia-sandero", "name": "Dacia Sandero", "fuel": "E10", "conso": 5.6, "fixed": 920, "e85_cost": 850},
    {"slug": "tesla-model-3", "name": "Tesla Model 3", "fuel": "Electrique_kWh", "conso": 14.8, "fixed": 950, "e85_cost": 0},
    {"slug": "toyota-yaris-hybride", "name": "Toyota Yaris Hybride", "fuel": "E10", "conso": 4.2, "fixed": 980, "e85_cost": 950},
    {"slug": "peugeot-3008", "name": "Peugeot 3008", "fuel": "Gazole", "conso": 5.8, "fixed": 1320, "e85_cost": 0},
    {"slug": "citroen-c3", "name": "Citroën C3", "fuel": "E10", "conso": 5.5, "fixed": 960, "e85_cost": 850},
    {"slug": "volkswagen-golf-8", "name": "Volkswagen Golf 8", "fuel": "E10", "conso": 5.9, "fixed": 1280, "e85_cost": 950},
    {"slug": "renault-captur", "name": "Renault Captur", "fuel": "E10", "conso": 6.1, "fixed": 1140, "e85_cost": 890},
    {"slug": "dacia-duster", "name": "Dacia Duster", "fuel": "Gazole", "conso": 5.3, "fixed": 1080, "e85_cost": 0},
    {"slug": "mg4-electrique", "name": "MG4 Électrique", "fuel": "Electrique_kWh", "conso": 16.0, "fixed": 880, "e85_cost": 0},
    {"slug": "fiat-500-electrique", "name": "Fiat 500 Électrique", "fuel": "Electrique_kWh", "conso": 13.8, "fixed": 840, "e85_cost": 0},
]

os.makedirs("modeles", exist_ok=True)
today_iso = datetime.date.today().isoformat()
sitemap_urls = [
    f"  <url><loc>https://simulateur-auto.com/</loc><lastmod>{today_iso}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>",
    f"  <url><loc>https://simulateur-auto.com/mentions-legales.html</loc><changefreq>yearly</changefreq><priority>0.3</priority></url>"
]

# 3. Génération automatique de chaque page modèle avec prix du jour + Calculateur ROI
for m in MODELS:
    unit_price = prices.get(m["fuel"], 1.75)
    energy_15k = round((15000 / 100) * m["conso"] * unit_price)
    total_year = energy_15k + m["fixed"]
    total_month = round(total_year / 12)
    per_km = round(total_year / 15000, 2)

    # Calcul rentabilité E85 si essence
    roi_block = ""
    if m["e85_cost"] > 0:
        e85_energy = round((15000 / 100) * (m["conso"] * 1.18) * prices["E85"])
        eco_an = max(1, energy_15k - e85_energy)
        mois_roi = round((m["e85_cost"] / eco_an) * 12)
        roi_block = f"""
        <div class="card">
          <h2>Rentabilité boîtier Superéthanol E85 sur {m['name']}</h2>
          <p style="color:#94a3b8;">Avec un boîtier homologué estimé à <strong>{m['e85_cost']} €</strong> et l'E85 à <strong>{prices['E85']} €/L</strong> aujourd'hui :</p>
          <div class="grid">
            <div class="stat"><span>Économie carburant / an</span><strong style="color:#4ade80;">+{eco_an} €</strong></div>
            <div class="stat"><span>Rentabilisé en</span><strong>{mois_roi} mois</strong></div>
            <div class="stat"><span>Gain net sur 5 ans</span><strong style="color:#4ade80;">+{(eco_an*5) - m['e85_cost']} €</strong></div>
          </div>
        </div>"""

    other_links = " • ".join([f'<a href="/modeles/{o["slug"]}.html">{o["name"]}</a>' for o in MODELS if o["slug"] != m["slug"]][:6])

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Coût réel {m['name']} (2027) — Budget carburant, assurance & entretien</title>
  <meta name="description" content="Combien coûte vraiment une {m['name']} en 2027 ? Budget mensuel ({total_month} €/mois), coût au kilomètre ({per_km} €/km) actualisé au {prices['updated_at']}." />
  <link rel="canonical" href="https://simulateur-auto.com/modeles/{m['slug']}.html" />
  <link rel="manifest" href="/manifest.json" />
  <style>
    body {{ margin:0; background:#050811; color:#f8fafc; font-family:system-ui,-apple-system,sans-serif; line-height:1.6; padding:24px 16px; }}
    .wrap {{ max-width:860px; margin:0 auto; }}
    a {{ color:#38bdf8; text-decoration:none; }}
    .card {{ background:rgba(15,23,42,0.85); border:1px solid rgba(148,163,184,0.18); border-radius:16px; padding:24px; margin-bottom:20px; }}
    .grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-top:16px; }}
    @media(max-width:650px) {{ .grid {{ grid-template-columns:1fr; }} }}
    .stat {{ background:#090e1a; padding:16px; border-radius:12px; text-align:center; border:1px solid rgba(148,163,184,0.14); }}
    .stat span {{ display:block; font-size:0.8rem; color:#94a3b8; }}
    .stat strong {{ font-size:1.45rem; color:#38bdf8; }}
    .btn {{ display:inline-block; background:linear-gradient(135deg,#0284c7,#1d4ed8); color:#fff; font-weight:700; padding:12px 24px; border-radius:10px; margin-top:14px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <p><a href="/">← Retour au Cockpit SimulateurAuto.com</a></p>
    <div class="card">
      <span style="color:#4ade80;font-size:0.85rem;font-weight:600;">● Prix officiels à jour au {prices['updated_at']}</span>
      <h1 style="margin:10px 0 8px;">Coût réel d'une {m['name']} (15 000 km/an)</h1>
      <p style="color:#94a3b8;">Estimation basée sur une consommation moyenne de <strong>{m['conso']}</strong> ({m['fuel']}) et <strong>{m['fixed']} €/an</strong> d'assurance + entretien.</p>
      <div class="grid">
        <div class="stat"><span>Budget total / mois</span><strong style="color:#4ade80;">{total_month} €</strong></div>
        <div class="stat"><span>Énergie / an</span><strong>{energy_15k} €</strong></div>
        <div class="stat"><span>Coût réel / km</span><strong>{per_km} €</strong></div>
      </div>
      <div style="text-align:center;margin-top:20px;">
        <a href="#affiliation-assurance" class="btn" rel="nofollow sponsored">Réduire l'assurance de ma {m['name']} →</a>
      </div>
    </div>
    {roi_block}
    <div class="card">
      <h2 style="margin-top:0;font-size:1.1rem;">Comparer d'autres modèles populaires</h2>
      <p style="font-size:0.9rem;line-height:1.9;">{other_links}</p>
      <p style="margin-bottom:0;"><a href="/">Personnaliser mon kilométrage exact sur le simulateur complet →</a></p>
    </div>
  </div>
</body>
</html>"""

    with open(f"modeles/{m['slug']}.html", "w", encoding="utf-8") as f:
        f.write(html)

    sitemap_urls.append(
        f"  <url><loc>https://simulateur-auto.com/modeles/{m['slug']}.html</loc><lastmod>{today_iso}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>"
    )

# 4. Mise à jour automatique de sitemap.xml
sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(sitemap_urls) + "\n</urlset>\n"
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_xml)

print("Mise à jour complète réussie : prices.json + 12 pages modèles + sitemap.xml")
