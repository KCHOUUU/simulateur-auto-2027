import json
import os
import datetime
import urllib.request
import zipfile
import io
import xml.etree.ElementTree as ET

# 1. Récupération des prix officiels (avec fallback anti-panne)
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

# 2. Base de 36 modèles majeurs du marché français
MODELS = [
    {"slug": "peugeot-208", "name": "Peugeot 208", "fuel": "E10", "conso": 5.4, "fixed": 1050, "e85_cost": 890, "cat": "Citadine"},
    {"slug": "renault-clio-5", "name": "Renault Clio 5", "fuel": "Gazole", "conso": 4.6, "fixed": 1120, "e85_cost": 0, "cat": "Citadine"},
    {"slug": "dacia-sandero", "name": "Dacia Sandero", "fuel": "E10", "conso": 5.6, "fixed": 920, "e85_cost": 850, "cat": "Citadine"},
    {"slug": "citroen-c3", "name": "Citroën C3", "fuel": "E10", "conso": 5.5, "fixed": 960, "e85_cost": 850, "cat": "Citadine"},
    {"slug": "toyota-yaris-hybride", "name": "Toyota Yaris Hybride", "fuel": "E10", "conso": 4.2, "fixed": 980, "e85_cost": 950, "cat": "Citadine"},
    {"slug": "volkswagen-polo", "name": "Volkswagen Polo", "fuel": "E10", "conso": 5.6, "fixed": 1080, "e85_cost": 920, "cat": "Citadine"},
    {"slug": "renault-twingo", "name": "Renault Twingo", "fuel": "E10", "conso": 5.1, "fixed": 860, "e85_cost": 790, "cat": "Citadine"},
    {"slug": "fiat-500-electrique", "name": "Fiat 500 Électrique", "fuel": "Electrique_kWh", "conso": 13.8, "fixed": 840, "e85_cost": 0, "cat": "Électrique"},
    {"slug": "dacia-spring", "name": "Dacia Spring", "fuel": "Electrique_kWh", "conso": 13.2, "fixed": 760, "e85_cost": 0, "cat": "Électrique"},
    {"slug": "peugeot-2008", "name": "Peugeot 2008", "fuel": "E10", "conso": 6.0, "fixed": 1160, "e85_cost": 890, "cat": "SUV"},
    {"slug": "renault-captur", "name": "Renault Captur", "fuel": "E10", "conso": 6.1, "fixed": 1140, "e85_cost": 890, "cat": "SUV"},
    {"slug": "dacia-duster", "name": "Dacia Duster", "fuel": "Gazole", "conso": 5.3, "fixed": 1080, "e85_cost": 0, "cat": "SUV"},
    {"slug": "peugeot-3008", "name": "Peugeot 3008", "fuel": "Gazole", "conso": 5.8, "fixed": 1320, "e85_cost": 0, "cat": "SUV"},
    {"slug": "renault-austral", "name": "Renault Austral Hybride", "fuel": "E10", "conso": 5.2, "fixed": 1290, "e85_cost": 0, "cat": "SUV"},
    {"slug": "citroen-c5-aircross", "name": "Citroën C5 Aircross", "fuel": "Gazole", "conso": 5.7, "fixed": 1280, "e85_cost": 0, "cat": "SUV"},
    {"slug": "volkswagen-t-roc", "name": "Volkswagen T-Roc", "fuel": "E10", "conso": 6.4, "fixed": 1250, "e85_cost": 950, "cat": "SUV"},
    {"slug": "volkswagen-tiguan", "name": "Volkswagen Tiguan", "fuel": "Gazole", "conso": 6.0, "fixed": 1390, "e85_cost": 0, "cat": "SUV"},
    {"slug": "toyota-c-hr", "name": "Toyota C-HR Hybride", "fuel": "E10", "conso": 4.9, "fixed": 1150, "e85_cost": 950, "cat": "SUV"},
    {"slug": "toyota-rav4", "name": "Toyota RAV4 Hybride", "fuel": "E10", "conso": 5.8, "fixed": 1340, "e85_cost": 980, "cat": "SUV"},
    {"slug": "hyundai-tucson", "name": "Hyundai Tucson Hybride", "fuel": "E10", "conso": 6.1, "fixed": 1290, "e85_cost": 950, "cat": "SUV"},
    {"slug": "kia-sportage", "name": "Kia Sportage Hybride", "fuel": "E10", "conso": 6.2, "fixed": 1270, "e85_cost": 950, "cat": "SUV"},
    {"slug": "nissan-qashqai", "name": "Nissan Qashqai", "fuel": "E10", "conso": 6.3, "fixed": 1220, "e85_cost": 920, "cat": "SUV"},
    {"slug": "ford-puma-e85", "name": "Ford Puma Flexifuel E85", "fuel": "E85", "conso": 7.1, "fixed": 1120, "e85_cost": 0, "cat": "SUV"},
    {"slug": "dacia-jogger", "name": "Dacia Jogger", "fuel": "E10", "conso": 6.0, "fixed": 1020, "e85_cost": 890, "cat": "Familiale"},
    {"slug": "peugeot-5008", "name": "Peugeot 5008", "fuel": "Gazole", "conso": 6.1, "fixed": 1380, "e85_cost": 0, "cat": "Familiale"},
    {"slug": "peugeot-308", "name": "Peugeot 308", "fuel": "E10", "conso": 5.8, "fixed": 1190, "e85_cost": 920, "cat": "Compacte"},
    {"slug": "volkswagen-golf-8", "name": "Volkswagen Golf 8", "fuel": "E10", "conso": 5.9, "fixed": 1280, "e85_cost": 950, "cat": "Compacte"},
    {"slug": "toyota-corolla-hybride", "name": "Toyota Corolla Hybride", "fuel": "E10", "conso": 4.6, "fixed": 1090, "e85_cost": 950, "cat": "Compacte"},
    {"slug": "citroen-c4", "name": "Citroën C4", "fuel": "E10", "conso": 5.8, "fixed": 1120, "e85_cost": 890, "cat": "Compacte"},
    {"slug": "audi-a3", "name": "Audi A3 Sportback", "fuel": "E10", "conso": 6.1, "fixed": 1460, "e85_cost": 990, "cat": "Compacte"},
    {"slug": "bmw-serie-1", "name": "BMW Série 1", "fuel": "E10", "conso": 6.3, "fixed": 1520, "e85_cost": 990, "cat": "Compacte"},
    {"slug": "mercedes-classe-a", "name": "Mercedes Classe A", "fuel": "E10", "conso": 6.2, "fixed": 1550, "e85_cost": 990, "cat": "Compacte"},
    {"slug": "tesla-model-3", "name": "Tesla Model 3", "fuel": "Electrique_kWh", "conso": 14.8, "fixed": 950, "e85_cost": 0, "cat": "Électrique"},
    {"slug": "tesla-model-y", "name": "Tesla Model Y", "fuel": "Electrique_kWh", "conso": 16.5, "fixed": 1050, "e85_cost": 0, "cat": "Électrique"},
    {"slug": "mg4-electrique", "name": "MG4 Électrique", "fuel": "Electrique_kWh", "conso": 16.0, "fixed": 880, "e85_cost": 0, "cat": "Électrique"},
    {"slug": "renault-megane-e-tech", "name": "Renault Mégane E-Tech", "fuel": "Electrique_kWh", "conso": 15.8, "fixed": 930, "e85_cost": 0, "cat": "Électrique"}
]

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
    ("tesla-model-y", "peugeot-3008")
]

