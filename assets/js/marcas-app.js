/* ==========================================================================
   EMORPHOSIS — M4RCAS Interactive App
   1. Busca grande centralizada no topo + Filtro por categoria no grid 3xN
   2. Sub-abas: Catálogo 3xN | Quiz Gringa -> BR | Coleções & Fit Lab
   3. Motor de recomendação Referências Internacionais -> Marcas Brasileiras
   4. Manequim Virtual (Fit Builder por camadas) + Arquivo de Coleções
   ========================================================================== */

(function () {
  const i18n = () => window.EmorphosisI18n || { getLang: () => "pt", t: (k, f) => f || k };

  let brandsData = [];
  let activeFilter = "all";
  let searchQuery = "";
  let currentSubtab = "catalogo";

  // Estado do Filtro Interativo de Média de Preço + Barra Deslizante de Valor (Barra Lateral)
  const SLIDER_NO_LIMIT = 700;
  let sliderMaxPrice = SLIDER_NO_LIMIT;
  let activeAvgTier = "all";
  let activePriceSort = "az";
  let isPriceSidebarMinimized = typeof window !== "undefined" && window.innerWidth <= 1180;

  // Estado do Quiz Gringa -> BR
  const selectedIntl = new Set();
  let selectedVibe = "";
  let selectedFocus = "all";

  // Referências internacionais mapeadas para atmosferas e categorias brasileiras
  const INTL_REFS = [
    { name: "Rick Owens", vibes: ["avantgarde", "darkwear", "footwear"] },
    { name: "Maison Margiela", vibes: ["avantgarde", "upcycling", "tailoring"] },
    { name: "Chrome Hearts", vibes: ["accessories", "darkwear", "punk"] },
    { name: "Stüssy", vibes: ["streetwear", "graphic"] },
    { name: "Acronym", vibes: ["gorpcore", "techwear"] },
    { name: "Our Legacy", vibes: ["minimal", "tailoring", "contemporary"] },
    { name: "Enfants Riches Déprimés", vibes: ["punk", "darkwear", "graphic"] },
    { name: "Yohji Yamamoto", vibes: ["avantgarde", "tailoring", "darkwear"] },
    { name: "Corteiz", vibes: ["streetwear", "graphic"] },
    { name: "Cav Empt", vibes: ["cyber", "streetwear", "graphic"] },
    { name: "Aimé Leon Dore", vibes: ["minimal", "contemporary", "tailoring"] },
    { name: "Guidi", vibes: ["footwear", "artisanal", "avantgarde"] },
    { name: "Undercover", vibes: ["punk", "avantgarde", "graphic"] },
    { name: "Balenciaga", vibes: ["avantgarde", "cyber", "streetwear"] },
    { name: "Palace", vibes: ["streetwear", "graphic"] },
    { name: "ROA / Arc'teryx", vibes: ["gorpcore", "footwear"] }
  ];

  const VIBE_LABELS = {
    pt: {
      avantgarde: "Avant-Garde",
      darkwear: "Darkwear",
      punk: "Punk / Underground",
      graphic: "Gráfico",
      streetwear: "Streetwear",
      contemporary: "Contemporâneo",
      minimal: "Minimal",
      tailoring: "Alfaiataria",
      upcycling: "Upcycling",
      artisanal: "Artesanal",
      gorpcore: "Gorpcore / Modular",
      techwear: "Techwear",
      cyber: "Cyber",
      archive: "Archive",
      experimental: "Experimental",
      accessories: "Acessórios",
      footwear: "Calçados"
    },
    en: {
      avantgarde: "Avant-Garde",
      darkwear: "Darkwear",
      punk: "Punk / Underground",
      graphic: "Graphic",
      streetwear: "Streetwear",
      contemporary: "Contemporary",
      minimal: "Minimal",
      tailoring: "Tailoring",
      upcycling: "Upcycling",
      artisanal: "Artisanal",
      gorpcore: "Gorpcore / Modular",
      techwear: "Techwear",
      cyber: "Cyber",
      archive: "Archive",
      experimental: "Experimental",
      accessories: "Accessories",
      footwear: "Footwear"
    }
  };

  // Peças por camada para o Manequim Virtual (Fit Lab)
  const FIT_SLOTS = [
    {
      id: "acc",
      labelPt: "Acessório / Headwear",
      labelEn: "Headwear / Accessory",
      items: [
        {
          slug: "drestudio",
          brand: "Drestudio",
          piecePt: "Boné Estruturado em Relevo",
          pieceEn: "Embossed Structured Cap",
          cutout: "assets/img/fitlab/drestudio-bone.png",
          comingSoon: true,
          fill: "#19f028",
          stroke: "#52ff5e"
        },
        {
          slug: "ablaze",
          brand: "Ablaze",
          piecePt: "Coifa & Choker Chainmail Artesanal",
          pieceEn: "Artisanal Chainmail Coif & Choker",
          fill: "#19f028",
          stroke: "#52ff5e"
        },
        {
          slug: "vinegar",
          brand: "Vinegar Archive",
          piecePt: "Corrente & Óculos Archive",
          pieceEn: "Archive Silver Chain & Eyewear",
          fill: "#12b820",
          stroke: "#19f028"
        },
        {
          slug: "aboveavarage",
          brand: "Above Average",
          piecePt: "Beanie & Joalheria Street",
          pieceEn: "Street Beanie & Heavy Silver",
          fill: "#0d3812",
          stroke: "#19f028"
        },
        {
          slug: "clemente",
          brand: "Clemente Studio",
          piecePt: "Peça Metálica Minimalista",
          pieceEn: "Minimal Sculpted Metal Piece",
          fill: "#145c1c",
          stroke: "#39ff48"
        }
      ]
    },
    {
      id: "top",
      labelPt: "Parte Superior / Top",
      labelEn: "Upper Body / Top",
      items: [
        {
          slug: "aevus",
          brand: "Atelier Aevus",
          piecePt: "Jaqueta Estruturada Handmade",
          pieceEn: "Structured Handmade Jacket",
          cutout: "assets/img/fitlab/aevus-jaqueta.png",
          fill: "#061108",
          stroke: "#19f028",
          path: "M72 80 L108 75 L152 75 L188 80 L200 178 L173 182 L166 124 L166 218 L94 218 L94 124 L87 182 L60 178 Z"
        },
        {
          slug: "carnan",
          brand: "Carnan",
          piecePt: "Overshirt / Tricô Contemporâneo",
          pieceEn: "Contemporary Knit Overshirt",
          fill: "#0a1c0d",
          stroke: "#39ff48",
          path: "M76 82 L108 76 L152 76 L184 82 L195 174 L170 178 L164 126 L164 222 L96 222 L96 126 L90 178 L65 174 Z"
        },
        {
          slug: "borra",
          brand: "Borra",
          piecePt: "Hoodie Upcycling Desconstruído",
          pieceEn: "Deconstructed Upcycled Hoodie",
          fill: "#0d2411",
          stroke: "#19f028",
          path: "M68 80 L106 72 L154 72 L192 80 L204 182 L175 186 L168 128 L168 224 L92 224 L92 128 L85 186 L56 182 Z"
        },
        {
          slug: "doth",
          brand: "Doth Project",
          piecePt: "Shell Modular Utilitária",
          pieceEn: "Modular Utilitarian Shell",
          fill: "#07170a",
          stroke: "#29ff38",
          path: "M72 80 L108 75 L152 75 L188 80 L198 180 L172 182 L166 126 L166 220 L94 220 L94 126 L88 182 L62 180 Z"
        },
        {
          slug: "piet",
          brand: "Piet",
          piecePt: "Camiseta Boxy Heavyweight",
          pieceEn: "Heavyweight Boxy Graphic Tee",
          fill: "#091a0c",
          stroke: "#19f028",
          path: "M74 82 L108 76 L152 76 L186 82 L196 142 L168 148 L164 122 L164 220 L96 220 L96 122 L92 148 L64 142 Z"
        },
        {
          slug: "cruel",
          brand: "Cruel",
          piecePt: "Longsleeve Darkwear Gráfica",
          pieceEn: "Darkwear Graphic Longsleeve",
          fill: "#040b05",
          stroke: "#19f028",
          path: "M75 82 L108 76 L152 76 L185 82 L196 178 L172 180 L165 126 L165 218 L95 218 L95 126 L88 180 L64 178 Z"
        }
      ]
    },
    {
      id: "bottom",
      labelPt: "Parte Inferior / Calça",
      labelEn: "Lower Body / Trousers",
      items: [
        {
          slug: "aevus",
          brand: "Atelier Aevus",
          piecePt: "Calça Wide Denim Estonada Desfiada",
          pieceEn: "Distressed Washed Wide Denim Trousers",
          cutout: "assets/img/fitlab/aevus-calca.png",
          fill: "#061208",
          stroke: "#19f028",
          path: "M95 218 L165 218 L180 386 L136 386 L130 272 L124 386 L80 386 Z"
        },
        {
          slug: "dod-alfaiataria",
          brand: "DOD Alfaiataria",
          piecePt: "Calça Alfaiataria Pregueada Wide",
          pieceEn: "Wide Pleated Tailored Trousers",
          fill: "#061208",
          stroke: "#19f028",
          path: "M95 218 L165 218 L180 386 L136 386 L130 272 L124 386 L80 386 Z"
        },
        {
          slug: "hardjeanssanto",
          brand: "Hard Jeans Santo",
          piecePt: "Denim Baggy Estruturado",
          pieceEn: "Structured Raw Baggy Denim",
          fill: "#091b0c",
          stroke: "#39ff48",
          path: "M94 218 L166 218 L184 386 L135 386 L130 278 L125 386 L76 386 Z"
        },
        {
          slug: "onyx",
          brand: "Onyx Five",
          piecePt: "Calça Sob Medida Avant-Garde",
          pieceEn: "Bespoke Avant-Garde Trousers",
          fill: "#040a05",
          stroke: "#19f028",
          path: "M95 218 L165 218 L176 386 L137 386 L130 268 L123 386 L84 386 Z"
        },
        {
          slug: "secta",
          brand: "Secta",
          piecePt: "Corte Reto Sob Medida Escuro",
          pieceEn: "Dark Bespoke Straight Cut",
          fill: "#071409",
          stroke: "#29ff38",
          path: "M96 218 L164 218 L172 386 L136 386 L130 270 L124 386 L88 386 Z"
        },
        {
          slug: "pace",
          brand: "Pace",
          piecePt: "Calça Cargo Utilitária",
          pieceEn: "Utilitarian Relaxed Cargo Pants",
          fill: "#0b1f0e",
          stroke: "#19f028",
          path: "M94 218 L166 218 L182 386 L136 386 L130 276 L124 386 L78 386 Z"
        }
      ]
    },
    {
      id: "shoes",
      labelPt: "Calçado / Footwear",
      labelEn: "Footwear",
      items: [
        {
          slug: "vilela",
          brand: "Vilela Boots",
          piecePt: "Bota Artesanal Solado Tratorado",
          pieceEn: "Handcrafted Heavy Lug Boot",
          fill: "#030704",
          stroke: "#19f028"
        },
        {
          slug: "viga",
          brand: "Viga Shoes",
          piecePt: "Sapato / Derby Autoral em Couro",
          pieceEn: "Artisanal Leather Derby",
          fill: "#081409",
          stroke: "#39ff48"
        },
        {
          slug: "agui",
          brand: "Agui",
          piecePt: "Silhueta Street / Mule Autoral",
          pieceEn: "Contemporary Street Footwear",
          fill: "#0b1c0d",
          stroke: "#19f028"
        }
      ]
    }
  ];

  const fitState = { acc: 0, top: 0, bottom: 0, shoes: 0 };

  const FEATURED_COLLECTIONS = [
    {
      slug: "bussfly",
      tagPt: "DROP EM DESTAQUE",
      tagEn: "FEATURED DROP",
      titlePt: "Drop Bussfly — Série Gráfica",
      titleEn: "Bussfly Drop — Graphic Capsule",
      descPt: "Construções urbanas e identidade gráfica autoral mapeadas no calendário Emorphosis.",
      descEn: "Urban silhouettes and signature graphic identity tracked on the Emorphosis drop radar."
    },
    {
      slug: "duck",
      tagPt: "ARQUIVO DE COLEÇÃO",
      tagEn: "COLLECTION ARCHIVE",
      titlePt: "Drop Duck Pt.2 — Anarco Street",
      titleEn: "Duck Drop Pt.2 — Anarcho Street",
      descPt: "Estética subversiva com referências punk e tiragens independentes.",
      descEn: "Subversive graphic language blending punk attitude and independent runs."
    },
    {
      slug: "wordly",
      tagPt: "COLLAB NACIONAL",
      tagEn: "BRAZILIAN COLLAB",
      titlePt: "Wordly + Internet Radio Dismorfia",
      titleEn: "Wordly + Internet Radio Dismorfia",
      descPt: "Conexão criativa unindo vestuário experimental, música underground e objetos visuais.",
      descEn: "Creative crossover uniting experimental garments, underground radio culture, and visual objects."
    },
    {
      slug: "ablaze",
      tagPt: "HANDMADE · ACESSÓRIOS",
      tagEn: "HANDMADE · ACCESSORIES",
      titlePt: "Ablaze — Chainmail & Metalurgia",
      titleEn: "Ablaze — Chainmail & Metalwork",
      descPt: "Peças tecidas elo por elo à mão em aço, unindo estética medieval e cyber-darkwear.",
      descEn: "Hand-linked steel chainmail pieces bridging medieval armor and cyber-darkwear."
    },
    {
      slug: "dod-alfaiataria",
      tagPt: "ALFAIATARIA AUTORAL",
      tagEn: "INDEPENDENT TAILORING",
      titlePt: "DOD Alfaiataria — Caimento & Corte",
      titleEn: "DOD Tailoring — Drape & Structure",
      descPt: "Alfaiataria contemporânea brasileira com foco em modelagem ampla e acabamento preciso.",
      descEn: "Contemporary Brazilian tailoring focused on wide proportions and sharp construction."
    },
    {
      slug: "vilela",
      tagPt: "CALÇADOS AUTORAIS",
      tagEn: "ARTISANAL FOOTWEAR",
      titlePt: "Vilela Boots — Couro & Presença",
      titleEn: "Vilela Boots — Heavy Leather Craft",
      descPt: "Botas brasileiras de construção robusta que dialogam diretamente com o avant-garde global.",
      descEn: "Heavy-duty Brazilian leather boots conversing directly with global avant-garde silhouettes."
    }
  ];

  // ==========================================================================
  // 1. MENU EXPANSÍVEL ("TRÊS RISCOS") + SUB-ABAS (#catalogo, #quiz, #colecoes)
  // ==========================================================================
  function closeDrawerMenu() {
    const topWrap = document.getElementById("marcas-top-controls");
    const toggleBtn = document.getElementById("marcas-hamburger-btn");
    const panel = document.getElementById("marcas-drawer-panel");
    if (!panel || !toggleBtn) return;
    panel.hidden = true;
    toggleBtn.setAttribute("aria-expanded", "false");
    toggleBtn.classList.remove("open");
    if (topWrap) topWrap.classList.remove("open");
  }

  function activateSubtab(tabName, updateHash) {
    const valid = ["catalogo", "quiz", "colecoes"];
    const normalized = tabName === "fitlab" ? "colecoes" : tabName;
    const target = valid.includes(normalized) ? normalized : "catalogo";
    currentSubtab = target;

    document.querySelectorAll(".subtab-btn").forEach((btn) => {
      const isMatch = btn.getAttribute("data-subtab") === target;
      btn.classList.toggle("active", isMatch);
      btn.setAttribute("aria-selected", isMatch ? "true" : "false");
    });

    valid.forEach((id) => {
      const sec = document.getElementById(`subview-${id}`);
      if (sec) sec.hidden = id !== target;
    });

    if (updateHash) {
      history.replaceState(null, "", `#${target}`);
    }
  }

  function initSubtabs() {
    document.querySelectorAll(".subtab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        activateSubtab(btn.getAttribute("data-subtab"), true);
        closeDrawerMenu();
      });
    });

    const checkHash = () => {
      const raw = (window.location.hash || "").replace(/^#/, "").toLowerCase();
      if (raw) activateSubtab(raw, false);
    };
    window.addEventListener("hashchange", checkHash);
    checkHash();
  }

  // ==========================================================================
  // 2. FILTRO POR CATEGORIA + MÉDIA DE PREÇO + BARRA DESLIZANTE + BUSCA NO GRID
  // ==========================================================================
  function formatBRL(val) {
    if (val === null || val === undefined || isNaN(val)) return "—";
    return Number(val).toLocaleString("pt-BR", {
      style: "currency",
      currency: "BRL",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function matchesAvgTier(avgVal, hasPrice, tier) {
    if (tier === "all") return true;
    if (tier === "consult") return !hasPrice;
    if (!hasPrice) return false;
    if (tier === "priced") return true;
    if (tier === "up_to_200") return avgVal <= 200;
    if (tier === "200_350") return avgVal > 200 && avgVal <= 350;
    if (tier === "350_600") return avgVal > 350 && avgVal <= 600;
    if (tier === "over_600") return avgVal > 600;
    return true;
  }

  function sortCatalogGridDom() {
    const grid = document.getElementById("brands-grid");
    if (!grid) return;
    const cards = Array.from(grid.querySelectorAll(".brand-card"));
    if (!cards.length) return;

    cards.sort((a, b) => {
      const idxA = Number(a.getAttribute("data-sort-idx") || 0);
      const idxB = Number(b.getAttribute("data-sort-idx") || 0);
      if (activePriceSort === "az") return idxA - idxB;

      const avgRawA = a.getAttribute("data-avg-price");
      const avgRawB = b.getAttribute("data-avg-price");
      const minRawA = a.getAttribute("data-min-price");
      const minRawB = b.getAttribute("data-min-price");

      const hasA = Boolean(avgRawA && minRawA);
      const hasB = Boolean(avgRawB && minRawB);

      if (hasA && !hasB) return -1;
      if (!hasA && hasB) return 1;
      if (!hasA && !hasB) return idxA - idxB;

      const avgA = parseFloat(avgRawA);
      const avgB = parseFloat(avgRawB);
      const minA = parseFloat(minRawA);
      const minB = parseFloat(minRawB);

      if (activePriceSort === "avg_asc") {
        return avgA - avgB || minA - minB || idxA - idxB;
      }
      if (activePriceSort === "avg_desc") {
        return avgB - avgA || minB - minA || idxA - idxB;
      }
      if (activePriceSort === "min_asc") {
        return minA - minB || avgA - avgB || idxA - idxB;
      }
      return idxA - idxB;
    });

    cards.forEach((card) => grid.appendChild(card));
  }

  function setPriceSidebarMinimized(minimized) {
    isPriceSidebarMinimized = Boolean(minimized);
    const wrap = document.getElementById("price-sidebar-wrap");
    const openBtn = document.getElementById("price-sidebar-open-btn");
    const backdrop = document.getElementById("price-sidebar-backdrop");
    if (wrap) {
      wrap.classList.toggle("is-minimized", isPriceSidebarMinimized);
      wrap.classList.toggle("is-maximized", !isPriceSidebarMinimized);
    }
    if (openBtn) {
      openBtn.setAttribute("aria-expanded", isPriceSidebarMinimized ? "false" : "true");
    }
    if (backdrop) {
      const isMobile = typeof window !== "undefined" && window.innerWidth <= 1180;
      backdrop.hidden = isPriceSidebarMinimized || !isMobile;
    }
  }

  function applyCatalogFilter() {
    sortCatalogGridDom();
    const cards = document.querySelectorAll("#brands-grid .brand-card");
    const q = searchQuery.trim().toLowerCase();
    const lang = i18n().getLang();
    const isSliderActive = sliderMaxPrice < SLIDER_NO_LIMIT;
    const hasAnyPriceFilter =
      isSliderActive || activeAvgTier !== "all" || activePriceSort !== "az";

    let visibleCount = 0;
    let visiblePricedCount = 0;
    let sumVisibleAvg = 0;

    cards.forEach((el) => {
      const nameStr = el.getAttribute("data-name") || "";
      const catStr = el.getAttribute("data-categories") || "";
      const minRaw = el.getAttribute("data-min-price");
      const avgRaw = el.getAttribute("data-avg-price");

      const hasPrice = Boolean(minRaw && avgRaw);
      const minPrice = hasPrice ? parseFloat(minRaw) : null;
      const avgPrice = hasPrice ? parseFloat(avgRaw) : null;

      const matchSearch = !q || nameStr.includes(q) || catStr.includes(q);
      const matchCat = activeFilter === "all" || catStr.includes(activeFilter);
      const matchSlider = !isSliderActive || (hasPrice && minPrice <= sliderMaxPrice);
      const matchAvg = matchesAvgTier(avgPrice, hasPrice, activeAvgTier);

      if (matchSearch && matchCat && matchSlider && matchAvg) {
        el.style.display = "";
        visibleCount++;
        if (hasPrice && avgPrice !== null) {
          visiblePricedCount++;
          sumVisibleAvg += avgPrice;
        }
      } else {
        el.style.display = "none";
      }
    });

    const countEl = document.getElementById("brand-count");
    if (countEl) countEl.textContent = String(visibleCount);

    const miniBadge = document.getElementById("price-sidebar-mini-badge");
    if (miniBadge) {
      miniBadge.textContent = isSliderActive
        ? `≤R$${sliderMaxPrice} (${visibleCount})`
        : String(visibleCount);
    }

    const openBtn = document.getElementById("price-sidebar-open-btn");
    if (openBtn) {
      openBtn.classList.toggle("has-active-filter", hasAnyPriceFilter);
    }

    const applyMobileBtn = document.getElementById("price-sidebar-apply-mobile-btn");
    if (applyMobileBtn) {
      applyMobileBtn.textContent =
        lang === "en" ? `VIEW ${visibleCount} BRANDS ▸` : `VER ${visibleCount} MARCAS ▸`;
    }

    const sliderBadge = document.getElementById("price-slider-val-badge");
    if (sliderBadge) {
      if (!isSliderActive) {
        sliderBadge.textContent =
          lang === "en"
            ? `NO LIMIT (${visibleCount} BRANDS)`
            : `SEM LIMITE (${visibleCount} MARCAS)`;
      } else {
        const valFmt = formatBRL(sliderMaxPrice);
        sliderBadge.textContent =
          lang === "en"
            ? `PIECES ≤ ${valFmt} · ${visibleCount} BRAND(S)`
            : `PEÇAS ATÉ ${valFmt} · ${visibleCount} MARCA(S)`;
      }
    }

    const summaryEl = document.getElementById("avg-live-summary");
    if (summaryEl) {
      const groupAvg =
        visiblePricedCount > 0 ? formatBRL(sumVisibleAvg / visiblePricedCount) : "—";
      if (isSliderActive) {
        summaryEl.textContent =
          lang === "en"
            ? `${visibleCount} brand(s) ≤ ${formatBRL(sliderMaxPrice)} · Avg: ${groupAvg}`
            : `${visibleCount} marca(s) até ${formatBRL(sliderMaxPrice)} · Média geral: ${groupAvg}`;
      } else {
        summaryEl.textContent =
          lang === "en"
            ? `Showing ${visibleCount} (${visiblePricedCount} priced) · Avg: ${groupAvg}`
            : `Exibindo ${visibleCount} (${visiblePricedCount} com média) · Média geral: ${groupAvg}`;
      }
    }
  }

  function syncSliderPresetsUI() {
    document.querySelectorAll(".price-preset-chip").forEach((chip) => {
      const val = Number(chip.getAttribute("data-slider-preset") || 0);
      chip.classList.toggle("active", val === sliderMaxPrice);
    });
  }

  function initCatalogControls() {
    setPriceSidebarMinimized(isPriceSidebarMinimized);

    const openSidebarBtn = document.getElementById("price-sidebar-open-btn");
    const minSidebarBtn = document.getElementById("price-sidebar-min-btn");
    const applyMobileBtn = document.getElementById("price-sidebar-apply-mobile-btn");
    const sidebarBackdrop = document.getElementById("price-sidebar-backdrop");

    if (openSidebarBtn) {
      openSidebarBtn.addEventListener("click", () => {
        setPriceSidebarMinimized(false);
      });
    }

    if (minSidebarBtn) {
      minSidebarBtn.addEventListener("click", () => {
        setPriceSidebarMinimized(true);
      });
    }

    if (applyMobileBtn) {
      applyMobileBtn.addEventListener("click", () => {
        setPriceSidebarMinimized(true);
      });
    }

    if (sidebarBackdrop) {
      sidebarBackdrop.addEventListener("click", () => {
        setPriceSidebarMinimized(true);
      });
    }

    window.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && !isPriceSidebarMinimized) {
        setPriceSidebarMinimized(true);
      }
    });

    window.addEventListener("resize", () => {
      const backdrop = document.getElementById("price-sidebar-backdrop");
      if (backdrop) {
        const isMobile = window.innerWidth <= 1180;
        backdrop.hidden = isPriceSidebarMinimized || !isMobile;
      }
    });

    const searchInput = document.getElementById("brand-search");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        searchQuery = e.target.value || "";
        if (currentSubtab !== "catalogo") {
          activateSubtab("catalogo", false);
        }
        applyCatalogFilter();
      });
    }

    const topWrap = document.getElementById("marcas-top-controls");
    const toggleBtn = document.getElementById("marcas-hamburger-btn");
    const panel = document.getElementById("marcas-drawer-panel");
    const currentLabel = document.getElementById("filter-menu-current");

    if (toggleBtn && panel) {
      toggleBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        const isOpen = !panel.hidden;
        panel.hidden = isOpen;
        toggleBtn.setAttribute("aria-expanded", isOpen ? "false" : "true");
        toggleBtn.classList.toggle("open", !isOpen);
        if (topWrap) topWrap.classList.toggle("open", !isOpen);
      });

      document.addEventListener("click", (e) => {
        if (!panel.hidden && topWrap && !topWrap.contains(e.target)) {
          closeDrawerMenu();
        }
      });
    }

    document.querySelectorAll(".filter-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        activeFilter = pill.getAttribute("data-filter") || "all";
        document.querySelectorAll(".filter-pill").forEach((p) =>
          p.classList.toggle("active", p === pill)
        );
        if (currentLabel) {
          currentLabel.textContent = pill.textContent || "";
          const i18nKey = pill.getAttribute("data-i18n");
          if (i18nKey) currentLabel.setAttribute("data-i18n", i18nKey);
        }
        if (currentSubtab !== "catalogo") {
          activateSubtab("catalogo", true);
        }
        closeDrawerMenu();
        applyCatalogFilter();
      });
    });

    // Barra Deslizante de Valor Máximo (filtra marcas que possuem peças <= valor selecionado)
    const priceSlider = document.getElementById("price-max-slider");
    if (priceSlider) {
      priceSlider.addEventListener("input", (e) => {
        sliderMaxPrice = Number(e.target.value || SLIDER_NO_LIMIT);
        syncSliderPresetsUI();
        applyCatalogFilter();
      });
    }

    document.querySelectorAll(".price-preset-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        const val = Number(chip.getAttribute("data-slider-preset") || SLIDER_NO_LIMIT);
        sliderMaxPrice = val;
        if (priceSlider) priceSlider.value = String(val);
        syncSliderPresetsUI();
        applyCatalogFilter();
      });
    });

    // Filtro por Faixa de Média de Preço da Marca
    document.querySelectorAll(".avg-price-pill").forEach((pill) => {
      pill.addEventListener("click", () => {
        activeAvgTier = pill.getAttribute("data-avg-tier") || "all";
        document.querySelectorAll(".avg-price-pill").forEach((p) =>
          p.classList.toggle("active", p === pill)
        );
        applyCatalogFilter();
      });
    });

    // Ordenação por Média de Preço / Peça Mais Barata / A-Z
    document.querySelectorAll(".price-sort-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        activePriceSort = btn.getAttribute("data-price-sort") || "az";
        document.querySelectorAll(".price-sort-btn").forEach((b) =>
          b.classList.toggle("active", b === btn)
        );
        applyCatalogFilter();
      });
    });

    // Botão Limpar Filtro de Preço
    const resetPriceBtn = document.getElementById("price-filter-reset-btn");
    if (resetPriceBtn) {
      resetPriceBtn.addEventListener("click", () => {
        sliderMaxPrice = SLIDER_NO_LIMIT;
        activeAvgTier = "all";
        activePriceSort = "az";
        if (priceSlider) priceSlider.value = String(SLIDER_NO_LIMIT);
        syncSliderPresetsUI();
        document.querySelectorAll(".avg-price-pill").forEach((p) =>
          p.classList.toggle("active", p.getAttribute("data-avg-tier") === "all")
        );
        document.querySelectorAll(".price-sort-btn").forEach((b) =>
          b.classList.toggle("active", b.getAttribute("data-price-sort") === "az")
        );
        applyCatalogFilter();
      });
    }

    // Ícone "i" no canto inferior esquerdo de cada marca: toque no celular abre o popover sem sair da página
    const gridEl = document.getElementById("brands-grid");
    if (gridEl) {
      gridEl.addEventListener("click", (ev) => {
        const infoEl = ev.target.closest(".brand-price-info");
        if (!infoEl) return;
        ev.preventDefault();
        ev.stopPropagation();
        const card = infoEl.closest(".brand-card");
        const wasOpen = infoEl.classList.contains("is-open");
        document.querySelectorAll(".brand-price-info.is-open").forEach((el) => {
          el.classList.remove("is-open");
          const c = el.closest(".brand-card");
          if (c) c.classList.remove("has-info-open");
        });
        if (!wasOpen) {
          infoEl.classList.add("is-open");
          if (card) card.classList.add("has-info-open");
        }
      });
    }

    document.addEventListener("click", (ev) => {
      if (!ev.target.closest(".brand-price-info")) {
        document.querySelectorAll(".brand-price-info.is-open").forEach((el) => {
          el.classList.remove("is-open");
          const c = el.closest(".brand-card");
          if (c) c.classList.remove("has-info-open");
        });
      }
    });
  }

  // ==========================================================================
  // 3. QUIZ & FILTRO DE REFERÊNCIAS INTERNACIONAIS -> MARCAS BRASILEIRAS
  // ==========================================================================
  function renderIntlChips() {
    const wrap = document.getElementById("intl-chips");
    if (!wrap) return;
    wrap.innerHTML = "";

    INTL_REFS.forEach((ref) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "intl-chip" + (selectedIntl.has(ref.name) ? " active" : "");
      btn.textContent = ref.name;
      btn.addEventListener("click", () => {
        if (selectedIntl.has(ref.name)) {
          selectedIntl.delete(ref.name);
        } else {
          selectedIntl.add(ref.name);
        }
        btn.classList.toggle("active", selectedIntl.has(ref.name));
        renderQuizResults();
      });
      wrap.appendChild(btn);
    });
  }

  function scoreBrand(brand) {
    let score = 0;
    const matchedTags = new Set();
    const bVibes = brand.vibes || [];
    const bCats = brand.categories || [];

    selectedIntl.forEach((refName) => {
      const ref = INTL_REFS.find((r) => r.name === refName);
      if (!ref) return;
      ref.vibes.forEach((v) => {
        if (bVibes.includes(v)) {
          score += 3;
          matchedTags.add(v);
        }
        if (v === "footwear" && bCats.includes("calcados")) {
          score += 4;
          matchedTags.add("footwear");
        }
        if (v === "accessories" && bCats.includes("acessorios")) {
          score += 4;
          matchedTags.add("accessories");
        }
      });
    });

    const relatedMap = {
      darkwear: ["avantgarde", "punk"],
      streetwear: ["graphic", "contemporary"],
      minimal: ["tailoring", "contemporary"],
      upcycling: ["artisanal", "punk"],
      gorpcore: ["techwear", "cyber", "archive"]
    };

    if (selectedVibe) {
      if (bVibes.includes(selectedVibe)) {
        score += 5;
        matchedTags.add(selectedVibe);
      }
      (relatedMap[selectedVibe] || []).forEach((rel) => {
        if (bVibes.includes(rel)) {
          score += 2;
          matchedTags.add(rel);
        }
      });
    }

    if (selectedFocus && selectedFocus !== "all") {
      if (selectedFocus === "handmade") {
        if (bCats.includes("handmade") || bCats.includes("upcycling") || bVibes.includes("artisanal")) {
          score += 6;
          matchedTags.add("artisanal");
        }
      } else if (selectedFocus === "tailoring") {
        if (bCats.includes("sob medida") || bCats.includes("alfaiataria") || bVibes.includes("tailoring")) {
          score += 7;
          matchedTags.add("tailoring");
        }
      } else if (selectedFocus === "accessories") {
        if (bCats.includes("acessorios") || bVibes.includes("accessories")) {
          score += 8;
          matchedTags.add("accessories");
        } else {
          score -= 4;
        }
      } else if (selectedFocus === "footwear") {
        if (bCats.includes("calcados") || bVibes.includes("footwear")) {
          score += 9;
          matchedTags.add("footwear");
        } else {
          score -= 5;
        }
      }
    }

    return { brand, score, matchedTags: Array.from(matchedTags) };
  }

  function renderQuizResults() {
    const grid = document.getElementById("quiz-results-grid");
    if (!grid || !brandsData.length) return;

    const lang = i18n().getLang();
    const hasActiveCriteria =
      selectedIntl.size > 0 || Boolean(selectedVibe) || (selectedFocus && selectedFocus !== "all");

    let list;
    if (!hasActiveCriteria) {
      const starterSlugs = [
        "aevus",
        "carnan",
        "dod-alfaiataria",
        "ablaze",
        "vilela",
        "borra",
        "doth",
        "piet",
        "onyx"
      ];
      list = starterSlugs
        .map((s) => brandsData.find((b) => b.slug === s))
        .filter(Boolean)
        .map((brand) => ({ brand, score: 0, matchedTags: (brand.vibes || []).slice(0, 2) }));
    } else {
      list = brandsData
        .map(scoreBrand)
        .filter((item) => item.score > 0)
        .sort((a, b) => b.score - a.score || a.brand.name.localeCompare(b.brand.name))
        .slice(0, 9);
    }

    if (!list.length) {
      grid.innerHTML = `<p class="empty-note">${
        lang === "en"
          ? "No exact match for this combination — try selecting another international reference."
          : "Nenhuma combinação exata para esse filtro — tente marcar mais uma referência acima."
      }</p>`;
      return;
    }

    const labels = VIBE_LABELS[lang] || VIBE_LABELS.pt;

    grid.innerHTML = list
      .map(({ brand, score, matchedTags }) => {
        const badge =
          score > 0
            ? `<span class="match-score">${Math.min(99, 68 + score * 3)}% MATCH</span>`
            : `<span class="match-score starter">${lang === "en" ? "CURATED PICK" : "DESTAQUE"}</span>`;
        const tagsHtml = (matchedTags.length ? matchedTags : brand.vibes || [])
          .slice(0, 3)
          .map((t) => `<span class="mini-tag">${labels[t] || t}</span>`)
          .join("");

        return `
          <article class="quiz-brand-card">
            <div class="quiz-card-top">
              <img src="${brand.img}" alt="${brand.name}" width="64" height="64" loading="lazy" />
              <div class="quiz-card-meta">
                ${badge}
                <h4>${brand.name}</h4>
                <span class="handle">@${brand.handle}</span>
              </div>
            </div>
            <div class="mini-tags">${tagsHtml}</div>
            <div class="quiz-card-actions">
              <a href="${brand.url}" target="_blank" rel="noopener noreferrer" class="btn-solid-sm">INSTAGRAM ↗</a>
            </div>
          </article>
        `;
      })
      .join("");
  }

  function initQuiz() {
    renderIntlChips();

    document.querySelectorAll('[data-quiz-group="vibe"] .quiz-opt').forEach((btn) => {
      btn.addEventListener("click", () => {
        const val = btn.getAttribute("data-val") || "";
        selectedVibe = selectedVibe === val ? "" : val;
        document
          .querySelectorAll('[data-quiz-group="vibe"] .quiz-opt')
          .forEach((b) => b.classList.toggle("active", b.getAttribute("data-val") === selectedVibe));
        renderQuizResults();
      });
    });

    document.querySelectorAll('[data-quiz-group="focus"] .quiz-opt').forEach((btn) => {
      if (btn.getAttribute("data-val") === "all") btn.classList.add("active");
      btn.addEventListener("click", () => {
        selectedFocus = btn.getAttribute("data-val") || "all";
        document
          .querySelectorAll('[data-quiz-group="focus"] .quiz-opt')
          .forEach((b) => b.classList.toggle("active", b === btn));
        renderQuizResults();
      });
    });

    const resetBtn = document.getElementById("reset-quiz-btn");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        selectedIntl.clear();
        selectedVibe = "";
        selectedFocus = "all";
        renderIntlChips();
        document.querySelectorAll('[data-quiz-group="vibe"] .quiz-opt').forEach((b) => b.classList.remove("active"));
        document
          .querySelectorAll('[data-quiz-group="focus"] .quiz-opt')
          .forEach((b) => b.classList.toggle("active", b.getAttribute("data-val") === "all"));
        renderQuizResults();
      });
    }
  }

  // ==========================================================================
  // 4. MANEQUIM VIRTUAL (FIT LAB) + COLEÇÕES DE MARCAS
  // ==========================================================================
  function updateMannequinSVG() {
    const acc = FIT_SLOTS[0].items[fitState.acc];
    const top = FIT_SLOTS[1].items[fitState.top];
    const bottom = FIT_SLOTS[2].items[fitState.bottom];
    const shoes = FIT_SLOTS[3].items[fitState.shoes];

    const accShape = document.getElementById("svg-acc-shape");
    const accImg = document.getElementById("svg-acc-img");
    if (acc.cutout && accImg) {
      accImg.setAttribute("href", acc.cutout);
      accImg.style.display = "";
      if (accShape) accShape.style.display = "none";
    } else {
      if (accImg) accImg.style.display = "none";
      if (accShape) {
        accShape.style.display = "";
        accShape.querySelectorAll("path").forEach((p) => p.setAttribute("fill", acc.fill));
        accShape.querySelectorAll("circle").forEach((c) => c.setAttribute("stroke", acc.stroke));
      }
    }

    const topShape = document.getElementById("svg-top-shape");
    const topImg = document.getElementById("svg-top-img");
    if (top.cutout && topImg) {
      topImg.setAttribute("href", top.cutout);
      topImg.style.display = "";
      if (topShape) topShape.style.display = "none";
    } else {
      if (topImg) topImg.style.display = "none";
      if (topShape) {
        topShape.style.display = "";
        topShape.setAttribute("fill", top.fill);
        topShape.setAttribute("stroke", top.stroke);
        if (top.path) topShape.setAttribute("d", top.path);
      }
    }

    const bottomShape = document.getElementById("svg-bottom-shape");
    const bottomImg = document.getElementById("svg-bottom-img");
    if (bottom.cutout && bottomImg) {
      bottomImg.setAttribute("href", bottom.cutout);
      bottomImg.style.display = "";
      if (bottomShape) bottomShape.style.display = "none";
    } else {
      if (bottomImg) bottomImg.style.display = "none";
      if (bottomShape) {
        bottomShape.style.display = "";
        bottomShape.setAttribute("fill", bottom.fill);
        bottomShape.setAttribute("stroke", bottom.stroke);
        if (bottom.path) bottomShape.setAttribute("d", bottom.path);
      }
    }

    const shoesShape = document.getElementById("svg-shoes-shape");
    const shoesImg = document.getElementById("svg-shoes-img");
    if (shoes.cutout && shoesImg) {
      shoesImg.setAttribute("href", shoes.cutout);
      shoesImg.style.display = "";
      if (shoesShape) shoesShape.style.display = "none";
    } else {
      if (shoesImg) shoesImg.style.display = "none";
      if (shoesShape) {
        shoesShape.style.display = "";
        shoesShape.setAttribute("fill", shoes.fill);
        shoesShape.setAttribute("stroke", shoes.stroke);
      }
    }
  }

  function renderFitLab() {
    const wrap = document.getElementById("fitlab-controls");
    if (!wrap) return;
    const lang = i18n().getLang();

    const rowsHtml = FIT_SLOTS.map((slot) => {
      const idx = fitState[slot.id];
      const item = slot.items[idx];
      const brandObj = brandsData.find((b) => b.slug === item.slug);
      const imgSrc = item.cutout || (brandObj ? brandObj.img : `assets/img/marcas/${item.slug}.jpg`);
      const slotTitle = lang === "en" ? slot.labelEn : slot.labelPt;
      const pieceName = lang === "en" ? item.pieceEn : item.piecePt;

      return `
        <div class="fit-layer-row" data-slot="${slot.id}">
          <div class="fit-layer-header">
            <span class="fit-layer-label">${slotTitle}</span>
            <span class="fit-layer-counter">${idx + 1}/${slot.items.length}</span>
          </div>
          <div class="fit-layer-picker">
            <button type="button" class="fit-arrow" data-dir="-1" data-slot="${slot.id}" aria-label="Anterior">‹</button>
            <div class="fit-piece-info">
              <img src="${imgSrc}" alt="${item.brand}" width="44" height="44" />
              <div>
                <strong>${item.brand}</strong>
                <span>${pieceName}</span>
              </div>
            </div>
            <button type="button" class="fit-arrow" data-dir="1" data-slot="${slot.id}" aria-label="Próximo">›</button>
          </div>
          ${
            item.isPersonal
              ? `<div class="fit-layer-links">
                  <span>${lang === "en" ? "★ PERSONAL WARDROBE (PRIVATE)" : "★ ACERVO PESSOAL (SÓ VOCÊ VÊ)"}</span>
                </div>`
              : brandObj
              ? `<div class="fit-layer-links">
                  <a href="${brandObj.url}" target="_blank" rel="noopener noreferrer">@${brandObj.handle} ↗</a>
                </div>`
              : item.comingSoon
              ? `<div class="fit-layer-links">
                  <span>${lang === "en" ? "COMING SOON TO CATALOG" : "EM BREVE NO CATÁLOGO"}</span>
                </div>`
              : ""
          }
        </div>
      `;
    }).join("");

    const randomTxt = lang === "en" ? "↻ RANDOMIZE FULL FIT" : "↻ SORTEAR FIT COMPLETO";
    wrap.innerHTML = `
      ${rowsHtml}
      <button type="button" class="btn-randomize-fit" id="btn-randomize-fit">${randomTxt}</button>
    `;

    wrap.querySelectorAll(".fit-arrow").forEach((btn) => {
      btn.addEventListener("click", () => {
        const slotId = btn.getAttribute("data-slot");
        const dir = Number(btn.getAttribute("data-dir") || 1);
        const slot = FIT_SLOTS.find((s) => s.id === slotId);
        if (!slot) return;
        fitState[slotId] = (fitState[slotId] + dir + slot.items.length) % slot.items.length;
        updateMannequinSVG();
        renderFitLab();
      });
    });

    const randBtn = document.getElementById("btn-randomize-fit");
    if (randBtn) {
      randBtn.addEventListener("click", () => {
        FIT_SLOTS.forEach((slot) => {
          fitState[slot.id] = Math.floor(Math.random() * slot.items.length);
        });
        updateMannequinSVG();
        renderFitLab();
      });
    }

    updateMannequinSVG();
  }

  function renderCollections() {
    const grid = document.getElementById("collections-grid");
    if (!grid) return;
    const lang = i18n().getLang();

    grid.innerHTML = FEATURED_COLLECTIONS.map((col) => {
      const brandObj = brandsData.find((b) => b.slug === col.slug);
      const img = brandObj ? brandObj.img : `assets/img/marcas/${col.slug}.jpg`;
      const igUrl = brandObj ? brandObj.url : "#";
      const tag = lang === "en" ? col.tagEn : col.tagPt;
      const title = lang === "en" ? col.titleEn : col.titlePt;
      const desc = lang === "en" ? col.descEn : col.descPt;

      return `
        <article class="collection-card">
          <div class="collection-head">
            <img src="${img}" alt="${title}" width="56" height="56" loading="lazy" />
            <div>
              <span class="collection-tag">${tag}</span>
              <h3>${title}</h3>
            </div>
          </div>
          <p>${desc}</p>
          <div class="quiz-card-actions">
            <a href="${igUrl}" target="_blank" rel="noopener noreferrer" class="btn-solid-sm">INSTAGRAM ↗</a>
          </div>
        </article>
      `;
    }).join("");
  }

  // ==========================================================================
  // 5. INSCRIÇÃO POR E-MAIL NAS MARCAS (ALERTA 1 HORA ANTES DO DROP)
  // ==========================================================================
  const subSelectedSlugs = new Set();
  let subAllBrands = false;
  let subFilterQuery = "";

  function updateSubCounter() {
    const lang = i18n().getLang();
    const counterEl = document.getElementById("sub-selected-counter");
    const allBtn = document.getElementById("sub-all-brands-btn");

    if (allBtn) {
      allBtn.classList.toggle("active", subAllBrands);
    }

    if (counterEl) {
      const total = brandsData.length || 133;
      const count = subAllBrands ? total : subSelectedSlugs.size;
      counterEl.textContent =
        lang === "en" ? `${count} selected` : `${count} selecionada(s)`;
    }
  }

  function renderDropSubscriptionSelector() {
    const container = document.getElementById("sub-brands-selector");
    if (!container) return;

    const q = subFilterQuery.trim().toLowerCase();
    const list = brandsData.filter((b) => {
      if (!q) return true;
      return (
        b.name.toLowerCase().includes(q) ||
        b.handle.toLowerCase().includes(q) ||
        b.slug.toLowerCase().includes(q)
      );
    });

    container.innerHTML = list
      .map((b) => {
        const isSelected = subAllBrands || subSelectedSlugs.has(b.slug);
        return `
          <button
            type="button"
            class="sub-brand-chip${isSelected ? " active" : ""}"
            data-sub-slug="${b.slug}"
            title="${b.name} (@${b.handle})"
          >
            <img src="${b.img}" alt="${b.name}" width="28" height="28" loading="lazy" />
            <span class="sub-brand-chip-name">${b.name}</span>
          </button>
        `;
      })
      .join("");

    container.querySelectorAll(".sub-brand-chip").forEach((btn) => {
      btn.addEventListener("click", () => {
        const slug = btn.getAttribute("data-sub-slug");
        if (!slug) return;

        if (subAllBrands) {
          subAllBrands = false;
          subSelectedSlugs.clear();
          brandsData.forEach((b) => {
            if (b.slug !== slug) subSelectedSlugs.add(b.slug);
          });
        } else if (subSelectedSlugs.has(slug)) {
          subSelectedSlugs.delete(slug);
        } else {
          subSelectedSlugs.add(slug);
        }

        renderDropSubscriptionSelector();
        updateSubCounter();
      });
    });

    updateSubCounter();
  }

  function initDropSubscription() {
    const allBtn = document.getElementById("sub-all-brands-btn");
    const clearBtn = document.getElementById("sub-clear-brands-btn");
    const filterInput = document.getElementById("sub-brand-filter");
    const form = document.getElementById("brand-drop-sub-form");
    const feedback = document.getElementById("sub-form-feedback");

    if (allBtn) {
      allBtn.addEventListener("click", () => {
        subAllBrands = !subAllBrands;
        if (subAllBrands) {
          subSelectedSlugs.clear();
        }
        renderDropSubscriptionSelector();
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        subAllBrands = false;
        subSelectedSlugs.clear();
        renderDropSubscriptionSelector();
      });
    }

    if (filterInput) {
      filterInput.addEventListener("input", (e) => {
        subFilterQuery = e.target.value || "";
        renderDropSubscriptionSelector();
      });
    }

    if (form && feedback) {
      form.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const lang = i18n().getLang();
        const emailInput = document.getElementById("sub-user-email");
        const email = emailInput ? emailInput.value.trim() : "";

        if (!subAllBrands && subSelectedSlugs.size === 0) {
          feedback.textContent =
            lang === "en"
              ? "Please select at least 1 brand (or click '★ ALL BRANDS')."
              : "Selecione pelo menos 1 marca (ou clique em '★ TODAS AS MARCAS').";
          feedback.className = "form-feedback err";
          return;
        }

        feedback.textContent =
          lang === "en" ? "Activating drop alerts..." : "Ativando alertas de drop...";
        feedback.className = "form-feedback";

        try {
          const res = await fetch("api/subscribe_drops.php", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email,
              all_brands: subAllBrands,
              brands: Array.from(subSelectedSlugs)
            })
          });
          const json = await res.json();
          if (res.ok && json.ok) {
            const countTxt = subAllBrands
              ? brandsData.length || 133
              : subSelectedSlugs.size;
            feedback.textContent =
              lang === "en"
                ? `Subscribed! You will receive an email 1 hour before drops from your ${countTxt} selected brand(s) with the drop time and Instagram link.`
                : `Inscrição confirmada! Você receberá um e-mail 1 hora antes dos drops de ${countTxt} marca(s) com o horário e o link do Instagram.`;
            feedback.className = "form-feedback ok";
            if (emailInput) emailInput.value = "";
          } else {
            throw new Error(json.error || "Error");
          }
        } catch (_) {
          feedback.textContent =
            lang === "en"
              ? "Could not complete registration. Check your email and try again."
              : "Não foi possível concluir o cadastro. Verifique seu e-mail e tente novamente.";
          feedback.className = "form-feedback err";
        }
      });
    }
  }

  // ==========================================================================
  // 6. ACERVO PESSOAL PRIVADO — UPLOAD & RECORTE AUTOMÁTICO DE ROUPAS (FIT LAB)
  //    Salvo exclusivamente no navegador do usuário (IndexedDB / localStorage)
  // ==========================================================================
  const PERSONAL_DB_NAME = "emorphosis_personal_wardrobe_db";
  const PERSONAL_STORE_NAME = "pieces";
  const PERSONAL_LS_KEY = "emorphosis_personal_wardrobe_v1";

  let personalPieces = [];
  let cutoutSourceImgData = null;
  let cutoutAutoSeeds = [];
  let cutoutExtraSeeds = [];

  function openPersonalDB() {
    return new Promise((resolve, reject) => {
      if (!window.indexedDB) {
        reject(new Error("IndexedDB unavailable"));
        return;
      }
      const req = window.indexedDB.open(PERSONAL_DB_NAME, 1);
      req.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains(PERSONAL_STORE_NAME)) {
          db.createObjectStore(PERSONAL_STORE_NAME, { keyPath: "id" });
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async function loadPersonalPiecesFromStorage() {
    try {
      const db = await openPersonalDB();
      return await new Promise((resolve, reject) => {
        const tx = db.transaction(PERSONAL_STORE_NAME, "readonly");
        const store = tx.objectStore(PERSONAL_STORE_NAME);
        const req = store.getAll();
        req.onsuccess = () => resolve(Array.isArray(req.result) ? req.result : []);
        req.onerror = () => reject(req.error);
      });
    } catch (_) {
      try {
        const raw = localStorage.getItem(PERSONAL_LS_KEY);
        return raw ? JSON.parse(raw) : [];
      } catch (__) {
        return [];
      }
    }
  }

  async function savePersonalPieceToStorage(piece) {
    try {
      const db = await openPersonalDB();
      await new Promise((resolve, reject) => {
        const tx = db.transaction(PERSONAL_STORE_NAME, "readwrite");
        const store = tx.objectStore(PERSONAL_STORE_NAME);
        store.put(piece);
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
    } catch (_) {
      try {
        localStorage.setItem(PERSONAL_LS_KEY, JSON.stringify(personalPieces));
      } catch (__) {}
    }
  }

  async function deletePersonalPieceFromStorage(id) {
    try {
      const db = await openPersonalDB();
      await new Promise((resolve, reject) => {
        const tx = db.transaction(PERSONAL_STORE_NAME, "readwrite");
        const store = tx.objectStore(PERSONAL_STORE_NAME);
        store.delete(id);
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
    } catch (_) {
      try {
        localStorage.setItem(PERSONAL_LS_KEY, JSON.stringify(personalPieces));
      } catch (__) {}
    }
  }

  function syncPersonalPiecesIntoFitSlots() {
    FIT_SLOTS.forEach((slot) => {
      slot.items = slot.items.filter((it) => !it.isPersonal);
      const userSlotPieces = personalPieces
        .filter((p) => p.slot === slot.id)
        .sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0));

      userSlotPieces.forEach((p) => {
        slot.items.unshift({
          id: p.id,
          slug: "personal-" + p.id,
          brand: p.brand || "Acervo Pessoal",
          piecePt: p.piecePt || "Peça Pessoal",
          pieceEn: p.pieceEn || p.piecePt || "Personal Garment",
          cutout: p.cutout,
          isPersonal: true,
          fill: "#061108",
          stroke: "#39ff48"
        });
      });

      if (fitState[slot.id] >= slot.items.length) {
        fitState[slot.id] = 0;
      }
    });
  }

  function colorDistance(r1, g1, b1, r2, g2, b2) {
    const dr = r1 - r2;
    const dg = g1 - g2;
    const db = b1 - b2;
    return Math.sqrt(0.3 * dr * dr + 0.59 * dg * dg + 0.11 * db * db);
  }

  function detectBorderBgColors(imgData) {
    const { width: w, height: h, data } = imgData;
    const samples = [];
    const stepX = Math.max(1, Math.floor(w / 40));
    const stepY = Math.max(1, Math.floor(h / 40));

    const pushPixel = (x, y) => {
      const idx = (y * w + x) * 4;
      if (data[idx + 3] < 128) return;
      samples.push([data[idx], data[idx + 1], data[idx + 2]]);
    };

    for (let x = 0; x < w; x += stepX) {
      pushPixel(x, 1);
      pushPixel(x, h - 2);
    }
    for (let y = 0; y < h; y += stepY) {
      pushPixel(1, y);
      pushPixel(w - 2, y);
    }

    if (!samples.length) return [[255, 255, 255]];

    // Agrupa amostras das bordas em clusters de cor (ex: fundo branco, cinza ou preto)
    const clusters = [];
    samples.forEach(([r, g, b]) => {
      let found = null;
      for (let i = 0; i < clusters.length; i++) {
        const c = clusters[i];
        if (colorDistance(r, g, b, c.r, c.g, c.b) <= 22) {
          found = c;
          break;
        }
      }
      if (found) {
        found.count++;
        found.r = Math.round((found.r * (found.count - 1) + r) / found.count);
        found.g = Math.round((found.g * (found.count - 1) + g) / found.count);
        found.b = Math.round((found.b * (found.count - 1) + b) / found.count);
      } else {
        clusters.push({ r, g, b, count: 1 });
      }
    });

    clusters.sort((a, b) => b.count - a.count);
    return clusters.slice(0, 3).map((c) => [c.r, c.g, c.b]);
  }

  function runCutoutEngine() {
    const canvas = document.getElementById("custom-cutout-canvas");
    if (!canvas || !cutoutSourceImgData) return;

    const tolInput = document.getElementById("custom-cutout-tolerance");
    const innerInput = document.getElementById("custom-cutout-inner");
    const tolerance = tolInput ? Number(tolInput.value) || 36 : 36;
    const removeInner = innerInput ? innerInput.checked : true;

    const w = cutoutSourceImgData.width;
    const h = cutoutSourceImgData.height;
    const src = cutoutSourceImgData.data;

    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    const outImg = ctx.createImageData(w, h);
    const dst = outImg.data;

    const seeds = cutoutAutoSeeds.concat(cutoutExtraSeeds.map((s) => [s.r, s.g, s.b]));
    const minDistToSeeds = (r, g, b) => {
      let best = 9999;
      for (let i = 0; i < seeds.length; i++) {
        const d = colorDistance(r, g, b, seeds[i][0], seeds[i][1], seeds[i][2]);
        if (d < best) best = d;
      }
      return best;
    };

    const totalPixels = w * h;
    const visited = new Uint8Array(totalPixels);
    const isBg = new Uint8Array(totalPixels);
    const queue = new Int32Array(totalPixels);
    let qHead = 0;
    let qTail = 0;

    const tryEnqueue = (x, y) => {
      if (x < 0 || x >= w || y < 0 || y >= h) return;
      const pIdx = y * w + x;
      if (visited[pIdx]) return;
      const cIdx = pIdx * 4;
      if (src[cIdx + 3] < 20) {
        visited[pIdx] = 1;
        isBg[pIdx] = 1;
        queue[qTail++] = pIdx;
        return;
      }
      const dist = minDistToSeeds(src[cIdx], src[cIdx + 1], src[cIdx + 2]);
      if (dist <= tolerance) {
        visited[pIdx] = 1;
        isBg[pIdx] = 1;
        queue[qTail++] = pIdx;
      }
    };

    for (let x = 0; x < w; x++) {
      tryEnqueue(x, 0);
      tryEnqueue(x, h - 1);
    }
    for (let y = 0; y < h; y++) {
      tryEnqueue(0, y);
      tryEnqueue(w - 1, y);
    }

    cutoutExtraSeeds.forEach((pt) => {
      if (typeof pt.x === "number" && typeof pt.y === "number") {
        const pIdx = pt.y * w + pt.x;
        if (!visited[pIdx]) {
          visited[pIdx] = 1;
          isBg[pIdx] = 1;
          queue[qTail++] = pIdx;
        }
      }
    });

    if (removeInner) {
      const innerTol = tolerance * 0.58;
      for (let y = 2; y < h - 2; y += 2) {
        for (let x = 2; x < w - 2; x += 2) {
          const pIdx = y * w + x;
          if (visited[pIdx]) continue;
          const cIdx = pIdx * 4;
          if (minDistToSeeds(src[cIdx], src[cIdx + 1], src[cIdx + 2]) <= innerTol) {
            tryEnqueue(x, y);
          }
        }
      }
    }

    const dx = [-1, 1, 0, 0, -1, -1, 1, 1];
    const dy = [0, 0, -1, 1, -1, 1, -1, 1];

    while (qHead < qTail) {
      const curr = queue[qHead++];
      const cx = curr % w;
      const cy = (curr - cx) / w;
      for (let d = 0; d < 8; d++) {
        tryEnqueue(cx + dx[d], cy + dy[d]);
      }
    }

    // Suavização de bordas (anti-aliasing de contorno)
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const pIdx = y * w + x;
        const cIdx = pIdx * 4;
        if (isBg[pIdx]) {
          dst[cIdx] = 0;
          dst[cIdx + 1] = 0;
          dst[cIdx + 2] = 0;
          dst[cIdx + 3] = 0;
        } else {
          let bgNeighbors = 0;
          for (let d = 0; d < 8; d++) {
            const nx = x + dx[d];
            const ny = y + dy[d];
            if (nx >= 0 && nx < w && ny >= 0 && ny < h && isBg[ny * w + nx]) {
              bgNeighbors++;
            }
          }
          let r = src[cIdx];
          let g = src[cIdx + 1];
          let b = src[cIdx + 2];
          let a = src[cIdx + 3];

          if (bgNeighbors > 0) {
            const dist = minDistToSeeds(r, g, b);
            const featherRange = tolerance * 1.45;
            if (dist < featherRange) {
              const ratio = Math.max(0.12, Math.min(1, (dist - tolerance * 0.65) / (featherRange - tolerance * 0.65)));
              a = Math.round(a * ratio);
            }
          }

          dst[cIdx] = r;
          dst[cIdx + 1] = g;
          dst[cIdx + 2] = b;
          dst[cIdx + 3] = a;
        }
      }
    }

    ctx.putImageData(outImg, 0, 0);
  }

  function extractCroppedCutoutDataUrl() {
    const canvas = document.getElementById("custom-cutout-canvas");
    if (!canvas || !canvas.width || !canvas.height) return null;

    const w = canvas.width;
    const h = canvas.height;
    const ctx = canvas.getContext("2d");
    const imgData = ctx.getImageData(0, 0, w, h);
    const data = imgData.data;

    let minX = w;
    let minY = h;
    let maxX = 0;
    let maxY = 0;
    let hasPixels = false;

    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const a = data[(y * w + x) * 4 + 3];
        if (a > 24) {
          hasPixels = true;
          if (x < minX) minX = x;
          if (x > maxX) maxX = x;
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;
        }
      }
    }

    if (!hasPixels) return canvas.toDataURL("image/png");

    const pad = 6;
    minX = Math.max(0, minX - pad);
    minY = Math.max(0, minY - pad);
    maxX = Math.min(w - 1, maxX + pad);
    maxY = Math.min(h - 1, maxY + pad);

    const cw = Math.max(1, maxX - minX + 1);
    const ch = Math.max(1, maxY - minY + 1);

    const cropCanvas = document.createElement("canvas");
    cropCanvas.width = cw;
    cropCanvas.height = ch;
    const cropCtx = cropCanvas.getContext("2d");
    cropCtx.drawImage(canvas, minX, minY, cw, ch, 0, 0, cw, ch);
    return cropCanvas.toDataURL("image/png");
  }

  function renderPersonalWardrobeGallery() {
    const grid = document.getElementById("personal-wardrobe-grid");
    const countEl = document.getElementById("personal-wardrobe-count");
    if (!grid) return;

    const lang = i18n().getLang();
    if (countEl) {
      countEl.textContent =
        lang === "en" ? `${personalPieces.length} item(s)` : `${personalPieces.length} peça(s)`;
    }

    if (!personalPieces.length) {
      const emptyTxt = i18n().t(
        "fit.empty_collection",
        "Você ainda não adicionou peças pessoais. Envie uma foto acima para recortar e testar no manequim."
      );
      grid.innerHTML = `<p class="empty-note">${emptyTxt}</p>`;
      return;
    }

    const slotLabels = {
      top: lang === "en" ? "TOP" : "PARTE SUPERIOR",
      bottom: lang === "en" ? "TROUSERS" : "CALÇA / INFERIOR",
      acc: lang === "en" ? "HEADWEAR / ACC" : "ACESSÓRIO / HEADWEAR",
      shoes: lang === "en" ? "FOOTWEAR" : "CALÇADO"
    };

    const sorted = [...personalPieces].sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0));

    grid.innerHTML = sorted
      .map((p) => {
        const badge = slotLabels[p.slot] || p.slot.toUpperCase();
        const equipTxt = lang === "en" ? "EQUIP ON MANNEQUIN" : "VESTIR NO MANEQUIM";
        const delTxt = lang === "en" ? "✕ DELETE" : "✕ EXCLUIR";

        return `
          <article class="personal-piece-card" data-personal-id="${p.id}">
            <div class="personal-piece-thumb">
              <img src="${p.cutout}" alt="${p.piecePt}" loading="lazy" />
            </div>
            <div class="personal-piece-meta">
              <span class="collection-tag">${badge} · ${p.brand}</span>
              <h4>${p.piecePt}</h4>
            </div>
            <div class="personal-piece-actions">
              <button type="button" class="btn-solid-sm btn-equip-personal" data-equip-id="${p.id}">${equipTxt}</button>
              <button type="button" class="reset-quiz-btn btn-delete-personal" data-delete-id="${p.id}">${delTxt}</button>
            </div>
          </article>
        `;
      })
      .join("");

    grid.querySelectorAll(".btn-equip-personal").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-equip-id");
        const piece = personalPieces.find((p) => p.id === id);
        if (!piece) return;
        const slotObj = FIT_SLOTS.find((s) => s.id === piece.slot);
        if (!slotObj) return;
        const idx = slotObj.items.findIndex((it) => it.id === piece.id);
        if (idx >= 0) {
          fitState[piece.slot] = idx;
          updateMannequinSVG();
          renderFitLab();
          const svgEl = document.getElementById("mannequin-svg");
          if (svgEl) svgEl.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      });
    });

    grid.querySelectorAll(".btn-delete-personal").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-delete-id");
        if (!id) return;
        personalPieces = personalPieces.filter((p) => p.id !== id);
        await deletePersonalPieceFromStorage(id);
        syncPersonalPiecesIntoFitSlots();
        updateMannequinSVG();
        renderFitLab();
        renderPersonalWardrobeGallery();
      });
    });
  }

  async function initPersonalWardrobe() {
    personalPieces = await loadPersonalPiecesFromStorage();
    syncPersonalPiecesIntoFitSlots();
    updateMannequinSVG();
    renderFitLab();
    renderPersonalWardrobeGallery();

    const fileInput = document.getElementById("custom-piece-file");
    const tuningWrap = document.getElementById("custom-cutout-tuning");
    const tolInput = document.getElementById("custom-cutout-tolerance");
    const tolBadge = document.getElementById("custom-tolerance-val");
    const innerInput = document.getElementById("custom-cutout-inner");
    const resetClicksBtn = document.getElementById("btn-reset-cutout-clicks");
    const saveBtn = document.getElementById("btn-save-custom-piece");
    const canvas = document.getElementById("custom-cutout-canvas");
    const placeholder = document.getElementById("custom-preview-placeholder");
    const feedback = document.getElementById("custom-upload-feedback");

    if (fileInput) {
      fileInput.addEventListener("change", (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) return;

        const nameInput = document.getElementById("custom-piece-name");
        if (nameInput && !nameInput.value.trim()) {
          nameInput.value = file.name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ");
        }

        const reader = new FileReader();
        reader.onload = (ev) => {
          const img = new Image();
          img.onload = () => {
            const maxDim = 620;
            const scale = Math.min(1, maxDim / Math.max(img.width, img.height));
            const w = Math.max(1, Math.round(img.width * scale));
            const h = Math.max(1, Math.round(img.height * scale));

            const offCanvas = document.createElement("canvas");
            offCanvas.width = w;
            offCanvas.height = h;
            const offCtx = offCanvas.getContext("2d");
            offCtx.drawImage(img, 0, 0, w, h);

            cutoutSourceImgData = offCtx.getImageData(0, 0, w, h);
            cutoutAutoSeeds = detectBorderBgColors(cutoutSourceImgData);
            cutoutExtraSeeds = [];

            if (placeholder) placeholder.hidden = true;
            if (canvas) canvas.hidden = false;
            if (tuningWrap) tuningWrap.hidden = false;
            if (feedback) {
              feedback.textContent = "";
              feedback.className = "form-feedback";
            }

            runCutoutEngine();
          };
          img.src = ev.target.result;
        };
        reader.readAsDataURL(file);
      });
    }

    if (tolInput) {
      tolInput.addEventListener("input", () => {
        if (tolBadge) tolBadge.textContent = tolInput.value;
        runCutoutEngine();
      });
    }

    if (innerInput) {
      innerInput.addEventListener("change", () => {
        runCutoutEngine();
      });
    }

    if (canvas) {
      canvas.addEventListener("click", (e) => {
        if (!cutoutSourceImgData) return;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const x = Math.max(0, Math.min(canvas.width - 1, Math.floor((e.clientX - rect.left) * scaleX)));
        const y = Math.max(0, Math.min(canvas.height - 1, Math.floor((e.clientY - rect.top) * scaleY)));
        const cIdx = (y * canvas.width + x) * 4;
        const src = cutoutSourceImgData.data;
        cutoutExtraSeeds.push({
          x,
          y,
          r: src[cIdx],
          g: src[cIdx + 1],
          b: src[cIdx + 2]
        });
        runCutoutEngine();
      });
    }

    if (resetClicksBtn) {
      resetClicksBtn.addEventListener("click", () => {
        cutoutExtraSeeds = [];
        if (tolInput) {
          tolInput.value = "36";
          if (tolBadge) tolBadge.textContent = "36";
        }
        runCutoutEngine();
      });
    }

    if (saveBtn) {
      saveBtn.addEventListener("click", async () => {
        const lang = i18n().getLang();
        if (!cutoutSourceImgData) {
          if (feedback) {
            feedback.textContent =
              lang === "en" ? "Please choose a garment photo first." : "Escolha uma foto de roupa primeiro.";
            feedback.className = "form-feedback err";
          }
          return;
        }

        const slotSelect = document.getElementById("custom-piece-slot");
        const nameInput = document.getElementById("custom-piece-name");
        const brandInput = document.getElementById("custom-piece-brand");

        const slot = slotSelect ? slotSelect.value : "top";
        const pieceName = (nameInput && nameInput.value.trim()) || (lang === "en" ? "My Custom Garment" : "Minha Peça Pessoal");
        const brandName = (brandInput && brandInput.value.trim()) || (lang === "en" ? "Personal Wardrobe" : "Acervo Pessoal");

        const croppedDataUrl = extractCroppedCutoutDataUrl();
        if (!croppedDataUrl) return;

        const newPiece = {
          id: "pw_" + Date.now() + "_" + Math.random().toString(36).slice(2, 7),
          slot,
          brand: brandName,
          piecePt: pieceName,
          pieceEn: pieceName,
          cutout: croppedDataUrl,
          createdAt: Date.now()
        };

        personalPieces.unshift(newPiece);
        await savePersonalPieceToStorage(newPiece);
        syncPersonalPiecesIntoFitSlots();

        fitState[slot] = 0;
        updateMannequinSVG();
        renderFitLab();
        renderPersonalWardrobeGallery();

        if (feedback) {
          feedback.textContent =
            lang === "en"
              ? "Garment cut out, added to your personal collection, and equipped on the mannequin!"
              : "Peça recortada, adicionada à sua coleção pessoal e vestida no manequim!";
          feedback.className = "form-feedback ok";
        }

        const svgEl = document.getElementById("mannequin-svg");
        if (svgEl) {
          setTimeout(() => {
            svgEl.scrollIntoView({ behavior: "smooth", block: "center" });
          }, 250);
        }
      });
    }
  }

  // ==========================================================================
  // INICIALIZAÇÃO
  // ==========================================================================
  async function loadBrands() {
    try {
      const res = await fetch("assets/data/marcas.json");
      if (res.ok) {
        brandsData = await res.json();
      }
    } catch (_) {}

    if (!brandsData.length) {
      document.querySelectorAll("#brands-grid .brand-card").forEach((link) => {
        const img = link.querySelector("img");
        if (!img) return;
        const url = link.getAttribute("href") || "";
        const handle = url.replace(/\/$/, "").split("/").pop() || "";
        const imgFile = (img.getAttribute("src") || "").split("/").pop() || "";
        const slug = imgFile.replace(/\.[^.]+$/, "").toLowerCase();
        brandsData.push({
          slug: slug || handle,
          name: (link.getAttribute("title") || handle).split(" (@")[0],
          handle,
          url,
          img: img.getAttribute("src") || "",
          categories: (link.getAttribute("data-categories") || "").split(/\s+/).filter(Boolean),
          vibes: ["streetwear", "contemporary"]
        });
      });
    }

    applyCatalogFilter();
    renderQuizResults();
    renderFitLab();
    renderCollections();
    renderDropSubscriptionSelector();
  }

  initSubtabs();
  initCatalogControls();
  initQuiz();
  initDropSubscription();
  initPersonalWardrobe();
  loadBrands();

  // Disparo silencioso em segundo plano para verificar se há drops começando em 1 hora
  fetch("api/cron_dispatch_drops.php?mode=ping").catch(() => {});

  window.addEventListener("emorphosis:langchange", () => {
    applyCatalogFilter();
    renderQuizResults();
    renderFitLab();
    renderCollections();
    updateSubCounter();
    renderPersonalWardrobeGallery();
  });
})();
