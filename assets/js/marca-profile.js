/* ==========================================================================
   EMORPHOSIS — Página Padronizada de Marca (marca.html?m=<slug>)
   Exibe informações da marca, conexões internacionais equivalentes, arquivo de
   coleções/drops, guia padronizado de lavagem/conservação e marcas próximas.
   ========================================================================== */

(function () {
  const i18n = () => window.EmorphosisI18n || { getLang: () => "pt", t: (k, f) => f || k };
  let allBrands = [];

  const CAT_LABELS = {
    pt: {
      roupas: "Vestuário Autoral",
      handmade: "Feito à Mão (Handmade)",
      acessorios: "Acessórios & Metais",
      calcados: "Calçados & Botas",
      "sob medida": "Sob Medida / Alfaiataria",
      alfaiataria: "Alfaiataria",
      upcycling: "Upcycling & Reconstrução",
      modular: "Design Modular",
      artisanal: "Artesanal",
      retail: "Curadoria & Retail",
      diversos: "Objetos & Projetos Visuais"
    },
    en: {
      roupas: "Independent Apparel",
      handmade: "Handmade",
      acessorios: "Accessories & Metalwork",
      calcados: "Footwear & Boots",
      "sob medida": "Bespoke / Made-to-Measure",
      alfaiataria: "Tailoring",
      upcycling: "Upcycling & Reconstruction",
      modular: "Modular Design",
      artisanal: "Artisanal",
      retail: "Curation & Retail",
      diversos: "Objects & Visual Projects"
    }
  };

  const INTL_BRIDGE = {
    avantgarde: ["Rick Owens", "Yohji Yamamoto", "Maison Margiela"],
    darkwear: ["Rick Owens", "Enfants Riches Déprimés", "Undercover"],
    punk: ["Enfants Riches Déprimés", "Undercover", "Chrome Hearts"],
    upcycling: ["Maison Margiela", "Greg Lauren", "Undercover"],
    tailoring: ["Our Legacy", "Yohji Yamamoto", "Aimé Leon Dore"],
    minimal: ["Our Legacy", "Aimé Leon Dore", "Jil Sander"],
    gorpcore: ["Acronym", "ROA", "Arc'teryx System_A"],
    techwear: ["Acronym", "Cav Empt"],
    cyber: ["Cav Empt", "Balenciaga"],
    footwear: ["Guidi", "Rick Owens Footwear", "ROA"],
    accessories: ["Chrome Hearts", "Parts of Four"],
    streetwear: ["Stüssy", "Palace", "Corteiz"],
    contemporary: ["Our Legacy", "Stüssy"]
  };

  const KNOWN_ARCHIVES = {
    bussfly: [
      { pt: "Drop Bussfly — Cápsula Oficial registrada no C4L3NDAR10", en: "Bussfly Drop — Official capsule tracked on C4L3NDAR10" }
    ],
    duck: [
      { pt: "Drop Duck Pt.2 — Lançamento registrado no C4L3NDAR10", en: "Duck Drop Pt.2 — Release tracked on C4L3NDAR10" }
    ],
    wordly: [
      { pt: "Collab Wordly + Dismorfia — Cápsula conjunta", en: "Wordly + Dismorfia Collab — Joint capsule" }
    ],
    dismorfia: [
      { pt: "Internet Radio Dismorfia + Wordly — Roupas, mídia & bandeiras", en: "Internet Radio Dismorfia + Wordly — Apparel, radio & flags" }
    ]
  };

  function getCareInstructions(cats, lang) {
    const isEn = lang === "en";
    if (cats.includes("calcados")) {
      return isEn
        ? [
            { icon: "◈", title: "Surface Cleaning", text: "Wipe dust and dirt with a slightly damp soft cloth; never submerge or machine wash." },
            { icon: "◈", title: "Leather Conditioning", text: "Apply neutral leather balm periodically to prevent cracking and preserve natural grain." },
            { icon: "◈", title: "Shade Drying", text: "Dry naturally in a ventilated area away from direct sun or heat sources." },
            { icon: "◈", title: "Structure Storage", text: "Use shoe trees or acid-free paper stuffing to preserve toe-box silhouette." }
          ]
        : [
            { icon: "◈", title: "Limpeza Superficial", text: "Remova poeira e resíduos com pano macio levemente úmido; nunca mergulhe em água nem use máquina." },
            { icon: "◈", title: "Hidratação do Couro", text: "Hidrate periodicamente com cera ou condicionador neutro para evitar ressecamento." },
            { icon: "◈", title: "Secagem à Sombra", text: "Deixe arejar naturalmente à sombra, longe do sol direto ou secadores." },
            { icon: "◈", title: "Preservação de Forma", text: "Guarde com preenchimento interno ou forma de madeira para manter a estrutura." }
          ];
    }

    if (cats.includes("acessorios")) {
      return isEn
        ? [
            { icon: "◈", title: "Avoid Chemicals", text: "Avoid direct contact with perfume, chlorine, seawater, or abrasive cleaners." },
            { icon: "◈", title: "Post-Wear Wipe", text: "Gently wipe chainmail or metal links with a dry microfiber cloth after wearing." },
            { icon: "◈", title: "Dry Storage", text: "Store individually in a dry pouch to prevent oxidation and tangling." },
            { icon: "◈", title: "Hand Polishing", text: "Use a dedicated metal/silver polishing cloth when luster softens." }
          ]
        : [
            { icon: "◈", title: "Evitar Químicos", text: "Evite contato direto com perfumes, cloro, mar ou produtos abrasivos." },
            { icon: "◈", title: "Pós-Uso", text: "Limpe os elos/metais suavemente com flanela seca após o uso para remover umidade." },
            { icon: "◈", title: "Armazenamento Individual", text: "Guarde em saquinho seco separado para evitar atrito e oxidação." },
            { icon: "◈", title: "Polimento Suave", text: "Utilize flanela própria para metais/aço/prata para restaurar o brilho." }
          ];
    }

    if (cats.includes("sob medida") || cats.includes("alfaiataria")) {
      return isEn
        ? [
            { icon: "◈", title: "Dry Clean or Cold Hand Wash", text: "Prefer professional dry cleaning or gentle cold wash to protect interfacing and drape." },
            { icon: "◈", title: "Steam / Press Inside Out", text: "Use a garment steamer or low-heat iron with a pressing cloth on the reverse side." },
            { icon: "◈", title: "Contoured Hanger", text: "Hang on wide-shoulder hangers to maintain shoulder and pleat geometry." },
            { icon: "◈", title: "No Tumble Dry", text: "Never tumble dry; air dry flat or hung in the shade." }
          ]
        : [
            { icon: "◈", title: "Lavagem a Seco ou Manual Fria", text: "Prefira lavanderia especializada a seco ou lavagem manual fria para preservar entretelas e caimento." },
            { icon: "◈", title: "Vaporização pelo Avesso", text: "Utilize steamer/vaporizador ou ferro em baixa temperatura com pano protetor pelo avesso." },
            { icon: "◈", title: "Cabide Anatômico", text: "Guarde em cabide estruturado largo para manter alinhamento de ombros e pregas." },
            { icon: "◈", title: "Zero Secadora", text: "Nunca utilize máquina secadora; seque sempre à sombra em local ventilado." }
          ];
    }

    if (cats.includes("handmade") || cats.includes("upcycling") || cats.includes("artisanal")) {
      return isEn
        ? [
            { icon: "30°", title: "Cold Hand Wash Only", text: "Wash gently by hand in cold water inside out using mild neutral soap." },
            { icon: "✕", title: "Do Not Wring or Bleach", text: "Do not twist seams, distress points, or custom hardware; never use bleach." },
            { icon: "▭", title: "Dry Flat in Shade", text: "Lay flat on a towel in the shade so wet weight does not stretch handmade knit/stitching." },
            { icon: "♨", title: "Low Indirect Steam", text: "Steam lightly from a distance; avoid direct iron contact on patches or raw edges." }
          ]
        : [
            { icon: "30°", title: "Lavagem Manual Fria", text: "Lave exclusivamente à mão em água fria, pelo avesso, com sabão neutro líquido." },
            { icon: "✕", title: "Não Torcer / Sem Alvejante", text: "Não torça recorte artesanal, aviamentos ou costuras expostas; zero cloro/alvejante." },
            { icon: "▭", title: "Secagem Horizontal à Sombra", text: "Seque na horizontal à sombra para que o peso da água não deforme a modelagem." },
            { icon: "♨", title: "Vapor Leve Indireto", text: "Prefira vapor leve à distância; nunca encoste o ferro quente sobre aplicações." }
          ];
    }

    return isEn
      ? [
          { icon: "30°", title: "Cold Gentle Wash (Inside Out)", text: "Wash at max 30°C inside out to protect heavyweight cotton fibers and screenprints." },
          { icon: "✕", title: "No Bleach / No Dryer", text: "Avoid bleach and tumble dryers to prevent shrinkage and print cracking." },
          { icon: "☀", title: "Line Dry in Shade", text: "Hang dry in the shade; direct sun fades dark dyes prematurely." },
          { icon: "♨", title: "Iron Reverse Side Only", text: "Iron on low heat inside out — never iron directly over graphics or labels." }
        ]
      : [
          { icon: "30°", title: "Lavagem Fria pelo Avesso (máx. 30°C)", text: "Lave sempre do avesso em água fria/ciclo delicado para proteger fibras e serigrafia." },
          { icon: "✕", title: "Sem Alvejante / Sem Secadora", text: "Não utilize cloro nem secadora térmica para evitar encolhimento e craquelado na estampa." },
          { icon: "☀", title: "Secagem à Sombra", text: "Seque pendurado à sombra para preservar tingimentos escuros e estonados." },
          { icon: "♨", title: "Passar Sempre pelo Avesso", text: "Passe em temperatura baixa pelo avesso, nunca diretamente sobre estampas ou etiquetas." }
        ];
  }

  function buildAboutText(brand, lang) {
    const cats = brand.categories || [];
    const catDict = CAT_LABELS[lang] || CAT_LABELS.pt;
    const catReadable = cats.length
      ? cats.map((c) => catDict[c] || c).join(", ")
      : lang === "en"
        ? "Independent Brazilian Label"
        : "Marca Independente Brasileira";

    if (lang === "en") {
      return `${brand.name} (@${brand.handle}) is part of the curated Emorphosis directory of independent Brazilian fashion, operating with focus on ${catReadable}. Each release follows independent drop cycles announced through the brand's official channels and tracked in our national release calendar.`;
    }
    return `${brand.name} (@${brand.handle}) integra o diretório curado da Emorphosis de moda autoral e independente brasileira, com atuação destacada em ${catReadable}. Seus lançamentos seguem ciclos independentes de drops acompanhados pelos canais oficiais da marca e pelo nosso calendário unificado.`;
  }

  function getIntlEquivalents(brand) {
    const out = [];
    (brand.vibes || []).forEach((v) => {
      (INTL_BRIDGE[v] || []).forEach((name) => {
        if (!out.includes(name)) out.push(name);
      });
    });
    return out.slice(0, 4);
  }

  function renderProfile() {
    const root = document.getElementById("brand-profile-root");
    if (!root || !allBrands.length) return;

    const params = new URLSearchParams(window.location.search);
    const slug = (params.get("m") || "").toLowerCase().trim();
    const brand =
      allBrands.find((b) => b.slug === slug || b.handle.toLowerCase() === slug) || allBrands[0];

    const lang = i18n().getLang();
    document.title = `${brand.name} — emorphosis.com.br`;

    const catDict = CAT_LABELS[lang] || CAT_LABELS.pt;
    const catsHtml = (brand.categories && brand.categories.length ? brand.categories : ["roupas"])
      .map((c) => `<span class="profile-badge">${catDict[c] || c}</span>`)
      .join("");

    const intlList = getIntlEquivalents(brand);
    const intlHtml = intlList
      .map((n) => `<span class="mini-tag">${n}</span>`)
      .join("");

    const careItems = getCareInstructions(brand.categories || [], lang)
      .map(
        (c) => `
        <div class="care-card">
          <div class="care-icon">${c.icon}</div>
          <div>
            <h4>${c.title}</h4>
            <p>${c.text}</p>
          </div>
        </div>
      `
      )
      .join("");

    const archives = KNOWN_ARCHIVES[brand.slug] || [];
    const dropsHtml = archives.length
      ? archives
          .map((item) => `<li class="archive-item">● ${lang === "en" ? item.en : item.pt}</li>`)
          .join("")
      : `<li class="archive-item">${
          lang === "en"
            ? "Independent seasonal drops & limited capsules — check live release dates on C4L3NDAR10 and official Instagram."
            : "Lançamentos por drops independentes e tiragens limitadas — acompanhe as próximas datas no C4L3NDAR10 e no Instagram oficial."
        }</li>`;

    const related = allBrands
      .filter((b) => b.slug !== brand.slug)
      .map((b) => {
        let s = 0;
        (b.categories || []).forEach((c) => {
          if ((brand.categories || []).includes(c)) s += 3;
        });
        (b.vibes || []).forEach((v) => {
          if ((brand.vibes || []).includes(v)) s += 2;
        });
        return { b, s };
      })
      .sort((a, b) => b.s - a.s || a.b.name.localeCompare(b.b.name))
      .slice(0, 3)
      .map(
        ({ b }) => `
        <a href="marca.html?m=${b.slug}" class="related-brand-card">
          <img src="${b.img}" alt="${b.name}" width="56" height="56" loading="lazy" />
          <div>
            <strong>${b.name}</strong>
            <span>@${b.handle}</span>
          </div>
        </a>
      `
      )
      .join("");

    root.innerHTML = `
      <section class="glass-box profile-hero">
        <img src="${brand.img}" alt="${brand.name}" class="profile-logo" width="150" height="150" />
        <div class="profile-hero-info">
          <div class="profile-badges">${catsHtml}</div>
          <h1 class="profile-name">${brand.name}</h1>
          <p class="profile-handle">@${brand.handle}</p>
          <div class="profile-cta-row">
            <a href="${brand.url}" target="_blank" rel="noopener noreferrer" class="btn-solid-green">
              ${i18n().t("marca.open_ig")}
            </a>
            <a href="c4l3ndar10.html" class="btn-outline-sm">
              ${lang === "en" ? "CHECK DROP CALENDAR" : "VER C4L3NDAR10 DE DROPS"}
            </a>
          </div>
        </div>
      </section>

      <div class="profile-two-col">
        <section class="glass-box">
          <h2 class="profile-sec-title">${i18n().t("marca.about_title")}</h2>
          <p class="profile-body-text">${buildAboutText(brand, lang)}</p>
          ${
            intlHtml
              ? `<div class="intl-bridge-box">
                  <span class="bridge-label">${
                    lang === "en"
                      ? "Global Aesthetic Parallels (Intl → BR):"
                      : "Conexões Estéticas Internacionais (Gringa → BR):"
                  }</span>
                  <div class="mini-tags">${intlHtml}</div>
                </div>`
              : ""
          }
        </section>

        <section class="glass-box">
          <h2 class="profile-sec-title">${i18n().t("marca.drops_title")}</h2>
          <ul class="archive-list">${dropsHtml}</ul>
          <a href="c4l3ndar10.html#radar-drops" class="inline-green-link">
            ${
              lang === "en"
                ? "+ Submit a new drop or lookbook for this brand →"
                : "+ Sugerir novo drop ou acervo desta marca →"
            }
          </a>
        </section>
      </div>

      <section class="glass-box">
        <h2 class="profile-sec-title">${i18n().t("marca.care_title")}</h2>
        <div class="care-grid">${careItems}</div>
      </section>

      <section class="glass-box">
        <h2 class="profile-sec-title">${i18n().t("marca.related_title")}</h2>
        <div class="related-grid">${related}</div>
      </section>
    `;
  }

  async function init() {
    try {
      const res = await fetch("assets/data/marcas.json");
      if (res.ok) allBrands = await res.json();
    } catch (_) {}
    renderProfile();
  }

  init();
  window.addEventListener("emorphosis:langchange", renderProfile);
})();