# Export JSON pour la barre de recherche du cockpit d'accueil
with open("models.json", "w", encoding="utf-8") as f:
    json.dump(MODELS, f, ensure_ascii=False, indent=2)

os.makedirs("modeles", exist_ok=True)
os.makedirs("duels", exist_ok=True)

models_by_slug = {m["slug"]: m for m in MODELS}
today_iso = datetime.date.today().isoformat()

sitemap_urls = [
    f"  <url><loc>https://simulateur-auto.com/</loc><lastmod>{today_iso}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>",
    f"  <url><loc>https://simulateur-auto.com/modeles/</loc><lastmod>{today_iso}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>",
    f"  <url><loc>https://simulateur-auto.com/mentions-legales.html</loc><changefreq>yearly</changefreq><priority>0.3</priority></url>"
]

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
      <a href="/modeles/">Tous les 36 modèles →</a>
    </div>

    <div class="card">
      <span class="badge">● Prix officiels à jour au __UPDATED_AT__ (__UNIT_PRICE__ __PRICE_UNIT__)</span>
      <h1 style="margin:12px 0 8px;">Coût réel d'une __NAME__ en 2027</h1>
      <p style="color:#94a3b8;margin-top:0;">Catégorie <strong>__CAT__</strong> • Motorisation <strong>__FUEL_LABEL__</strong> • Conso moyenne <strong>__CONSO__ __CONSO_UNIT__</strong> • Frais fixes estimés <strong>__FIXED__ €/an</strong> (assurance + entretien).</p>

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
        <a id="cockpit-link" href="/?fuel=__FUEL_KEY__&conso=__CONSO__&fixed=__FIXED__&km=15000" class="btn-sec">Personnaliser dans le cockpit →</a>
      </div>
    </div>

    __ROI_BLOCK__
    __DUELS_BLOCK__

    <div class="card">
      <h2 style="margin-top:0;font-size:1.1rem;">Autres modèles de la catégorie __CAT__ & populaires</h2>
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

