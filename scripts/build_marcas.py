"""
Gera assets/data/marcas.json, database/marcas.json e m4rcas.html completo com:
- Barra de busca grande centralizada no topo da parte principal
- Sub-abas estilizadas (fundo preto, borda verde, fonte verde estilizada):
  Catálogo 3xN | Quiz Gringa -> BR | Coleções & Fit Lab
- Filtro por categoria em caixa preta com borda verde e fonte verde
- Grid 3xN original de imagens clicáveis com mix-blend-mode no fundo (sem botão +INFO)
"""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TXT_PATH = ROOT / "database" / "marcas.txt"
IMG_DIR = ROOT / "assets" / "img" / "marcas"
DATA_DIR = ROOT / "assets" / "data"
UNLINKED_DIR = ROOT / "database" / "imagens_sem_link"
PRICE_PATH = ROOT / "database" / "brand_prices.json"
LOCATION_PATH = ROOT / "database" / "brand_locations.json"
ASSET_VER = "20261126g"

MAPPING: dict[str, tuple[str, str, str]] = {
    "1of1exclusivist": ("1of1.jpg", "1of1 Exclusivist", "1of1"),
    "ablazechainmail": ("ablaze.jpg", "Ablaze", "ablaze"),
    "aboveaverage.st": ("aboveavarage.jpg", "Above Average", "above average"),
    "accident133": ("accident.jpg", "Accident", "accident"),
    "atelieraevus": ("aevus.jpg", "Atelier Aevus", "aevus"),
    "agui.com.br": ("agui.jpg", "Agui", "agui"),
    "alexandrepavaodotcom": ("alexandre.jpg", "Alexandre Pavão", "alexandre pavao"),
    "amnidevt": ("amni.jpg", "Amni", "amni"),
    "anciestanger": ("anciestanger.jpg", "Anciestanger", "anciestanger"),
    "annyapparel_": ("anny.jpg", "Anny Apparel", "anny"),
    "anty.brand": ("anty.jpg", "Anty", "anty"),
    "apill_____": ("apill.jpg", "Apill", "apill"),
    "arch______studio": ("arch.jpg", "Arch Studio", "arch studio"),
    "b_____________eeer": ("beer.jpg", "Beer", "beer"),
    "bly.estetic": ("bly.jpg", "Bly", "bly"),
    "boffboychique": ("boffboy.jpg", "Boffboy Chique", "boffboy"),
    "bootllegal": ("boot.jpg", "Bootllegal", "bootllegal"),
    "borra_malware": ("borra.jpg", "Borra", "borra"),
    "bosycoys": ("bosy.jpg", "Bosy", "bosy"),
    "bouji.oficial": ("bouji.jpg", "Bouji", "bouji"),
    "bugi.studio": ("bugi.jpg", "Bugi Studio", "bugi"),
    "bussfly": ("bussfly.jpg", "Bussfly", "bussfly"),
    "carnan": ("carnan.jpg", "Carnan", "carnan"),
    "cettibr": ("cetti.jpg", "Cetti", "cetti"),
    "cieseason": ("cie.jpg", "Cie", "cie"),
    "cienalab": ("ciena.jpg", "Ciena", "ciena"),
    "cipher_plague": ("cipher.jpg", "Cipher Plague", "cipher"),
    "clmntstudio": ("clemente.jpg", "Clemente Studio", "clemente"),
    "corearchivist": ("core.jpg", "Core Archivist", "core"),
    "ewcruel": ("cruel.jpg", "Cruel", "cruel"),
    "cypriano___": ("cypriano.jpg", "Cypriano", "cypriano"),
    "delafoeco": ("delafoe.jpg", "Delafoe", "delafoe"),
    "desgosto": ("desgosto.jpg", "Desgosto", "desgosto"),
    "des.prezo": ("desprezo.jpg", "Desprezo", "desprezo"),
    "diptaller": ("diptaller.jpg", "Diptaller", "diptaller"),
    "dirty.com.br": ("dirty.jpg", "Dirty", "dirty"),
    "internetradiodismorfia": ("dismorfia.jpg", "Dismorfia", "dismorfia"),
    "disorder.com.br": ("disorder.jpg", "Disorder", "disorder"),
    "dodalfaiataria": ("dod-alfaiataria.jpg", "DOD Alfaiataria", "dod alfaiataria"),
    "dope__studios": ("dope.jpg", "Dope Studios", "dope"),
    "dothproject": ("doth.jpg", "Doth Project", "doth"),
    "down.jacquards": ("down.jpg", "Down Jacquards", "down"),
    "ducktheanarco": ("duck.jpg", "Duck", "duck"),
    "thedustcompany": ("dust.jpg", "Dust Company", "dust"),
    "dyingbrains": ("dyingbrains.jpg", "Dying Brains", "dying brains"),
    "each_br": ("each.jpg", "Each", "each"),
    "eclat.sty": ("eclat.jpg", "Eclat", "eclat"),
    "eghostudios": ("egho.jpg", "Egho Studios", "egho"),
    "eloemcomum": ("elo.jpg", "Elo em Comum", "elo"),
    "teiaaaaaaaaaaaaaaaaaaa": ("estudioteia.jpg", "Teia", "teia"),
    "etogallery": ("eto.jpg", "Eto Gallery", "eto"),
    "exodus.index": ("exodus.jpg", "Exodus", "exodus"),
    "666fantasma666": ("fantasma.jpg", "Fantasma", "fantasma"),
    "fashiondwsign": ("maison.jpg", "Maison RefTaylor", "maison"),
    "femzor": ("femzor.jpg", "Femzor", "femzor"),
    "flysupply.inc": ("fly.jpg", "Fly Supply", "fly"),
    "gurte": ("gurte.jpg", "Gurte", "gurte"),
    "haltfever": ("halt.jpg", "Halt Fever", "halt"),
    "hardjeanssanto": ("hardjeanssanto.jpg", "Hard Jeans Santo", "hard jeans santo"),
    "hasag.store": ("hasag.jpg", "Hasag", "hasag"),
    "heiko.cc": ("heiko.jpg", "Heiko", "heiko"),
    "helloneartx": ("helloneartx.jpg", "Hell on Eartx", "helloneartx"),
    "hextermina": ("hextermina.jpg", "Hextermina", "hextermina"),
    "hist_______": ("hist.jpg", "Hist", "hist"),
    "humaniteism": ("humanite.jpg", "Humanite", "humanite"),
    "iniquity____": ("iniquity.jpg", "Iniquity", "iniquity"),
    "kapitolkulture": ("kapitol.jpg", "Kapitol Kulture", "kapitol"),
    "kardiganstudios": ("kardigan.jpg", "Kardigan Studios", "kardigan"),
    "kg__studios": ("kgstudios.jpg", "KG Studios", "kg studios"),
    "fs.kleos": ("kleos.jpg", "Kleos", "kleos"),
    "leordre": ("leordre.jpg", "Le Ordre", "leordre"),
    "lepreofficial": ("lepre.jpg", "Lepre", "lepre"),
    "lobo_trajado": ("lobotrajado.jpg", "Lobo Trajado", "lobo trajado"),
    "lobo__bobo": ("lobobobo.jpg", "Lobo Bobo", "lobo bobo"),
    "lts__studios": ("lts.jpg", "LTS Studios", "lts"),
    "lykd_studio": ("lykd.jpg", "Lykd Studio", "lykd"),
    "mad_enlatados": ("madenlatados.jpg", "Mad Enlatados", "mad enlatados"),
    "use_melania": ("melania.jpg", "Melania", "melania"),
    "mldyy444": ("melody.jpg", "Melody", "melody"),
    "messa.og": ("messa.jpg", "Messa", "messa"),
    "mis_____fits": ("misfits.jpg", "Misfits", "misfits"),
    "monadaxyz": ("monada.jpg", "Monada", "monada"),
    "mortevisual": ("mortevisual.jpg", "Morte Visual", "morte visual"),
    "naiceco": ("naice.jpg", "Naice", "naice"),
    "nilmesz": ("nilme.jpg", "Nilme", "nilme"),
    "nimbo_creations": ("nimbo.jpg", "Nimbo Creations", "nimbo"),
    "ninfacyborg": ("ninfa.jpg", "Ninfa Cyborg", "ninfa"),
    "noir.division_": ("noirdivison.jpg", "Noir Division", "noir division"),
    "notfun.co": ("notfun.jpg", "Not Fun", "notfun"),
    "onyx.five": ("onyx.jpg", "Onyx Five", "onyx"),
    "0br1g0n": ("obrigon.jpg", "Obrigon", "obrigon"),
    "pace": ("pace.jpg", "Pace", "pace"),
    "pendrag6n": ("pendragon.jpg", "Pendragon", "pendragon"),
    "perschange": ("perschange.jpg", "Perschange", "perschange"),
    "piet_org": ("piet.jpg", "Piet", "piet"),
    "prelvde.corp": ("prelvde.jpg", "Prelvde", "prelvde"),
    "preux_official": ("preux.jpg", "Preux", "preux"),
    "quadrocreations": ("quadro.jpg", "Quadro Creations", "quadro"),
    "rapha___________": ("rapha.jpg", "Rapha", "rapha"),
    "rebornstudio__": ("reborn.jpg", "Reborn Studio", "reborn"),
    "refine.company": ("refine.jpg", "Refine Company", "refine"),
    "requiem.fi": ("requiem.jpg", "Requiem", "requiem"),
    "resurgestudios_": ("resurge.jpg", "Resurge Studios", "resurge"),
    "rhytmo__": ("rhytmo.jpg", "Rhytmo", "rhytmo"),
    "saintephemere": ("saintephemere.jpg", "Saint Éphémère", "saintephemere"),
    "samplecqa": ("sample.jpg", "Sample", "sample"),
    "santapeste": ("santapeste.jpg", "Santa Peste", "santapeste"),
    "sarcophvgus": ("sarcophvgus.jpg", "Sarcophvgus", "sarcophvgus"),
    "sczosix": ("sczosix.jpg", "Sczo-6", "sczosix"),
    "secta.online": ("secta.jpg", "Secta", "secta"),
    "ssexyysymbol": ("sexsymbol.jpg", "Sex Symbol", "sexsymbol"),
    "shiftedsant": ("shift.jpg", "Shifted Sant", "shiftedsant"),
    "sixthaven": ("sixthaven.jpg", "Sixthaven", "sixthaven"),
    "sskopos": ("skopos.jpg", "Skopos", "skopos"),
    "sobersince2009": ("sober.jpg", "Sober Since 2009", "sober"),
    "s000ldi": ("soldi.jpg", "Soldi", "soldi"),
    "sopro.co": ("sopro.jpg", "Sopro", "sopro"),
    "sowsupply": ("sow.jpg", "State of Wonder", "sow"),
    "spicebysilva": ("spice.jpg", "Spice by Silva", "spice"),
    "spicyjam.studio": ("spicyjam.jpg", "Spicy Jam Studio", "spicyjam"),
    "twovariant": ("twovariant.jpg", "Two Variant", "twovariant"),
    "ukio_____": ("ukio.jpg", "Ukio", "ukio"),
    "ums458": ("ums.jpg", "UMS 458", "ums"),
    "ung.br": ("ung.jpg", "UNG", "ung"),
    "velvetblogg": ("velvet.jpg", "Velvet", "velvet"),
    "ventana____": ("ventana.jpg", "Ventana", "ventana"),
    "viga.shoes": ("viga.jpg", "Viga Shoes", "viga"),
    "vilelaboots": ("vilela.jpg", "Vilela Boots", "vilela"),
    "vinegar.archive.br": ("vinegar.jpg", "Vinegar Archive", "vinegar"),
    "wearvsc": ("vscwear.jpg", "Wear VSC", "wearvsc"),
    "wordly.co": ("wordly.jpg", "Wordly", "wordly"),
    "armuraa": ("armura.jpg", "Armura", "armura"),
    "bobestudios": ("bobe.jpg", "Bobe Studios", "bobe studios"),
    "ateliebyeller": ("byeller.jpg", "ByEller", "byeller"),
    "fantasiaceleste_": ("fantasiaceleste.jpg", "Fantasia Celeste", "fantasia celeste"),
    "grama____": ("grama.jpg", "Grama", "grama"),
    "martins__________": ("martins.jpg", "Martins", "martins"),
    "newcultdestroy": ("newcultdestroy.jpg", "New Cult Destroy", "new cult destroy"),
    "outliertlr": ("outlier.jpg", "Atelier Outlier", "outlier"),
    "usestacci": ("stacci.jpg", "Stacci", "stacci"),
    "st.lacerda": ("stlacerda.jpg", "Studio Lacerda", "studio lacerda"),
    "theybs_oficial": ("theybs.jpg", "Theybs", "theybs"),
    "trecostudio": ("trecostudio.jpg", "Treco Studio", "treco studio"),
    "unselfishlover": ("unselfishlover.jpg", "Unselfish Lover", "unselfish lover"),
}

