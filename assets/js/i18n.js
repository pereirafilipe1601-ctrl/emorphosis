/* ==========================================================================
   EMORPHOSIS — Sistema Bilíngue (Português / Inglês)
   Persiste a escolha do usuário em localStorage ("emorphosis_lang") e atualiza
   automaticamente todos os elementos [data-i18n] e componentes dinâmicos.
   ========================================================================== */

(function () {
  const STORAGE_KEY = "emorphosis_lang";

  const DICT = {
    pt: {
      "brand.info_btn": "+ INFO",
      "home.dock_kicker": "DIRETÓRIO BRASILEIRO DE MODA INDEPENDENTE",
      "home.btn_catalog": "EXPLORAR 141 MARCAS",
      "home.btn_quiz": "QU1Z GRINGA → BR",
      "home.btn_fitlab": "MANEQUIM VIRTUAL",
      "home.btn_drops": "PRÓXIMOS DROPS",

      "marcas.tab_catalog": "CATÁL0G0 (141)",
      "marcas.tab_quiz": "QU1Z GRINGA → BR",
      "marcas.tab_collections": "C0L3ÇÕ3S & F1T LAB",
      "marcas.search_placeholder": "Buscar marca ou @instagram...",

      "marcas.menu_modes": "SEÇÃO DA PÁGINA:",
      "filter.menu_label": "FILTRAR CATEGORIA:",
      "filter.all": "TODAS",
      "filter.roupas": "ROUPAS",
      "filter.handmade": "HANDMADE",
      "filter.acessorios": "ACESSÓRIOS",
      "filter.calcados": "CALÇADOS",
      "filter.sob_medida": "SOB MEDIDA / ALFAIATARIA",
      "filter.upcycling": "UPCYCLING",
      "filter.diversos": "DIVERSOS",

      "price.sidebar_open_btn": "PREÇO & MÉDIA",
      "price.sidebar_kicker": "FILTRO INTERATIVO",
      "price.sidebar_title": "PREÇO & MÉDIA",
      "price.sidebar_min_btn": "MINIMIZAR",
      "price.slider_title_short": "PEÇAS ABAIXO DO VALOR:",
      "price.slider_sub_short": "Deslize para selecionar o valor máximo",
      "price.no_limit": "SEM LIMITE (141 MARCAS)",
      "price.reset_btn": "Limpar filtro",
      "price.apply_mobile_btn": "VER MARCAS ▸",
      "price.bound_all": "TODAS",
      "price.preset_all": "TODAS",
      "price.avg_label_short": "MÉDIA DE PREÇO DA MARCA:",
      "price.avg_sub_short": "(Peça mais barata + mais cara ÷ 2)",
      "price.sort_label": "ORDENAR CATÁLOGO:",
      "price.sort_az": "A–Z",
      "price.sort_avg_asc": "MENOR MÉDIA ↑",
      "price.sort_avg_desc": "MAIOR MÉDIA ↓",
      "price.sort_min_asc": "MAIS BARATA ↑",
      "price.tier_all": "TODAS (141)",
      "price.tier_priced": "COM MÉDIA MAPEADA (111)",
      "price.tier_200": "MÉDIA ATÉ R$ 200 (19)",
      "price.tier_350": "MÉDIA R$ 200 – R$ 350 (35)",
      "price.tier_600": "MÉDIA R$ 350 – R$ 600 (25)",
      "price.tier_over_600": "MÉDIA ACIMA DE R$ 600 (32)",
      "price.tier_consult": "DROP / SOB CONSULTA (30)",
      "price.card_avg": "MÉDIA:",
      "price.card_from": "MÍNIMO:",
      "price.card_to": "MÁXIMO:",
      "price.badge_consult": "DROP / SOB CONSULTA",

      "quiz.kicker": "CURADORIA INTERNACIONAL → NACIONAL",
      "quiz.title": "Encontre Marcas Brasileiras pelo seu Gosto",
      "quiz.subtitle":
        "Selecione marcas internacionais que você curte e responda 3 perguntas rápidas para descobrir marcas independentes brasileiras com estética próxima.",
      "quiz.step1":
        "1. Quais referências internacionais conversam com seu estilo? (escolha quantas quiser)",
      "quiz.step2": "2. Qual atmosfera visual você mais procura hoje?",
      "quiz.vibe_dark": "Darkwear / Avant-Garde / Gótico",
      "quiz.vibe_street": "Streetwear / Gráfico / Urbano",
      "quiz.vibe_minimal": "Alfaiataria / Minimalista / Clean",
      "quiz.vibe_diy": "Upcycling / Desconstruído / Punk DIY",
      "quiz.vibe_tech": "Modular / Techwear / Utilitário",
      "quiz.step3": "3. O que mais pesa na sua escolha?",
      "quiz.focus_any": "Qualquer peça (visão geral)",
      "quiz.focus_handmade": "Feito à mão / Tiragem limitada / 1of1",
      "quiz.focus_tailoring": "Corte sob medida / Caimento de alfaiataria",
      "quiz.focus_acc": "Acessórios, Chainmail & Joalheria Bruta",
      "quiz.focus_foot": "Botas & Calçados Autorais",
      "quiz.results_title": "Recomendações Brasileiras para Você",
      "quiz.reset": "Limpar seleção",

      "fit.kicker": "PROTÓTIPO INTERATIVO · FIT LAB",
      "fit.title": "Manequim Virtual — Montador de Fits",
      "fit.subtitle":
        "Combine peças por camada (Acessório, Parte Superior, Calça e Calçado) de marcas do diretório Emorphosis para visualizar paleta, proporção e descobrir combinações.",
      "fit.png_note": "Pronto para receber recortes PNG reais das peças das marcas.",
      "fit.custom_kicker": "ACERVO PESSOAL PRIVADO · SÓ VOCÊ VÊ",
      "fit.custom_title": "Enviar e Recortar Sua Própria Peça",
      "fit.custom_sub":
        "Envie a foto de uma roupa ou acessório. O site remove o fundo automaticamente, recorta a peça e adiciona à sua coleção pessoal no Manequim Virtual (disponível apenas para você neste navegador).",
      "fit.slot_label": "1. Categoria / Camada no Manequim",
      "fit.slot_top": "Parte Superior / Top (Jaqueta, Camiseta, Moletom)",
      "fit.slot_bottom": "Parte Inferior / Calça (Calça, Bermuda, Saia)",
      "fit.slot_acc": "Acessório / Headwear (Boné, Gorro, Bolsa, Joia)",
      "fit.slot_shoes": "Calçado / Footwear (Bota, Tênis, Sapato)",
      "fit.piece_name_label": "2. Nome da Peça",
      "fit.piece_name_ph": "Ex: Minha Jaqueta Estruturada, Calça Baggy...",
      "fit.piece_brand_label": "3. Marca ou Identificação (opcional)",
      "fit.piece_brand_ph": "Ex: Acervo Pessoal, Peça Autoral...",
      "fit.upload_btn": "📷 ESCOLHER FOTO DA ROUPA (RECORTE AUTOMÁTICO)",
      "fit.tolerance_label": "Sensibilidade do Recorte de Fundo:",
      "fit.inner_pockets_label": "Remover vãos internos do fundo (ex: entre as pernas da calça)",
      "fit.preview_hint": "Dica: você também pode clicar em qualquer ponto do fundo na prévia para apagar aquela cor.",
      "fit.reset_clicks_btn": "Restaurar recorte padrão",
      "fit.save_piece_btn": "+ ADICIONAR À MINHA COLEÇÃO E VESTIR NO MANEQUIM",
      "fit.my_collection_title": "Minha Coleção Pessoal (Visível Apenas para Você)",
      "fit.empty_collection": "Você ainda não adicionou peças pessoais. Envie uma foto acima para recortar e testar no manequim.",

      "col.kicker": "ARQUIVO & LOOKBOOKS",
      "col.title": "Coleções & Drops em Destaque",
      "col.subtitle":
        "Explore lançamentos, colaborações recentes e acesse o Instagram oficial de cada marca.",

      "sub.kicker": "ALERTA DE DROPS · 1 HORA ANTES",
      "sub.title": "Inscreva-se nas Marcas para Avisos de Drop",
      "sub.subtitle":
        "Selecione as marcas que você acompanha (ou todas do catálogo) e cadastre seu e-mail. Quando faltar 1 hora para o drop começar, enviaremos um aviso com a marca, o horário exato e o link direto do Instagram.",
      "sub.email_ph": "Digite seu melhor e-mail...",
      "sub.filter_ph": "Filtrar marcas para selecionar...",
      "sub.select_all": "★ TODAS AS MARCAS (141)",
      "sub.clear_btn": "Limpar marcas",
      "sub.submit_btn": "INSCREVER-SE NOS DROPS (AVISO 1H ANTES)",

      "cal.kicker": "RADAR & AUTOMAÇÃO DE LANÇAMENTOS",
      "cal.form_title": "Sugerir Drop ou Receber Avisos",
      "cal.form_sub":
        "Conhece um lançamento nacional que vai acontecer ou quer receber alertas dos próximos drops? Envie abaixo para alimentar nosso calendário.",
      "cal.email_ph": "Seu e-mail (para alertas)",
      "cal.brand_ph": "Nome da marca ou @instagram",
      "cal.link_ph": "Link do post / anúncio do drop (opcional)",
      "cal.submit_btn": "ENVIAR PARA O RADAR",

      "sobre.kicker": "MANIFESTO & CONEXÃO NACIONAL",
      "sobre.title": "EMORPHOSIS — Ecossistema da Moda Independente Brasileira",
      "sobre.p1":
        "A Emorphosis nasceu para catalogar, conectar e amplificar marcas independentes, ateliês autorais e criadores experimentais de todo o Brasil em uma única plataforma viva.",
      "sobre.p2":
        "Nossa meta é consolidar a Emorphosis entre as 5 principais plataformas e referências de moda independente do Brasil — conectando referências globais à produção autoral brasileira, organizando o calendário de drops e criando ferramentas interativas de descoberta.",
      "sobre.stat1_label": "Marcas Brasileiras Catalogadas",
      "sobre.stat2_label": "Polos Criativos (BR + UK)",
      "sobre.stat3_label": "Meta de Referência Nacional",
      "sobre.team_kicker": "NÚCLEO CRIATIVO & OPERACIONAL",
      "sobre.team_title": "Equipe Emorphosis",
      "sobre.role_giovane":
        "Implementação de features no site, arquitetura web e filtros interativos Gringa → BR.",
      "sobre.role_kimura":
        "Direção criativa, design visual e identidade estética do projeto.",
      "sobre.role_vito":
        "Edição de vídeo, marketing, confecção de peças e pesquisa de marcas internacionais equivalentes.",
      "sobre.role_pedro":
        "Design, vetorização, arte-final, ilustração digital e conexão entre marcas da gringa e do Brasil.",
      "sobre.role_marlon":
        "Conexões estratégicas, curadoria de referências e otimização do ecossistema.",

      "marca.back": "← VOLTAR PARA M4RCAS",
      "marca.open_ig": "ABRIR INSTAGRAM OFICIAL ↗",
      "marca.about_title": "Sobre & Identidade",
      "marca.drops_title": "Coleções Passadas & Radar de Drops",
      "marca.care_title": "Instruções Padronizadas de Lavagem & Conservação",
      "marca.related_title": "Marcas Brasileiras na Mesma Atmosfera"
    },

    en: {
      "brand.info_btn": "+ INFO",
      "home.dock_kicker": "BRAZILIAN INDEPENDENT FASHION DIRECTORY",
      "home.btn_catalog": "EXPLORE 141 BRANDS",
      "home.btn_quiz": "INTL → BR QUIZ",
      "home.btn_fitlab": "VIRTUAL MANNEQUIN",
      "home.btn_drops": "UPCOMING DROPS",

      "marcas.tab_catalog": "CATAL0G (141)",
      "marcas.tab_quiz": "INTL → BR QU1Z",
      "marcas.tab_collections": "C0LL3CTI0NS & F1T LAB",
      "marcas.search_placeholder": "Search brand or @instagram...",

      "marcas.menu_modes": "PAGE SECTION:",
      "filter.menu_label": "CATEGORY FILTER:",
      "filter.all": "ALL",
      "filter.roupas": "APPAREL",
      "filter.handmade": "HANDMADE",
      "filter.acessorios": "ACCESSORIES",
      "filter.calcados": "FOOTWEAR",
      "filter.sob_medida": "BESPOKE / TAILORING",
      "filter.upcycling": "UPCYCLING",
      "filter.diversos": "OBJECTS & MISC",

      "price.sidebar_open_btn": "PRICE & AVG",
      "price.sidebar_kicker": "INTERACTIVE FILTER",
      "price.sidebar_title": "PRICE & AVG",
      "price.sidebar_min_btn": "MINIMIZE",
      "price.slider_title_short": "PIECES BELOW PRICE:",
      "price.slider_sub_short": "Slide to select max piece price",
      "price.no_limit": "NO LIMIT (141 BRANDS)",
      "price.reset_btn": "Reset filter",
      "price.apply_mobile_btn": "VIEW BRANDS ▸",
      "price.bound_all": "ALL",
      "price.preset_all": "ALL",
      "price.avg_label_short": "BRAND AVERAGE PRICE:",
      "price.avg_sub_short": "(Cheapest + most expensive ÷ 2)",
      "price.sort_label": "SORT CATALOG:",
      "price.sort_az": "A–Z",
      "price.sort_avg_asc": "LOWEST AVG ↑",
      "price.sort_avg_desc": "HIGHEST AVG ↓",
      "price.sort_min_asc": "CHEAPEST ↑",
      "price.tier_all": "ALL (141)",
      "price.tier_priced": "MAPPED AVERAGE (111)",
      "price.tier_200": "AVG UP TO R$ 200 (19)",
      "price.tier_350": "AVG R$ 200 – R$ 350 (35)",
      "price.tier_600": "AVG R$ 350 – R$ 600 (25)",
      "price.tier_over_600": "AVG OVER R$ 600 (32)",
      "price.tier_consult": "DROP / ON REQUEST (30)",
      "price.card_avg": "AVG:",
      "price.card_from": "MIN:",
      "price.card_to": "MAX:",
      "price.badge_consult": "DROP / ON REQUEST",

      "quiz.kicker": "INTERNATIONAL → BRAZILIAN CURATION",
      "quiz.title": "Find Brazilian Brands Matching Your Taste",
      "quiz.subtitle":
        "Pick international labels you admire and answer 3 quick questions to discover independent Brazilian brands with a kindred aesthetic.",
      "quiz.step1":
        "1. Which international references resonate with your style? (pick as many as you like)",
      "quiz.step2": "2. Which visual atmosphere are you looking for right now?",
      "quiz.vibe_dark": "Darkwear / Avant-Garde / Gothic",
      "quiz.vibe_street": "Streetwear / Graphic / Urban",
      "quiz.vibe_minimal": "Tailoring / Minimalist / Clean",
      "quiz.vibe_diy": "Upcycling / Deconstructed / DIY Punk",
      "quiz.vibe_tech": "Modular / Techwear / Utilitarian",
      "quiz.step3": "3. What matters most in a piece?",
      "quiz.focus_any": "Any category (full overview)",
      "quiz.focus_handmade": "Handmade / Limited run / 1-of-1",
      "quiz.focus_tailoring": "Bespoke cut / Tailored drape",
      "quiz.focus_acc": "Accessories, Chainmail & Raw Jewelry",
      "quiz.focus_foot": "Artisanal Boots & Footwear",
      "quiz.results_title": "Brazilian Recommendations for You",
      "quiz.reset": "Reset filters",

      "fit.kicker": "INTERACTIVE PROTOTYPE · FIT LAB",
      "fit.title": "Virtual Mannequin — Fit Builder",
      "fit.subtitle":
        "Mix & match layers (Headwear/Accessory, Top, Trousers, and Footwear) from Emorphosis directory brands to preview proportions, palettes, and full-fit combinations.",
      "fit.png_note": "Ready to load real transparent PNG garment cutouts from brands.",
      "fit.custom_kicker": "PRIVATE PERSONAL WARDROBE · ONLY YOU CAN SEE",
      "fit.custom_title": "Upload & Cut Out Your Own Garment",
      "fit.custom_sub":
        "Upload a photo of a garment or accessory. The site automatically removes the background, crops the item, and adds it to your personal collection on the Virtual Mannequin (visible only to you in this browser).",
      "fit.slot_label": "1. Mannequin Layer / Category",
      "fit.slot_top": "Upper Body / Top (Jacket, Tee, Hoodie)",
      "fit.slot_bottom": "Lower Body / Trousers (Pants, Shorts, Skirt)",
      "fit.slot_acc": "Headwear / Accessory (Cap, Beanie, Bag, Jewelry)",
      "fit.slot_shoes": "Footwear (Boots, Sneakers, Derby)",
      "fit.piece_name_label": "2. Garment Name",
      "fit.piece_name_ph": "E.g., My Leather Jacket, Baggy Denim...",
      "fit.piece_brand_label": "3. Brand or Label (optional)",
      "fit.piece_brand_ph": "E.g., Personal Wardrobe, Custom Piece...",
      "fit.upload_btn": "📷 CHOOSE GARMENT PHOTO (AUTO CUTOUT)",
      "fit.tolerance_label": "Background Cutout Sensitivity:",
      "fit.inner_pockets_label": "Remove enclosed background gaps (e.g. between trouser legs)",
      "fit.preview_hint": "Tip: you can also click any background spot in the preview to erase that color.",
      "fit.reset_clicks_btn": "Reset cutout clicks",
      "fit.save_piece_btn": "+ ADD TO MY COLLECTION & EQUIP ON MANNEQUIN",
      "fit.my_collection_title": "My Personal Collection (Visible Only to You)",
      "fit.empty_collection": "You haven't added personal garments yet. Upload a photo above to cut out and test on the mannequin.",

      "col.kicker": "ARCHIVE & LOOKBOOKS",
      "col.title": "Featured Brand Collections & Drops",
      "col.subtitle":
        "Explore recent drops, collaborations, and open each brand's official Instagram.",

      "sub.kicker": "DROP ALERTS · 1 HOUR BEFORE",
      "sub.title": "Subscribe to Brands for Drop Alerts",
      "sub.subtitle":
        "Select the brands you follow (or all catalog brands) and enter your email. When a drop is 1 hour away, you'll receive an alert with the brand name, exact drop time, and direct Instagram link.",
      "sub.email_ph": "Enter your best email...",
      "sub.filter_ph": "Filter brands to select...",
      "sub.select_all": "★ ALL BRANDS (141)",
      "sub.clear_btn": "Clear selection",
      "sub.submit_btn": "SUBSCRIBE TO DROP ALERTS (1H PRIOR)",

      "cal.kicker": "DROP RADAR & AUTOMATION",
      "cal.form_title": "Submit a Drop or Subscribe to Alerts",
      "cal.form_sub":
        "Know an upcoming Brazilian drop or want release reminders? Submit below to feed our curated calendar.",
      "cal.email_ph": "Your email (for drop alerts)",
      "cal.brand_ph": "Brand name or @instagram",
      "cal.link_ph": "Instagram post / drop link (optional)",
      "cal.submit_btn": "SEND TO RADAR",

      "sobre.kicker": "MANIFESTO & NATIONAL SCENE",
      "sobre.title": "EMORPHOSIS — Brazilian Independent Fashion Ecosystem",
      "sobre.p1":
        "Emorphosis was built to catalog, connect, and amplify independent labels, artisanal ateliers, and experimental designers from across Brazil in one living platform.",
      "sobre.p2":
        "Our goal is to establish Emorphosis among the top 5 independent fashion platforms and references in Brazil — bridging global references with local artisanal creation, tracking drops, and building interactive discovery tools.",
      "sobre.stat1_label": "Cataloged Brazilian Brands",
      "sobre.stat2_label": "Creative Hubs (BR + UK)",
      "sobre.stat3_label": "National Platform Vision",
      "sobre.team_kicker": "CREATIVE & TECH COLLECTIVE",
      "sobre.team_title": "Emorphosis Team",
      "sobre.role_giovane":
        "Website feature engineering, web architecture, and interactive Intl → BR filter systems.",
      "sobre.role_kimura":
        "Creative direction, visual design, and aesthetic identity of the project.",
      "sobre.role_vito":
        "Video editing, marketing, garment making, and international reference scouting.",
      "sobre.role_pedro":
        "Design, vectorization, final artwork, digital illustration, and Intl ↔ Brazil brand mapping.",
      "sobre.role_marlon":
        "Strategic connections, cultural reference research, and ecosystem optimization.",

      "marca.back": "← BACK TO M4RCAS",
      "marca.open_ig": "OPEN OFFICIAL INSTAGRAM ↗",
      "marca.about_title": "About & Identity",
      "marca.drops_title": "Past Collections & Drop Radar",
      "marca.care_title": "Standardized Washing & Garment Care Guide",
      "marca.related_title": "Kindred Brazilian Brands"
    }
  };

  function getLang() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "en" || saved === "pt") return saved;
    } catch (_) {}
    return "pt";
  }

  function t(key, fallback) {
    const lang = getLang();
    if (DICT[lang] && DICT[lang][key] !== undefined) {
      return DICT[lang][key];
    }
    if (DICT.pt[key] !== undefined) {
      return DICT.pt[key];
    }
    return fallback !== undefined ? fallback : key;
  }

  function apply(root) {
    const scope = root || document;
    const lang = getLang();
    document.documentElement.lang = lang === "en" ? "en" : "pt-BR";

    scope.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (DICT[lang] && DICT[lang][key] !== undefined) {
        el.textContent = DICT[lang][key];
      }
    });

    scope.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (DICT[lang] && DICT[lang][key] !== undefined) {
        el.setAttribute("placeholder", DICT[lang][key]);
      }
    });

    document.querySelectorAll("[data-lang-btn]").forEach((btn) => {
      const isActive = btn.getAttribute("data-lang-btn") === lang;
      btn.classList.toggle("active", isActive);
      btn.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
  }

  function setLang(lang) {
    const next = lang === "en" ? "en" : "pt";
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (_) {}
    apply(document);
    window.dispatchEvent(new CustomEvent("emorphosis:langchange", { detail: { lang: next } }));
  }

  document.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-lang-btn]");
    if (!btn) return;
    setLang(btn.getAttribute("data-lang-btn"));
  });

  document.addEventListener("keydown", (ev) => {
    if (ev.key !== "Enter" && ev.key !== " ") return;
    const btn = ev.target.closest("[data-lang-btn]");
    if (!btn) return;
    ev.preventDefault();
    setLang(btn.getAttribute("data-lang-btn"));
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => apply(document));
  } else {
    apply(document);
  }

  window.EmorphosisI18n = { getLang, setLang, t, apply };
})();