# 3. Génération des 36 pages modèles interactives
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

    # Liens vers les duels incluant ce modèle
    related_duels = []
    for s1, s2 in DUELS:
        if m["slug"] in (s1, s2):
            m1, m2 = models_by_slug[s1], models_by_slug[s2]
            related_duels.append(f'<a class="chip" href="/duels/{s1}-vs-{s2}.html">Duel : {m1["name"]} vs {m2["name"]} →</a>')
    duels_block = ""
    if related_duels:
        duels_block = f"""
    <div class="card">
      <h2 style="margin-top:0;font-size:1.1rem;">Duels comparatifs avec la {m['name']}</h2>
      <div class="chips">{''.join(related_duels)}</div>
    </div>"""

    same_cat = [o for o in MODELS if o["slug"] != m["slug"] and o["cat"] == m["cat"]]
    others = same_cat + [o for o in MODELS if o["slug"] != m["slug"] and o["cat"] != m["cat"]]
    other_links = "".join([f'<a class="chip" href="/modeles/{o["slug"]}.html">{o["name"]}</a>' for o in others[:8]])

    html = (MODEL_TEMPLATE
        .replace("__NAME__", m["name"])
        .replace("__SLUG__", m["slug"])
        .replace("__CAT__", m["cat"])
        .replace("__FUEL_KEY__", m["fuel"])
        .replace("__FUEL_LABEL__", FUEL_LABELS[m["fuel"]])
        .replace("__CONSO__", str(m["conso"]))
        .replace("__CONSO_UNIT__", FUEL_UNITS[m["fuel"]])
        .replace("__FIXED__", str(m["fixed"]))
        .replace("__UNIT_PRICE__", str(unit_price))
        .replace("__PRICE_UNIT__", price_unit)
        .replace("__UPDATED_AT__", prices["updated_at"])
        .replace("__TOTAL_MONTH__", str(total_month))
        .replace("__ENERGY_15K__", str(energy_15k))
        .replace("__PER_KM__", f"{per_km:.2f}")
        .replace("__E85_COST__", str(m["e85_cost"]))
        .replace("__E85_PRICE__", str(prices["E85"]))
        .replace("__ROI_BLOCK__", roi_block)
        .replace("__DUELS_BLOCK__", duels_block)
        .replace("__OTHER_LINKS__", other_links)
    )

    with open(f"modeles/{m['slug']}.html", "w", encoding="utf-8") as f:
        f.write(html)

    sitemap_urls.append(
        f"  <url><loc>https://simulateur-auto.com/modeles/{m['slug']}.html</loc><lastmod>{today_iso}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>"
    )

# 4. Génération des 10 pages DUELS interactives
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
      <a href="/modeles/">Catalogue des 36 modèles →</a>
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