VIBE_OVERRIDES: dict[str, list[str]] = {
    "atelieraevus": ["avantgarde", "darkwear", "artisanal"],
    "onyx.five": ["avantgarde", "tailoring", "darkwear"],
    "secta.online": ["avantgarde", "tailoring", "darkwear"],
    "0br1g0n": ["avantgarde", "artisanal", "darkwear"],
    "noir.division_": ["darkwear", "avantgarde", "artisanal"],
    "ewcruel": ["darkwear", "punk", "graphic"],
    "iniquity____": ["darkwear", "streetwear", "graphic"],
    "mortevisual": ["darkwear", "punk", "graphic"],
    "sarcophvgus": ["darkwear", "avantgarde"],
    "requiem.fi": ["darkwear", "avantgarde"],
    "resurgestudios_": ["darkwear", "punk"],
    "hextermina": ["darkwear", "punk"],
    "santapeste": ["darkwear", "punk"],
    "666fantasma666": ["darkwear", "punk"],
    "sixthaven": ["darkwear", "punk", "graphic"],
    "borra_malware": ["upcycling", "punk", "artisanal"],
    "ninfacyborg": ["upcycling", "avantgarde", "cyber"],
    "internetradiodismorfia": ["punk", "graphic", "streetwear"],
    "desgosto": ["punk", "darkwear", "graphic"],
    "des.prezo": ["punk", "darkwear", "graphic"],
    "dothproject": ["gorpcore", "techwear", "artisanal"],
    "corearchivist": ["archive", "gorpcore", "streetwear"],
    "ums458": ["archive", "artisanal", "gorpcore"],
    "sczosix": ["cyber", "gorpcore", "experimental"],
    "cipher_plague": ["cyber", "darkwear"],
    "dodalfaiataria": ["tailoring", "minimal"],
    "amnidevt": ["minimal", "tailoring", "contemporary"],
    "leordre": ["minimal", "tailoring", "contemporary"],
    "saintephemere": ["minimal", "contemporary", "avantgarde"],
    "arch______studio": ["minimal", "contemporary"],
    "cienalab": ["minimal", "contemporary"],
    "eclat.sty": ["minimal", "contemporary"],
    "preux_official": ["minimal", "streetwear"],
    "heiko.cc": ["minimal", "streetwear"],
    "carnan": ["streetwear", "contemporary", "minimal"],
    "pace": ["streetwear", "contemporary", "gorpcore"],
    "piet_org": ["streetwear", "contemporary", "gorpcore"],
    "mad_enlatados": ["streetwear", "graphic"],
    "kapitolkulture": ["streetwear", "graphic"],
    "dope__studios": ["streetwear", "graphic"],
    "kardiganstudios": ["streetwear", "contemporary"],
    "sowsupply": ["streetwear", "contemporary"],
    "ukio_____": ["streetwear", "minimal"],
    "ducktheanarco": ["streetwear", "punk", "graphic"],
    "wordly.co": ["streetwear", "graphic", "experimental"],
    "bussfly": ["streetwear", "graphic"],
    "ablazechainmail": ["accessories", "darkwear", "artisanal"],
    "aboveaverage.st": ["accessories", "streetwear"],
    "clmntstudio": ["accessories", "minimal"],
    "vinegar.archive.br": ["accessories", "archive"],
    "vilelaboots": ["footwear", "avantgarde", "darkwear"],
    "viga.shoes": ["footwear", "contemporary", "tailoring"],
    "agui.com.br": ["footwear", "streetwear"],
    "armuraa": ["avantgarde", "artisanal"],
    "bobestudios": ["streetwear", "graphic", "contemporary"],
    "ateliebyeller": ["artisanal", "upcycling", "streetwear"],
    "fantasiaceleste_": ["artisanal", "upcycling", "experimental"],
    "grama____": ["contemporary", "minimal", "tailoring"],
    "martins__________": ["avantgarde", "tailoring", "contemporary", "experimental"],
    "newcultdestroy": ["darkwear", "punk", "graphic"],
    "outliertlr": ["upcycling", "artisanal", "punk"],
    "usestacci": ["streetwear", "graphic", "contemporary"],
    "st.lacerda": ["contemporary", "minimal", "graphic"],
    "theybs_oficial": ["streetwear", "artisanal", "experimental"],
    "trecostudio": ["punk", "graphic", "streetwear"],
    "unselfishlover": ["artisanal", "contemporary", "experimental"],
}


def make_slug(img_file: str) -> str:
    return Path(img_file).stem.lower().replace(" ", "-")


def infer_vibes(handle: str, cats: list[str]) -> list[str]:
    if handle in VIBE_OVERRIDES:
        return VIBE_OVERRIDES[handle]
    vibes: list[str] = []
    if "calcados" in cats:
        vibes.extend(["footwear", "contemporary"])
    if "acessorios" in cats:
        vibes.extend(["accessories", "streetwear"])
    if "alfaiataria" in cats or "sob medida" in cats:
        vibes.extend(["tailoring", "avantgarde"])
    if "upcycling" in cats:
        vibes.extend(["upcycling", "artisanal", "punk"])
    if "modular" in cats:
        vibes.extend(["gorpcore", "techwear"])
    if "handmade" in cats or "artisanal" in cats:
        vibes.extend(["artisanal", "avantgarde"])
    if "diversos" in cats:
        vibes.extend(["experimental", "streetwear"])
    if not vibes:
        vibes.extend(["streetwear", "contemporary"])
    return list(dict.fromkeys(vibes))


def fmt_brl_short(val: float | None) -> str:
    if val is None:
        return ""
    if abs(val - round(val)) < 0.01:
        return f"R$ {int(round(val)):,}".replace(",", ".")
    s = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def fmt_brl_full(val: float | None) -> str:
    if val is None:
        return ""
    s = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    txt = TXT_PATH.read_text(encoding="utf-8")
    price_map: dict[str, dict] = {}
    if PRICE_PATH.exists():
        for entry in json.loads(PRICE_PATH.read_text(encoding="utf-8")):
            if entry.get("handle"):
                price_map[entry["handle"]] = entry
            if entry.get("slug"):
                price_map[entry["slug"]] = entry

    loc_map: dict[str, dict] = {}
    if LOCATION_PATH.exists():
        loc_map = json.loads(LOCATION_PATH.read_text(encoding="utf-8"))

    brands = []
    used_files = set()

    for line in txt.splitlines():
        m = re.search(r"(https://www\.instagram\.com/([^/?\s]+))([^\n]*)", line)
        if not m:
            continue
        _, handle, rest = m.groups()
        if handle not in MAPPING:
            continue
        img_file, display_name, sort_key = MAPPING[handle]
        img_path = IMG_DIR / img_file
        if not img_path.exists():
            raise FileNotFoundError(f"Imagem ausente: {img_path}")
        used_files.add(img_file)

        cats = [c.strip().lower() for c in re.findall(r"\(([^)]+)\)", rest)]
        if "roupa" in cats and "roupas" not in cats:
            cats.append("roupas")
        if "roupas e bandeiras" in cats and "roupas" not in cats:
            cats.append("roupas")
        if "alfaiataria" in cats and "sob medida" not in cats:
            cats.append("sob medida")
        if "artisanal" in cats and "handmade" not in cats:
            cats.append("handmade")

        slug = make_slug(img_file)
        vibes = infer_vibes(handle, cats)

        p_info = price_map.get(handle) or price_map.get(slug) or {}
        found_price = bool(
            p_info.get("found")
            and p_info.get("min_price") is not None
            and p_info.get("max_price") is not None
        )
        min_p = float(p_info["min_price"]) if found_price else None
        max_p = float(p_info["max_price"]) if found_price else None
        avg_p = round((min_p + max_p) / 2.0, 2) if (min_p is not None and max_p is not None) else None

        l_info = loc_map.get(slug) or {}

        brands.append(
            {
                "slug": slug,
                "name": display_name,
                "sort_key": sort_key,
                "handle": handle,
                "url": f"https://www.instagram.com/{handle}/",
                "img": f"assets/img/marcas/{img_file}",
                "categories": cats,
                "vibes": vibes,
                "price_found": found_price,
                "min_price": min_p,
                "max_price": max_p,
                "avg_price": avg_p,
                "min_item": p_info.get("min_item", "") if found_price else "",
                "max_item": p_info.get("max_item", "") if found_price else "",
                "store_url": p_info.get("store_url") if p_info else None,
                "city": l_info.get("city", "São Paulo"),
                "state": l_info.get("state", "SP"),
                "location": l_info.get("location_str", "São Paulo - SP"),
                "location_source": l_info.get("source", ""),
                "location_confidence": l_info.get("confidence", "high"),
                "lat": l_info.get("lat", -23.5505),
                "lon": l_info.get("lon", -46.6333),
                "map_x": l_info.get("map_x", 1058.0),
                "map_y": l_info.get("map_y", 888.0),
                "state_x": l_info.get("state_x", 500.0),
                "state_y": l_info.get("state_y", 330.0),
            }
        )

    UNLINKED_DIR.mkdir(parents=True, exist_ok=True)
    for f in IMG_DIR.glob("*.jpg"):
        if f.name not in used_files:
            shutil.move(str(f), str(UNLINKED_DIR / f.name))

    brands.sort(key=lambda b: b["sort_key"])
    json_str = json.dumps(brands, ensure_ascii=False, indent=2)
    (ROOT / "database" / "marcas.json").write_text(json_str, encoding="utf-8")
    (DATA_DIR / "marcas.json").write_text(json_str, encoding="utf-8")

    priced_count = sum(1 for b in brands if b["price_found"])
    consult_count = len(brands) - priced_count
    cnt_200 = sum(1 for b in brands if b["price_found"] and b["avg_price"] is not None and b["avg_price"] <= 200)
    cnt_350 = sum(1 for b in brands if b["price_found"] and b["avg_price"] is not None and 200 < b["avg_price"] <= 350)
    cnt_600 = sum(1 for b in brands if b["price_found"] and b["avg_price"] is not None and 350 < b["avg_price"] <= 600)
    cnt_over_600 = sum(1 for b in brands if b["price_found"] and b["avg_price"] is not None and b["avg_price"] > 600)

    # Grid 3xN direto (<a class="brand-card"> dentro de .brands-grid, com ícone de info no canto inferior esquerdo)
    cards = []
    for idx, b in enumerate(brands):
        cat_str = " ".join(b["categories"])
        alt_str = html.escape(f"{b['name']} {cat_str}".strip())
        safe_name = html.escape(b["name"])
        if b["price_found"]:
            avg_txt = fmt_brl_full(b["avg_price"])
            min_txt = fmt_brl_full(b["min_price"])
            max_txt = fmt_brl_full(b["max_price"])
            title_str = html.escape(f"{b['name']} (@{b['handle']})")
            badge_html = (
                f'<span class="brand-price-info" tabindex="0" aria-label="Preços de {safe_name}">'
                f'<span class="bpi-icon" aria-hidden="true">i</span>'
                f'<span class="bpi-popover" role="tooltip">'
                f'<strong class="bpi-title">{safe_name}</strong>'
                f'<span class="bpi-row bpi-row-avg"><em data-i18n="price.card_avg">MÉDIA:</em> <b>{avg_txt}</b></span>'
                f'<span class="bpi-row"><em data-i18n="price.card_from">MÍNIMO:</em> <b>{min_txt}</b></span>'
                f'<span class="bpi-row"><em data-i18n="price.card_to">MÁXIMO:</em> <b>{max_txt}</b></span>'
                f"</span>"
                f"</span>"
            )
            min_attr = f"{b['min_price']:.2f}"
            max_attr = f"{b['max_price']:.2f}"
            avg_attr = f"{b['avg_price']:.2f}"
        else:
            title_str = html.escape(f"{b['name']} (@{b['handle']})")
            badge_html = (
                f'<span class="brand-price-info bpi-consult" tabindex="0" aria-label="Preços de {safe_name}">'
                f'<span class="bpi-icon" aria-hidden="true">i</span>'
                f'<span class="bpi-popover" role="tooltip">'
                f'<strong class="bpi-title">{safe_name}</strong>'
                f'<span class="bpi-row bpi-row-consult" data-i18n="price.badge_consult">DROP / SOB CONSULTA</span>'
                f"</span>"
                f"</span>"
            )
            min_attr = ""
            max_attr = ""
            avg_attr = ""

        cards.append(
            f'        <a class="brand-card" href="{b["url"]}" target="_blank" rel="noopener noreferrer" '
            f'title="{title_str}" data-slug="{html.escape(b["slug"])}" data-sort-idx="{idx}" '
            f'data-name="{html.escape(b["name"].lower())} {html.escape(b["handle"].lower())}" '
            f'data-categories="{html.escape(cat_str)}" '
            f'data-min-price="{min_attr}" data-max-price="{max_attr}" data-avg-price="{avg_attr}">'
            f'<img src="{b["img"]}?v={ASSET_VER}" alt="{alt_str}" loading="lazy" decoding="async" width="260" height="260" />'
            f"{badge_html}"
            f"</a>"
        )

    cards_joined = "\n".join(cards)
    page = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>M4RCAS — emorphosis.com.br</title>
  <link rel="icon" type="image/png" href="assets/img/favicon.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Inter:wght@400;500;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="assets/css/style.css?v={ASSET_VER}" />