for s1, s2 in DUELS:
    m1, m2 = models_by_slug[s1], models_by_slug[s2]
    dslug = f"{s1}-vs-{s2}"
    other_duels_html = "".join([
        f'<a class="chip" href="/duels/{a}-vs-{b}.html">{models_by_slug[a]["name"]} vs {models_by_slug[b]["name"]}</a>'
        for a, b in DUELS if f"{a}-vs-{b}" != dslug
    ])
    dhtml = (DUEL_TEMPLATE
        .replace("__DSLUG__", dslug)
        .replace("__UPDATED_AT__", prices["updated_at"])
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

# 5. Génération du Catalogue interactif /modeles/index.html
cards_data = []
for m in MODELS:
    p = prices.get(m["fuel"], 1.75)
    month = round((((15000 / 100) * m["conso"] * p) + m["fixed"]) / 12)
    cards_data.append({
        "slug": m["slug"],
        "name": m["name"],
        "cat": m["cat"],
        "fuel": m["fuel"],
        "fuelLabel": FUEL_LABELS[m["fuel"]],
        "conso": m["conso"],
        "unit": FUEL_UNITS[m["fuel"]],
        "month": month
    })

duels_cards_html = "".join([
    f'<a class="duel-link" href="/duels/{a}-vs-{b}.html"><strong>{models_by_slug[a]["name"]}</strong> vs <strong>{models_by_slug[b]["name"]}</strong> <span>→</span></a>'
    for a, b in DUELS
])

CATALOG_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Catalogue des 36 modèles auto & Duels (2027) — SimulateurAuto.com</title>
  <meta name="description" content="Recherchez le coût réel mensuel de 36 modèles populaires (Peugeot, Renault, Dacia, Tesla, Toyota, Audi, BMW) actualisé au __UPDATED_AT__." />
  <link rel="canonical" href="https://simulateur-auto.com/modeles/" />
  <link rel="manifest" href="/manifest.json" />
  <style>
    body { margin:0; background:#050811; color:#f8fafc; font-family:system-ui,-apple-system,sans-serif; padding:24px 16px; line-height:1.5; }
    .wrap { max-width:1020px; margin:0 auto; }
    a { color:#38bdf8; text-decoration:none; }
    .search-bar { width:100%; box-sizing:border-box; padding:14px 16px; border-radius:12px; border:1px solid rgba(148,163,184,0.22); background:#0f172a; color:#fff; font-size:1rem; margin:16px 0; }
    .filters { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px; }
    .fbtn { background:#0f172a; color:#cbd5e1; border:1px solid rgba(148,163,184,0.2); padding:8px 14px; border-radius:9px; cursor:pointer; font-size:0.86rem; }
    .fbtn.active { background:rgba(56,189,248,0.16); border-color:#38bdf8; color:#38bdf8; font-weight:700; }
    .grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }
    @media(max-width:820px) { .grid { grid-template-columns:repeat(2,1fr); } }
    @media(max-width:540px) { .grid { grid-template-columns:1fr; } }
    .mcard { display:block; background:rgba(15,23,42,0.88); border:1px solid rgba(148,163,184,0.16); border-radius:14px; padding:16px; color:#f8fafc; transition:0.2s; }
    .mcard:hover { border-color:#38bdf8; transform:translateY(-2px); }
    .mcard h3 { margin:0 0 4px; font-size:1.05rem; }
    .meta { font-size:0.82rem; color:#94a3b8; }
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
    <h1 style="margin:8px 0 4px;">Catalogue des 36 modèles & Duels (2027)</h1>
    <p style="color:#94a3b8;margin-top:0;">Budgets mensuels calculés pour 15 000 km/an avec les prix officiels du __UPDATED_AT__.</p>

    <input type="text" id="q" class="search-bar" placeholder="Rechercher une voiture (ex : 208, Clio, Tesla, Audi, SUV...)" />
    <div class="filters">
      <button class="fbtn active" data-f="ALL">Tous (36)</button>
      <button class="fbtn" data-f="E10">Essence / Hybride</button>
      <button class="fbtn" data-f="Gazole">Diesel</button>
      <button class="fbtn" data-f="Electrique_kWh">100 % Électrique</button>
      <button class="fbtn" data-f="E85">E85</button>
    </div>

    <div id="list" class="grid"></div>

    <h2 style="margin-top:38px;">Les 10 Duels les plus comparés</h2>
    <div class="duel-list">__DUELS_HTML__</div>
  </div>

  <script>
    const DATA = __CARDS_JSON__;
    let currentFuel = "ALL";
    const qInput = document.getElementById("q");
    const list = document.getElementById("list");

    function render() {
      const q = qInput.value.trim().toLowerCase();
      const filtered = DATA.filter(m => {
        const matchFuel = currentFuel === "ALL" || m.fuel === currentFuel;
        const matchText = !q || m.name.toLowerCase().includes(q) || m.cat.toLowerCase().includes(q) || m.fuelLabel.toLowerCase().includes(q);
        return matchFuel && matchText;
      });
      list.innerHTML = filtered.map(m => `
        <a class="mcard" href="/modeles/${m.slug}.html">
          <h3>${m.name}</h3>
          <div class="meta">${m.cat} • ${m.fuelLabel} • ${m.conso} ${m.unit}</div>
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
    render();
  </script>
</body>
</html>
"""

with open("modeles/index.html", "w", encoding="utf-8") as f:
    f.write(
        CATALOG_HTML
        .replace("__UPDATED_AT__", prices["updated_at"])
        .replace("__CARDS_JSON__", json.dumps(cards_data, ensure_ascii=False))
        .replace("__DUELS_HTML__", duels_cards_html)
    )

# 6. Mise à jour automatique de sitemap.xml (49 URLs)
sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(sitemap_urls) + "\n</urlset>\n"
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap_xml)

print(f"Mise à jour V2 réussie : prices.json + models.json + {len(MODELS)} fiches + {len(DUELS)} duels + catalogue + sitemap.xml")