</head>
<body class="page-marcas">
  <!-- Fundo da aba M4RCAS: vídeo generative background.mp4 -->
  <div class="bg-layer" id="marcas-bg-layer" aria-hidden="true">
    <video
      id="marcas-bg-video"
      autoplay
      muted
      loop
      playsinline
      preload="auto"
      poster="assets/img/home-bg-poster.jpg"
    >
      <source src="assets/video/home-bg.mp4" type="video/mp4" />
    </video>
  </div>

  <!-- Cabeçalho Padrão Emorphosis -->
  <header class="site-header">
    <div class="lang-switch" aria-label="Idioma / Language">
      <span role="button" tabindex="0" class="lang-btn active" data-lang-btn="pt">PT</span>
      <span class="lang-sep">/</span>
      <span role="button" tabindex="0" class="lang-btn" data-lang-btn="en">EN</span>
    </div>

    <div class="brand-wrap">
      <a href="/?v={ASSET_VER}" class="brand-link" aria-label="EMORPHOSIS - Página Inicial">
        <img src="assets/img/logo.png" alt="EMORPHOSIS" class="brand-logo" />
      </a>
      <div class="brand-divider" role="presentation"></div>
    </div>

    <nav class="site-nav" aria-label="Menu principal">
      <ul class="nav-list">
        <li><a href="/?v={ASSET_VER}" class="nav-link">H0M3</a></li>
        <li><a href="m4rcas.html" class="nav-link active" aria-current="page">M4RCAS</a></li>
        <li><a href="c4l3ndar10.html" class="nav-link">C4L3NDAR10</a></li>
        <li><a href="c0mun1dad3.html" class="nav-link">C0MUN1DAD3</a></li>
        <li><a href="s0br3.html" class="nav-link">S0BR3</a></li>
      </ul>
    </nav>
  </header>

  <main class="page-stage">
    <div class="stage-content marcas-stage">
      <!-- Topo da aba M4RCAS: apenas a barra de busca centralizada + botão de menu expansível ("três riscos") -->
      <div class="marcas-top-controls" id="marcas-top-controls">
        <div class="marcas-search-bar-row">
          <button
            type="button"
            class="hamburger-menu-btn"
            id="marcas-hamburger-btn"
            aria-expanded="false"
            aria-controls="marcas-drawer-panel"
            aria-label="Abrir menu de categorias e filtros"
            title="Menu: Catálogo, Quiz, Fit Lab e Filtros"
          >
            <span class="hamburger-lines" aria-hidden="true">
              <span></span>
              <span></span>
              <span></span>
            </span>
          </button>

          <div class="search-hero-wrap">
            <input
              type="search"
              id="brand-search"
              class="catalog-search-lg"
              placeholder="Buscar marca ou @instagram..."
              data-i18n-placeholder="marcas.search_placeholder"
              autocomplete="off"
            />
            <span class="brand-count" id="brand-count">{len(brands)}</span>
          </div>
        </div>

        <!-- Menu Expansível ("Três Riscos"): Modos (Catálogo / Quiz / Fit Lab) + Separação + Filtros -->
        <div class="marcas-drawer-panel" id="marcas-drawer-panel" hidden>
          <!-- Parte 1: Categorias de Modo (Catálogo / Quiz Gringa -> BR / Coleções & Fit Lab) -->
          <div class="drawer-section">
            <div class="drawer-section-header">
              <span class="drawer-section-title" data-i18n="marcas.menu_modes">SEÇÃO DA PÁGINA:</span>
            </div>
            <div class="subtabs-bar" role="tablist" aria-label="Modos da aba Marcas">
              <button type="button" class="subtab-btn active" data-subtab="catalogo" data-i18n="marcas.tab_catalog">CATÁL0G0 ({len(brands)})</button>
              <button type="button" class="subtab-btn" data-subtab="quiz" data-i18n="marcas.tab_quiz">QU1Z GRINGA → BR</button>
              <button type="button" class="subtab-btn" data-subtab="colecoes" data-i18n="marcas.tab_collections">C0L3ÇÕ3S &amp; F1T LAB</button>
            </div>
          </div>

          <!-- Separação clara entre as opções (Catálogo / Quiz / Fit Lab) e os Filtros de Categoria -->
          <div class="subtabs-divider" role="presentation" aria-hidden="true"></div>

          <!-- Parte 2: Filtros de Categoria das Marcas -->
          <div class="drawer-section">
            <div class="drawer-section-header">
              <span class="drawer-section-title" data-i18n="filter.menu_label">FILTRAR CATEGORIA:</span>
              <span class="filter-menu-current" id="filter-menu-current" data-i18n="filter.all">TODAS</span>
            </div>
            <div class="filter-pills" role="group" aria-label="Filtrar por categoria">
              <button type="button" class="filter-pill active" data-filter="all" data-i18n="filter.all">TODAS</button>
              <button type="button" class="filter-pill" data-filter="roupas" data-i18n="filter.roupas">ROUPAS</button>
              <button type="button" class="filter-pill" data-filter="handmade" data-i18n="filter.handmade">HANDMADE</button>
              <button type="button" class="filter-pill" data-filter="acessorios" data-i18n="filter.acessorios">ACESSÓRIOS</button>
              <button type="button" class="filter-pill" data-filter="calcados" data-i18n="filter.calcados">CALÇADOS</button>
              <button type="button" class="filter-pill" data-filter="sob medida" data-i18n="filter.sob_medida">SOB MEDIDA / ALFAIATARIA</button>
              <button type="button" class="filter-pill" data-filter="upcycling" data-i18n="filter.upcycling">UPCYCLING</button>
              <button type="button" class="filter-pill" data-filter="diversos" data-i18n="filter.diversos">DIVERSOS</button>
            </div>
          </div>
        </div>
      </div>

      <!-- SUB-ABA 1: CATÁLOGO 3xN + BARRA LATERAL MINIMIZÁVEL DE PREÇO & MÉDIA -->
      <section id="subview-catalogo" class="subview-section">
        <!-- Barra Lateral de Filtro de Preço e Média (Pode ser Minimizada e Maximizada) -->
        <div class="price-sidebar-wrap" id="price-sidebar-wrap">
          <!-- Botão / Aba Lateral quando Minimizada (para Maximizar) -->
          <button
            type="button"
            class="price-sidebar-open-btn"
            id="price-sidebar-open-btn"
            aria-expanded="true"
            aria-controls="price-sidebar"
            title="Maximizar filtro de preço e média"
          >
            <span class="ps-open-icon" aria-hidden="true">💲</span>
            <span class="ps-open-label" data-i18n="price.sidebar_open_btn">PREÇO &amp; MÉDIA</span>
            <span class="ps-open-count" id="price-sidebar-mini-badge">{len(brands)}</span>
            <span class="ps-open-arrow" aria-hidden="true">▸</span>
          </button>

          <!-- Fundo escuro de toque para celular (fecha ao tocar fora) -->
          <div class="price-sidebar-backdrop" id="price-sidebar-backdrop" hidden></div>

          <!-- Painel da Barra Lateral Maximizada -->
          <aside class="price-sidebar" id="price-sidebar" aria-label="Filtro lateral de preço e média">
            <div class="price-sidebar-top">
              <div class="price-sidebar-brand">
                <span class="ps-top-kicker" data-i18n="price.sidebar_kicker">FILTRO INTERATIVO</span>
                <h3 class="ps-top-title" data-i18n="price.sidebar_title">PREÇO &amp; MÉDIA</h3>
              </div>
              <button
                type="button"
                class="price-sidebar-min-btn"
                id="price-sidebar-min-btn"
                aria-label="Minimizar barra lateral de preço"
                title="Minimizar barra lateral"
              >
                <span aria-hidden="true">◂</span>
                <span data-i18n="price.sidebar_min_btn">MINIMIZAR</span>
              </button>
            </div>

            <!-- Status em Tempo Real -->
            <div class="price-sidebar-status">
              <span class="price-val-badge" id="price-slider-val-badge" data-i18n="price.no_limit">SEM LIMITE ({len(brands)} MARCAS)</span>
              <span class="avg-live-summary" id="avg-live-summary">Exibindo {len(brands)} marcas ({priced_count} com média)</span>
            </div>

            <div class="price-sidebar-body">
              <!-- Bloco 1: Barra Deslizante (Marcas com peças abaixo do valor selecionado) -->
              <div class="price-sidebar-block">
                <div class="ps-block-head">
                  <span class="ps-block-title" data-i18n="price.slider_title_short">PEÇAS ABAIXO DO VALOR:</span>
                  <span class="ps-block-sub" data-i18n="price.slider_sub_short">Deslize para selecionar o valor máximo</span>
                </div>

                <div class="price-slider-track-row">
                  <span class="price-bound-label">R$ 25</span>
                  <input
                    type="range"
                    id="price-max-slider"
                    class="price-range-slider"
                    min="25"
                    max="700"
                    step="5"
                    value="700"
                    aria-label="Selecionar valor máximo de peça em reais"
                  />
                  <span class="price-bound-label" data-i18n="price.bound_all">TODAS</span>
                </div>

                <div class="price-slider-presets" role="group" aria-label="Atalhos de valor máximo">
                  <button type="button" class="price-preset-chip" data-slider-preset="50">R$ 50</button>
                  <button type="button" class="price-preset-chip" data-slider-preset="100">R$ 100</button>
                  <button type="button" class="price-preset-chip" data-slider-preset="150">R$ 150</button>
                  <button type="button" class="price-preset-chip" data-slider-preset="200">R$ 200</button>
                  <button type="button" class="price-preset-chip" data-slider-preset="300">R$ 300</button>
                  <button type="button" class="price-preset-chip" data-slider-preset="500">R$ 500</button>
                  <button type="button" class="price-preset-chip" data-slider-preset="650">R$ 650</button>
                  <button type="button" class="price-preset-chip active" data-slider-preset="700" data-i18n="price.preset_all">TODAS</button>
                </div>
              </div>

              <!-- Bloco 2: Filtro por Média de Preço de Cada Marca ((Mais Barata + Mais Cara) / 2) -->
              <div class="price-sidebar-block">
                <div class="ps-block-head">
                  <span class="ps-block-title" data-i18n="price.avg_label_short">MÉDIA DE PREÇO DA MARCA:</span>
                  <span class="ps-block-sub" data-i18n="price.avg_sub_short">(Peça mais barata + mais cara ÷ 2)</span>
                </div>

                <div class="avg-price-pills" role="group" aria-label="Faixas de média de preço">
                  <button type="button" class="avg-price-pill active" data-avg-tier="all" data-i18n="price.tier_all">TODAS ({len(brands)})</button>
                  <button type="button" class="avg-price-pill" data-avg-tier="priced" data-i18n="price.tier_priced">COM MÉDIA MAPEADA ({priced_count})</button>
                  <button type="button" class="avg-price-pill" data-avg-tier="up_to_200" data-i18n="price.tier_200">MÉDIA ATÉ R$ 200 ({cnt_200})</button>
                  <button type="button" class="avg-price-pill" data-avg-tier="200_350" data-i18n="price.tier_350">MÉDIA R$ 200 – R$ 350 ({cnt_350})</button>
                  <button type="button" class="avg-price-pill" data-avg-tier="350_600" data-i18n="price.tier_600">MÉDIA R$ 350 – R$ 600 ({cnt_600})</button>
                  <button type="button" class="avg-price-pill" data-avg-tier="over_600" data-i18n="price.tier_over_600">MÉDIA ACIMA DE R$ 600 ({cnt_over_600})</button>
                  <button type="button" class="avg-price-pill" data-avg-tier="consult" data-i18n="price.tier_consult">DROP / SOB CONSULTA ({consult_count})</button>
                </div>
              </div>

              <!-- Bloco 3: Ordenação por Preço -->
              <div class="price-sidebar-block">
                <div class="ps-block-head">
                  <span class="ps-block-title" data-i18n="price.sort_label">ORDENAR CATÁLOGO:</span>
                </div>
                <div class="price-sort-group" role="group" aria-label="Ordenar marcas por preço">
                  <button type="button" class="price-sort-btn active" data-price-sort="az" data-i18n="price.sort_az">A–Z</button>
                  <button type="button" class="price-sort-btn" data-price-sort="avg_asc" data-i18n="price.sort_avg_asc">MENOR MÉDIA ↑</button>
                  <button type="button" class="price-sort-btn" data-price-sort="avg_desc" data-i18n="price.sort_avg_desc">MAIOR MÉDIA ↓</button>
                  <button type="button" class="price-sort-btn" data-price-sort="min_asc" data-i18n="price.sort_min_asc">MAIS BARATA ↑</button>
                </div>
              </div>
            </div>

            <!-- Rodapé da Barra Lateral -->
            <div class="price-sidebar-footer">
              <button type="button" class="reset-quiz-btn price-reset-btn" id="price-filter-reset-btn" data-i18n="price.reset_btn">Limpar filtro</button>
              <button type="button" class="btn-solid-green price-apply-mobile-btn" id="price-sidebar-apply-mobile-btn" data-i18n="price.apply_mobile_btn">VER MARCAS ▸</button>
            </div>
          </aside>
        </div>

        <div class="brands-grid" id="brands-grid" aria-label="Catálogo de Marcas">
{cards_joined}
        </div>

        <!-- Sistema de Inscrição por E-mail nas Marcas (Alerta 1 Hora Antes do Drop) -->
        <div class="glass-box drop-subscribe-box" id="drop-subscribe-box">
          <span class="section-kicker" data-i18n="sub.kicker">ALERTA DE DROPS · 1 HORA ANTES</span>
          <h2 class="section-heading" data-i18n="sub.title">Inscreva-se nas Marcas para Avisos de Drop</h2>
          <p class="section-sub" data-i18n="sub.subtitle">
            Selecione as marcas que você acompanha (ou todas do catálogo) e cadastre seu e-mail. Quando faltar 1 hora para o drop começar, enviaremos um aviso com a marca, o horário exato e o link direto do Instagram.
          </p>

          <form id="brand-drop-sub-form" class="brand-drop-sub-form">
            <div class="sub-Controls-toolbar">
              <button type="button" class="sub-all-toggle" id="sub-all-brands-btn" data-i18n="sub.select_all">
                ★ TODAS AS MARCAS ({len(brands)})
              </button>
              <input
                type="search"
                id="sub-brand-filter"
                class="radar-input sub-brand-filter-input"
                placeholder="Filtrar marcas para selecionar..."
                data-i18n-placeholder="sub.filter_ph"
                autocomplete="off"
              />
              <span class="sub-selected-counter" id="sub-selected-counter">0 selecionada(s)</span>
              <button type="button" class="reset-quiz-btn" id="sub-clear-brands-btn" data-i18n="sub.clear_btn">
                Limpar marcas
              </button>
            </div>

            <div class="sub-brands-selector" id="sub-brands-selector" role="group" aria-label="Selecionar marcas para receber alertas"></div>

            <div class="sub-email-submit-row">
              <input
                type="email"
                id="sub-user-email"
                name="email"
                required
                class="radar-input sub-email-input"
                placeholder="Digite seu melhor e-mail..."
                data-i18n-placeholder="sub.email_ph"
                autocomplete="email"
              />
              <button type="submit" class="btn-solid-green sub-submit-btn" id="sub-submit-btn" data-i18n="sub.submit_btn">
                INSCREVER-SE NOS DROPS (AVISO 1H ANTES)
              </button>
            </div>
            <p id="sub-form-feedback" class="form-feedback" aria-live="polite"></p>
          </form>
        </div>
      </section>

      <!-- SUB-ABA 2: QUESTIONÁRIO & BUSCADOR DE REFERÊNCIAS INTERNACIONAIS -> BR -->
      <section id="subview-quiz" class="subview-section" hidden>
        <div class="glass-box">
          <span class="section-kicker" data-i18n="quiz.kicker">CURADORIA INTERNACIONAL → NACIONAL</span>
          <h2 class="section-heading" data-i18n="quiz.title">Encontre Marcas Brasileiras pelo seu Gosto</h2>
          <p class="section-sub" data-i18n="quiz.subtitle">
            Selecione marcas internacionais que você curte e responda 3 perguntas rápidas para descobrir marcas independentes brasileiras com estética próxima.
          </p>

          <!-- Passo 1: Referências Internacionais -->
          <div class="quiz-block">
            <h3 class="quiz-step-title" data-i18n="quiz.step1">1. Quais referências internacionais conversam com seu estilo? (escolha quantas quiser)</h3>
            <div class="intl-chips" id="intl-chips"></div>
          </div>

          <!-- Passo 2: Estética / Silhouette -->
          <div class="quiz-block">
            <h3 class="quiz-step-title" data-i18n="quiz.step2">2. Qual atmosfera visual você mais procura hoje?</h3>
            <div class="quiz-options" data-quiz-group="vibe">
              <button type="button" class="quiz-opt" data-val="darkwear" data-i18n="quiz.vibe_dark">Darkwear / Avant-Garde / Gótico</button>
              <button type="button" class="quiz-opt" data-val="streetwear" data-i18n="quiz.vibe_street">Streetwear / Gráfico / Urbano</button>
              <button type="button" class="quiz-opt" data-val="minimal" data-i18n="quiz.vibe_minimal">Alfaiataria / Minimalista / Clean</button>
              <button type="button" class="quiz-opt" data-val="upcycling" data-i18n="quiz.vibe_diy">Upcycling / Desconstruído / Punk DIY</button>
              <button type="button" class="quiz-opt" data-val="gorpcore" data-i18n="quiz.vibe_tech">Modular / Techwear / Utilitário</button>
            </div>
          </div>

          <!-- Passo 3: Tipo de Peça / Construção -->
          <div class="quiz-block">
            <h3 class="quiz-step-title" data-i18n="quiz.step3">3. O que mais pesa na sua escolha?</h3>
            <div class="quiz-options" data-quiz-group="focus">
              <button type="button" class="quiz-opt" data-val="all" data-i18n="quiz.focus_any">Qualquer peça (visão geral)</button>
              <button type="button" class="quiz-opt" data-val="handmade" data-i18n="quiz.focus_handmade">Feito à mão / Tiragem limitada / 1of1</button>
              <button type="button" class="quiz-opt" data-val="tailoring" data-i18n="quiz.focus_tailoring">Corte sob medida / Caimento de alfaiataria</button>
              <button type="button" class="quiz-opt" data-val="accessories" data-i18n="quiz.focus_acc">Acessórios, Chainmail &amp; Joalheria Bruta</button>
              <button type="button" class="quiz-opt" data-val="footwear" data-i18n="quiz.focus_foot">Botas &amp; Calçados Autorais</button>
            </div>
          </div>

          <div class="quiz-results-wrap" id="quiz-results-wrap">
            <div class="quiz-results-header">
              <h3 class="quiz-step-title" data-i18n="quiz.results_title">Recomendações Brasileiras para Você</h3>
              <button type="button" class="reset-quiz-btn" id="reset-quiz-btn" data-i18n="quiz.reset">Limpar seleção</button>
            </div>
            <div class="quiz-results-grid" id="quiz-results-grid"></div>
          </div>
        </div>
      </section>

      <!-- SUB-ABA 3: ABA DE COLEÇÃO DE MARCAS + MANEQUIM VIRTUAL (FIT BUILDER BETA) -->
      <section id="subview-colecoes" class="subview-section" hidden>
        <!-- Manequim Virtual / Fit Builder -->
        <div class="glass-box fitlab-box">
          <span class="section-kicker" data-i18n="fit.kicker">PROTÓTIPO INTERATIVO · FIT LAB</span>
          <h2 class="section-heading" data-i18n="fit.title">Manequim Virtual — Montador de Fits</h2>
          <p class="section-sub" data-i18n="fit.subtitle">
            Combine peças por camada (Acessório, Parte Superior, Calça e Calçado) de marcas do diretório Emorphosis para visualizar paleta, proporção e descobrir combinações.
          </p>

          <div class="fitlab-grid">
            <!-- Manequim SVG Dinâmico -->
            <div class="mannequin-stage">
              <svg id="mannequin-svg" viewBox="0 0 260 460" class="mannequin-svg" aria-label="Manequim Virtual Emorphosis">
                <!-- Silhueta base -->
                <circle cx="130" cy="44" r="22" fill="#050c06" stroke="#19f028" stroke-width="1.5" />
                <rect x="122" y="65" width="16" height="14" rx="4" fill="#050c06" stroke="#19f028" stroke-width="1" />
                <!-- Footwear / Botas (base inferior) -->
                <g id="svg-slot-shoes">
                  <path id="svg-shoes-shape" d="M80 386 L122 386 L122 420 L70 420 Q68 404 80 386 Z M138 386 L180 386 Q192 404 190 420 L138 420 Z" fill="#030704" stroke="#19f028" stroke-width="1.6" />
                  <image id="svg-shoes-img" href="" x="56" y="376" width="148" height="62" preserveAspectRatio="xMidYMid meet" class="mannequin-cutout-img" style="display:none" />
                </g>
                <!-- Bottom / Calça Wide / Alfaiataria -->
                <g id="svg-slot-bottom">
                  <path id="svg-bottom-shape" d="M95 218 L165 218 L178 386 L136 386 L130 274 L124 386 L82 386 Z" fill="#050c06" stroke="#19f028" stroke-opacity="0.8" stroke-width="1.6" style="display:none" />
                  <image id="svg-bottom-img" href="assets/img/fitlab/aevus-calca.png" x="50" y="204" width="160" height="202" preserveAspectRatio="xMidYMid meet" class="mannequin-cutout-img" />
                </g>
                <!-- Top / Jaqueta / Camiseta Boxy (sobrepõe o cós da calça naturalmente) -->
                <g id="svg-slot-top">
                  <path id="svg-top-shape" d="M74 82 L108 76 L152 76 L186 82 L198 176 L172 180 L166 126 L166 220 L94 220 L94 126 L88 180 L62 176 Z" fill="#09140b" stroke="#19f028" stroke-width="1.8" style="display:none" />
                  <image id="svg-top-img" href="assets/img/fitlab/aevus-jaqueta.png" x="26" y="50" width="208" height="176" preserveAspectRatio="xMidYMid meet" class="mannequin-cutout-img" />
                </g>
                <!-- Acessório / Headwear / Chainmail -->
                <g id="svg-slot-acc">
                  <g id="svg-acc-shape" style="display:none">
                    <path d="M104 38 Q130 14 156 38 L152 46 Q130 34 108 46 Z" fill="#19f028" opacity="0.85" />
                    <circle cx="130" cy="84" r="14" fill="none" stroke="#19f028" stroke-width="2.5" stroke-dasharray="3 2" />
                  </g>
                  <image id="svg-acc-img" href="assets/img/fitlab/drestudio-bone.png" x="96" y="2" width="68" height="58" preserveAspectRatio="xMidYMid meet" class="mannequin-cutout-img" />
                </g>
              </svg>
              <div class="mannequin-note" data-i18n="fit.png_note">
                Pronto para receber recortes PNG reais das peças das marcas.
              </div>
            </div>

            <!-- Controles de cada Camada -->
            <div class="fitlab-controls" id="fitlab-controls"></div>
          </div>
        </div>

        <!-- Estúdio de Upload & Recorte Automático de Peças Pessoais (Salvo Localmente por Usuário) -->
        <div class="glass-box custom-wardrobe-box" id="fitlab-custom-studio">
          <span class="section-kicker" data-i18n="fit.custom_kicker">ACERVO PESSOAL PRIVADO · SÓ VOCÊ VÊ</span>
          <h2 class="section-heading" data-i18n="fit.custom_title">Enviar e Recortar Sua Própria Peça</h2>
          <p class="section-sub" data-i18n="fit.custom_sub">
            Envie a foto de uma roupa ou acessório. O site remove o fundo automaticamente, recorta a peça e adiciona à sua coleção pessoal no Manequim Virtual (disponível apenas para você neste navegador).
          </p>

          <div class="custom-upload-grid">
            <!-- Coluna 1: Configuração da Peça e Upload -->
            <div class="custom-upload-form">
              <div class="custom-field-group">
                <label for="custom-piece-slot" class="custom-field-label" data-i18n="fit.slot_label">1. Categoria / Camada no Manequim</label>
                <select id="custom-piece-slot" class="radar-input custom-select">
                  <option value="top" data-i18n="fit.slot_top">Parte Superior / Top (Jaqueta, Camiseta, Moletom)</option>
                  <option value="bottom" data-i18n="fit.slot_bottom">Parte Inferior / Calça (Calça, Bermuda, Saia)</option>
                  <option value="acc" data-i18n="fit.slot_acc">Acessório / Headwear (Boné, Gorro, Bolsa, Joia)</option>
                  <option value="shoes" data-i18n="fit.slot_shoes">Calçado / Footwear (Bota, Tênis, Sapato)</option>
                </select>
              </div>

              <div class="custom-field-group">
                <label for="custom-piece-name" class="custom-field-label" data-i18n="fit.piece_name_label">2. Nome da Peça</label>
                <input
                  type="text"
                  id="custom-piece-name"
                  class="radar-input"
                  placeholder="Ex: Minha Jaqueta Estruturada, Calça Baggy..."
                  data-i18n-placeholder="fit.piece_name_ph"
                  maxlength="60"
                />
              </div>

              <div class="custom-field-group">
                <label for="custom-piece-brand" class="custom-field-label" data-i18n="fit.piece_brand_label">3. Marca ou Identificação (opcional)</label>
                <input
                  type="text"
                  id="custom-piece-brand"
                  class="radar-input"
                  placeholder="Ex: Acervo Pessoal, Peça Autoral..."
                  data-i18n-placeholder="fit.piece_brand_ph"
                  maxlength="40"
                />
              </div>

              <div class="custom-file-upload-wrap">
                <input
                  type="file"
                  id="custom-piece-file"
                  accept="image/*"
                  class="custom-file-input-hidden"
                />
                <label for="custom-piece-file" class="btn-solid-green custom-file-btn" data-i18n="fit.upload_btn">
                  📷 ESCOLHER FOTO DA ROUPA (RECORTE AUTOMÁTICO)
                </label>
              </div>

              <!-- Controles de Sensibilidade do Recorte (aparecem após carregar uma foto) -->
              <div class="custom-cutout-tuning" id="custom-cutout-tuning" hidden>
                <div class="tuning-slider-row">
                  <label for="custom-cutout-tolerance" data-i18n="fit.tolerance_label">Sensibilidade do Recorte de Fundo:</label>
                  <span id="custom-tolerance-val" class="tuning-val-badge">36</span>
                </div>
                <input
                  type="range"
                  id="custom-cutout-tolerance"
                  min="5"
                  max="95"
                  value="36"
                  class="custom-range-slider"
                />

                <label class="custom-checkbox-row">
                  <input type="checkbox" id="custom-cutout-inner" checked />
                  <span data-i18n="fit.inner_pockets_label">Remover vãos internos do fundo (ex: entre as pernas da calça)</span>
                </label>

                <p class="custom-preview-hint" data-i18n="fit.preview_hint">
                  Dica: você também pode clicar em qualquer ponto do fundo na prévia para apagar aquela cor.
                </p>

                <div class="custom-tuning-actions">
                  <button type="button" class="reset-quiz-btn" id="btn-reset-cutout-clicks" data-i18n="fit.reset_clicks_btn">
                    Restaurar recorte padrão
                  </button>
                  <button type="button" class="btn-solid-green" id="btn-save-custom-piece" data-i18n="fit.save_piece_btn">
                    + ADICIONAR À MINHA COLEÇÃO E VESTIR NO MANEQUIM
                  </button>
                </div>
              </div>
              <p id="custom-upload-feedback" class="form-feedback" aria-live="polite"></p>
            </div>

            <!-- Coluna 2: Prévia Interativa do Recorte Transparente -->
            <div class="custom-preview-stage" id="custom-preview-stage">
              <div class="custom-preview-checkerboard" id="custom-preview-box">
                <canvas id="custom-cutout-canvas" class="custom-cutout-canvas" hidden></canvas>
                <div class="custom-preview-placeholder" id="custom-preview-placeholder">
                  <span>✂️</span>
                  <p>Selecione uma foto de roupa ao lado para visualizar o recorte automático em fundo transparente.</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Galeria da Coleção Pessoal do Usuário -->
          <div class="personal-wardrobe-gallery-wrap">
            <div class="quiz-results-header">
              <h3 class="quiz-step-title" data-i18n="fit.my_collection_title">Minha Coleção Pessoal (Visível Apenas para Você)</h3>
              <span class="sub-selected-counter" id="personal-wardrobe-count">0 peça(s)</span>
            </div>
            <div class="personal-wardrobe-grid" id="personal-wardrobe-grid"></div>
          </div>
        </div>

        <!-- Arquivo de Coleções & Drops de Marcas -->
        <div class="glass-box collections-box">
          <span class="section-kicker" data-i18n="col.kicker">ARQUIVO &amp; LOOKBOOKS</span>
          <h2 class="section-heading" data-i18n="col.title">Coleções &amp; Drops em Destaque</h2>
          <p class="section-sub" data-i18n="col.subtitle">
            Explore lançamentos, colaborações recentes e acesse o Instagram oficial de cada marca.
          </p>
          <div class="collections-grid" id="collections-grid"></div>
        </div>
      </section>
    </div>
  </main>

  <script src="assets/js/i18n.js?v={ASSET_VER}"></script>
  <script src="assets/js/main.js?v={ASSET_VER}"></script>
  <script src="assets/js/marcas-app.js?v={ASSET_VER}"></script>
</body>
</html>
"""
    (ROOT / "m4rcas.html").write_text(page, encoding="utf-8")
    print(f"[OK] m4rcas.html e assets/data/marcas.json gerados com {len(brands)} marcas!")


if __name__ == "__main__":
    main()
