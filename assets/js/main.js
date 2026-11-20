/* ==========================================================================
   EMORPHOSIS — Main Script
   1. Autoplay silencioso nos vídeos de fundo
   2. Efeito de Glitch nos textos da header e títulos (data-glitch)
   3. Radar em Tempo Real de Usuários Ativos no Mapa do Brasil:
      - Converte (lat, lon) localmente em célula de pixel (mx, my) do mapa 2560x1440 (sem transmitir coordenadas GPS exatas de rua/casa)
      - Exibe apenas Cidade e Estado (ex: CURITIBA, PR) no tooltip do ponto
      - Usa os píxeis verdes de assets/data/brazil_map_bounds.json para confinar todos os pontos dentro do Brasil
   4. Fundo de ondas de pontos verdes caso exista #bg-matrix-waves na página
   ========================================================================== */

(function () {
  // 1. Garante autoplay silencioso em vídeos de fundo (desktop e mobile)
  document.querySelectorAll(".bg-layer video").forEach((vid) => {
    vid.muted = true;
    vid.defaultMuted = true;
    const playPromise = vid.play();
    if (playPromise && typeof playPromise.catch === "function") {
      playPromise.catch(() => {});
    }
  });

  // 2. Aplica atributo data-glitch para o efeito de glitch em camadas (::before / ::after)
  function syncGlitchAttributes() {
    const selectors = [
      ".nav-link",
      ".lang-btn",
      ".subtab-btn",
      ".filter-pill",
      ".section-heading",
      ".mystery-q-btn"
    ];
    document.querySelectorAll(selectors.join(",")).forEach((el) => {
      el.classList.add("glitch-text");
      el.setAttribute("data-glitch", (el.textContent || "").trim());
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", syncGlitchAttributes);
  } else {
    syncGlitchAttributes();
  }
  window.addEventListener("emorphosis:langchange", syncGlitchAttributes);

  // ==========================================================================
  // 3. RADAR DE PRESENÇA SEGURO (CIDADE/ESTADO + PIXEL CONFINADO PELA BORDA VERDE)
  // ==========================================================================
  const UID_KEY = "emorphosis_uid_v1";
  const ANON_PIXEL_KEY = "emorphosis_px_city_v2";

  try {
    localStorage.removeItem("emorphosis_geo_v1");
    localStorage.removeItem("emorphosis_geo_v2");
    localStorage.removeItem("emorphosis_geo_v3");
    localStorage.removeItem("emorphosis_geo_v4");
    sessionStorage.removeItem("emorphosis_px_anon_v1");
  } catch (e) {}

  function getOrCreateUid() {
    try {
      let uid = localStorage.getItem(UID_KEY);
      if (!uid || uid.length < 8) {
        const rand = Math.random().toString(36).substring(2, 10) + Date.now().toString(36).slice(-6);
        uid = "usr_" + rand;
        localStorage.setItem(UID_KEY, uid);
      }
      return uid;
    } catch (e) {
      return "usr_anon_" + Math.floor(Math.random() * 999999);
    }
  }

  function isInsideBrazil(lat, lon) {
    return (
      typeof lat === "number" &&
      typeof lon === "number" &&
      !isNaN(lat) &&
      !isNaN(lon) &&
      lat >= -33.9 &&
      lat <= 5.4 &&
      lon >= -74.2 &&
      lon <= -34.5
    );
  }

  const BRAZIL_MAP_ANCHORS = [
    { city: "Curitiba", region: "PR", lat: -25.4284, lon: -49.2733, x: 1001, y: 928 },
    { city: "Florianópolis", region: "SC", lat: -27.5954, lon: -48.5480, x: 1024, y: 972 },
    { city: "Porto Alegre", region: "RS", lat: -30.0346, lon: -51.2177, x: 982, y: 1024 },
    { city: "São Paulo", region: "SP", lat: -23.5505, lon: -46.6333, x: 1058, y: 888 },
    { city: "Rio de Janeiro", region: "RJ", lat: -22.9068, lon: -43.1729, x: 1134, y: 873 },
    { city: "Belo Horizonte", region: "MG", lat: -19.9167, lon: -43.9345, x: 1118, y: 815 },
    { city: "Vitória", region: "ES", lat: -20.3155, lon: -40.3128, x: 1184, y: 822 },
    { city: "Brasília", region: "DF", lat: -15.7939, lon: -47.8828, x: 1044, y: 738 },
    { city: "Goiânia", region: "GO", lat: -16.6869, lon: -49.2648, x: 1015, y: 755 },
    { city: "Campo Grande", region: "MS", lat: -20.4697, lon: -54.6201, x: 905, y: 822 },
    { city: "Cuiabá", region: "MT", lat: -15.6014, lon: -56.0979, x: 875, y: 725 },
    { city: "Salvador", region: "BA", lat: -12.9714, lon: -38.5014, x: 1230, y: 682 },
    { city: "Aracaju", region: "SE", lat: -10.9472, lon: -37.0731, x: 1260, y: 642 },
    { city: "Maceió", region: "AL", lat: -9.6658, lon: -35.7350, x: 1286, y: 618 },
    { city: "Recife", region: "PE", lat: -8.0476, lon: -34.8770, x: 1306, y: 588 },
    { city: "João Pessoa", region: "PB", lat: -7.1195, lon: -34.8450, x: 1310, y: 568 },
    { city: "Natal", region: "RN", lat: -5.7945, lon: -35.2110, x: 1298, y: 540 },
    { city: "Fortaleza", region: "CE", lat: -3.7172, lon: -38.5433, x: 1230, y: 502 },
    { city: "Teresina", region: "PI", lat: -5.0892, lon: -42.8019, x: 1148, y: 528 },
    { city: "São Luís", region: "MA", lat: -2.5307, lon: -44.3068, x: 1112, y: 478 },
    { city: "Belém", region: "PA", lat: -1.4558, lon: -48.4902, x: 1026, y: 454 },
    { city: "Macapá", region: "AP", lat: 0.0349, lon: -51.0694, x: 972, y: 420 },
    { city: "Palmas", region: "TO", lat: -10.1689, lon: -48.3317, x: 1032, y: 628 },
    { city: "Manaus", region: "AM", lat: -3.1190, lon: -60.0217, x: 768, y: 518 },
    { city: "Boa Vista", region: "RR", lat: 2.8235, lon: -60.6758, x: 765, y: 374 },
    { city: "Porto Velho", region: "RO", lat: -8.7619, lon: -63.9039, x: 710, y: 602 },
    { city: "Rio Branco", region: "AC", lat: -9.9754, lon: -67.8249, x: 625, y: 624 }
  ];

  function findNearestBrazilCity(lat, lon) {
    let best = BRAZIL_MAP_ANCHORS[0];
    let bestDist = Infinity;
    for (const a of BRAZIL_MAP_ANCHORS) {
      const d = (lat - a.lat) * (lat - a.lat) + (lon - a.lon) * (lon - a.lon);
      if (d < bestDist) {
        bestDist = d;
        best = a;
      }
    }
    return best;
  }

  let brazilBorderData = {
    imageWidth: 2560,
    imageHeight: 1440,
    pixelBounds: { minX: 496, maxX: 1333, minY: 325, maxY: 1110 },
    geoExtremes: { latNorth: 5.2718, latSouth: -33.7512, lonWest: -73.9828, lonEast: -34.7931 },
    rows: null,
    cols: null
  };

  fetch("assets/data/brazil_map_bounds.json?v=20261111c")
    .then((r) => (r.ok ? r.json() : null))
    .then((json) => {
      if (json && json.pixelBounds && json.rows && json.cols) {
        brazilBorderData = json;
        renderBrazilMapRadar();
      }
    })
    .catch(() => {});

  function clampInsideBrazilGreenBorder(x, y, padPx = 8) {
    const pb = brazilBorderData.pixelBounds || { minX: 496, maxX: 1333, minY: 325, maxY: 1110 };
    let cx = Math.max(pb.minX + padPx, Math.min(pb.maxX - padPx, x));
    let cy = Math.max(pb.minY + padPx, Math.min(pb.maxY - padPx, y));

    if (brazilBorderData.rows && brazilBorderData.cols) {
      const ry = String(Math.max(pb.minY, Math.min(pb.maxY, Math.round(cy))));
      const rowSpan = brazilBorderData.rows[ry];
      if (Array.isArray(rowSpan) && rowSpan.length === 2) {
        const minRx = rowSpan[0] + padPx;
        const maxRx = rowSpan[1] - padPx;
        if (minRx <= maxRx) {
          cx = Math.max(minRx, Math.min(maxRx, cx));
        } else {
          cx = (rowSpan[0] + rowSpan[1]) * 0.5;
        }
      }

      const rx = String(Math.max(pb.minX, Math.min(pb.maxX, Math.round(cx))));
      const colSpan = brazilBorderData.cols[rx];
      if (Array.isArray(colSpan) && colSpan.length === 2) {
        const minCy = colSpan[0] + padPx;
        const maxCy = colSpan[1] - padPx;
        if (minCy <= maxCy) {
          cy = Math.max(minCy, Math.min(maxCy, cy));
        } else {
          cy = (colSpan[0] + colSpan[1]) * 0.5;
        }
      }

      const ry2 = String(Math.max(pb.minY, Math.min(pb.maxY, Math.round(cy))));
      const rowSpan2 = brazilBorderData.rows[ry2];
      if (Array.isArray(rowSpan2) && rowSpan2.length === 2) {
        const minRx2 = rowSpan2[0] + padPx;
        const maxRx2 = rowSpan2[1] - padPx;
        if (minRx2 <= maxRx2) {
          cx = Math.max(minRx2, Math.min(maxRx2, cx));
        }
      }
    }

    return { imgX: cx, imgY: cy };
  }

  function baseGreenBorderProjection(lat, lon) {
    const pb = brazilBorderData.pixelBounds || { minX: 496, maxX: 1333, minY: 325, maxY: 1110 };
    const ge = brazilBorderData.geoExtremes || {
      latNorth: 5.2718,
      latSouth: -33.7512,
      lonWest: -73.9828,
      lonEast: -34.7931
    };

    const normX = (lon - ge.lonWest) / (ge.lonEast - ge.lonWest);
    const normY = (ge.latNorth - lat) / (ge.latNorth - ge.latSouth);

    const x = pb.minX + normX * (pb.maxX - pb.minX) - normY * 14.0;
    const y = pb.minY + normY * (pb.maxY - pb.minY) + (normX - 0.35) * 18.0;
    return { x, y };
  }

  function latLonToQuantizedPixel(lat, lon) {
    for (const a of BRAZIL_MAP_ANCHORS) {
      const dLat = lat - a.lat;
      const dLon = lon - a.lon;
      if (dLat * dLat + dLon * dLon < 0.04) {
        const c = clampInsideBrazilGreenBorder(a.x, a.y, 8);
        return {
          mx: Math.round(c.imgX / 6) * 6,
          my: Math.round(c.imgY / 6) * 6
        };
      }
    }

    const base = baseGreenBorderProjection(lat, lon);
    let sumW = 0;
    let sumDx = 0;
    let sumDy = 0;

    for (const a of BRAZIL_MAP_ANCHORS) {
      const d2 = (lat - a.lat) * (lat - a.lat) + (lon - a.lon) * (lon - a.lon) + 0.001;
      const w = 1 / (d2 * d2);
      const aBase = baseGreenBorderProjection(a.lat, a.lon);
      sumW += w;
      sumDx += w * (a.x - aBase.x);
      sumDy += w * (a.y - aBase.y);
    }

    const rawX = base.x + (sumW > 0 ? sumDx / sumW : 0);
    const rawY = base.y + (sumW > 0 ? sumDy / sumW : 0);
    const clamped = clampInsideBrazilGreenBorder(rawX, rawY, 8);

    return {
      mx: Math.round(clamped.imgX / 6) * 6,
      my: Math.round(clamped.imgY / 6) * 6
    };
  }

  let hasExactBrowserGps = false;

  async function reverseGeocodeCityState(lat, lon) {
    try {
      const ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
      const timer = ctrl ? setTimeout(() => ctrl.abort(), 2500) : null;
      const url = `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${encodeURIComponent(lat)}&longitude=${encodeURIComponent(lon)}&localityLanguage=pt`;
      const res = await fetch(url, ctrl ? { signal: ctrl.signal } : {});
      if (timer) clearTimeout(timer);
      if (res.ok) {
        const d = await res.json();
        const city = d.city || d.locality || "";
        let region = "";
        if (d.principalSubdivisionCode && String(d.principalSubdivisionCode).includes("-")) {
          region = String(d.principalSubdivisionCode).split("-")[1];
        }
        if (city) {
          return { city, region: region || "BR" };
        }
      }
    } catch (e) {}
    const nearest = findNearestBrazilCity(lat, lon);
    return { city: nearest.city, region: nearest.region };
  }

  function requestBrowserGeolocationPermission(forcePrompt = false) {
    return new Promise((resolve) => {
      if (!("geolocation" in navigator)) {
        resolve(null);
        return;
      }
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const lat = Number(pos.coords.latitude);
          const lon = Number(pos.coords.longitude);
          if (isInsideBrazil(lat, lon)) {
            hasExactBrowserGps = true;
            const place = await reverseGeocodeCityState(lat, lon);
            // Converte (lat, lon) em pixel quantizado (mx, my) e descarta lat/lon exatos
            const px = latLonToQuantizedPixel(lat, lon);
            const anonInfo = {
              city: place.city,
              region: place.region,
              mx: px.mx,
              my: px.my,
              exact_gps: true,
              ts: Date.now()
            };
            try {
              sessionStorage.setItem(ANON_PIXEL_KEY, JSON.stringify(anonInfo));
            } catch (e) {}
            resolve(anonInfo);
          } else {
            resolve(null);
          }
        },
        () => {
          resolve(null);
        },
        {
          enableHighAccuracy: false,
          timeout: forcePrompt ? 10000 : 6000,
          maximumAge: 300000
        }
      );
    });
  }

  async function resolveClientAnonymousPixel() {
    try {
      const raw = sessionStorage.getItem(ANON_PIXEL_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && parsed.ts && Date.now() - parsed.ts < 3600000 * 2 && parsed.mx && parsed.my && parsed.city) {
          if (parsed.exact_gps) {
            hasExactBrowserGps = true;
            return parsed;
          }
        }
      }
    } catch (e) {}

    const gpsPixel = await requestBrowserGeolocationPermission(false);
    if (gpsPixel) {
      return gpsPixel;
    }

    try {
      const ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
      const timer = ctrl ? setTimeout(() => ctrl.abort(), 2200) : null;
      const res = await fetch("https://ipwho.is/", ctrl ? { signal: ctrl.signal } : {});
      if (timer) clearTimeout(timer);
      if (res.ok) {
        const d = await res.json();
        if (d && d.success && d.country_code === "BR") {
          let lat = Number(d.latitude);
          let lon = Number(d.longitude);
          const reg = String(d.region_code || "BR").toUpperCase();
          const city = d.city || "Brasil";
          if (reg === "PR" && lat >= -26.15 && lat <= -25.05 && lon >= -49.85 && lon <= -48.85) {
            lat = -25.4284;
            lon = -49.2733;
          }
          if (isInsideBrazil(lat, lon)) {
            const px = latLonToQuantizedPixel(lat, lon);
            const anonInfo = {
              city,
              region: reg,
              mx: px.mx,
              my: px.my,
              exact_gps: false,
              ts: Date.now()
            };
            try {
              sessionStorage.setItem(ANON_PIXEL_KEY, JSON.stringify(anonInfo));
            } catch (e) {}
            return anonInfo;
          }
        }
      }
    } catch (e) {}

    return null;
  }

  const IMG_W = 2560;
  const IMG_H = 1440;

  function imagePixelToScreen(imgX, imgY) {
    const bgImg = document.querySelector(".home-bg-img");
    let vpW = window.innerWidth;
    let vpH = window.innerHeight;
    let left0 = 0;
    let top0 = 0;
    let isMobileContain = vpW <= 820;

    if (bgImg) {
      const rect = bgImg.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        vpW = rect.width;
        vpH = rect.height;
        left0 = rect.left;
        top0 = rect.top;
      }
      const st = window.getComputedStyle(bgImg);
      if (st && st.objectFit) {
        isMobileContain = st.objectFit === "contain";
      }
    }

    const scale = isMobileContain
      ? Math.min(vpW / IMG_W, vpH / IMG_H)
      : Math.max(vpW / IMG_W, vpH / IMG_H);
    const posY = isMobileContain ? 0.54 : 0.56;

    const renderW = IMG_W * scale;
    const renderH = IMG_H * scale;
    const offsetX = left0 + (vpW - renderW) * 0.5;
    const offsetY = top0 + (vpH - renderH) * posY;

    return {
      x: offsetX + (imgX / IMG_W) * renderW,
      y: offsetY + (imgY / IMG_H) * renderH
    };
  }

  const radarContainer = document.getElementById("brazil-map-radar");
  let activeUsersList = [];
  let totalUniqueVisitors = 0;
  let hudEl = null;

  // ==========================================================================
  // 3B. MAPA INTERATIVO POR ESTADO -> JANELA DE APLICATIVO DE COMPUTADOR (H0M3)
  //     - No mapa principal: apenas os 10 estados que possuem marcas são clicáveis
  //     - Ao clicar em um estado: abre uma janela estilo aplicativo de computador
  //       com o estado traçado em verde sobre fundo preto, os ícones de missão de
  //       espião de cada marca daquele estado, e o Dossiê de Análise Tática no
  //       canto inferior esquerdo da janela.
  // ==========================================================================
  let spyBrandsList = [];
  let statesShapesData = {};
  let mainStatesBeaconsEl = null;
  let osModalBackdropEl = null;
  let osWindowEl = null;
  let showSpyTargets = true;
  let openStateUf = null;
  let lockedSpySlug = null;
  let stateSearchQuery = "";
  let isOsWinMaximized = false;
  let isDossierCollapsed = false;
  let cmdTypewriterTimer = null;

  const STATE_ORDER = ["SP", "SC", "PR", "RS", "RJ", "MG", "ES", "GO", "DF", "RN"];

  const CAT_LABELS_PT = {
    roupas: "roupas e vestuário autoral",
    acessorios: "acessórios e joalheria",
    calcados: "calçados autorais",
    handmade: "produção handmade / artesanal",
    "sob medida": "modelagem sob medida e alfaiataria",
    upcycling: "upcycling e reconstrução de peças",
    diversos: "objetos e criações experimentais"
  };

  const VIBE_LABELS_PT = {
    streetwear: "streetwear",
    darkwear: "darkwear",
    avantgarde: "avant-garde",
    punk: "punk / underground",
    graphic: "design gráfico",
    contemporary: "contemporânea",
    minimal: "minimalista",
    tailoring: "alfaiataria",
    upcycling: "upcycling",
    artisanal: "artesanal",
    gorpcore: "gorpcore / utilitária",
    techwear: "techwear",
    cyber: "cyber",
    archive: "archive",
    experimental: "experimental",
    accessories: "acessórios",
    footwear: "footwear"
  };

  function buildBrandCmdNarrative(b, isEn) {
    const locStr = b.location || (b.city ? `${b.city} - ${b.state || "SP"}` : (b.state || "SP"));
    const dmsStr = formatDmsCoord(b.lat || -23.5505, b.lon || -46.6333);
    const rawCats = Array.isArray(b.categories) && b.categories.length ? b.categories : ["roupas"];
    const rawVibes = Array.isArray(b.vibes) && b.vibes.length ? b.vibes : ["streetwear", "contemporary"];

    if (isEn) {
      const catsEn = rawCats.join(", ");
      const vibesEn = rawVibes.slice(0, 3).join(", ");
      let pricePart = "Operates via limited drops, 1of1 releases, or direct inquiry on Instagram.";
      if (b.price_found && b.avg_price) {
        const minItem = b.min_item ? ` (${b.min_item})` : "";
        const maxItem = b.max_item ? ` (${b.max_item})` : "";
        pricePart = `Catalog pieces range from ${formatBrlSpy(b.min_price)}${minItem} up to ${formatBrlSpy(b.max_price)}${maxItem}, with an average price of ${formatBrlSpy(b.avg_price)}.`;
      }
      return [
        `C:\\EMORPHOSIS\\${b.state || "SP"}> query --brand "${b.name}" --ig @${b.handle}`,
        `[LOC] ${locStr} // GPS ${dmsStr}`,
        `[INFO] ${b.name} (@${b.handle}) is an independent Brazilian label based in ${locStr}, focused on ${catsEn} with a ${vibesEn} aesthetic. ${pricePart}`
      ].join("\n");
    }

    const catsPt = rawCats.map((c) => CAT_LABELS_PT[c] || c).join(", ");
    const vibesPt = rawVibes
      .slice(0, 3)
      .map((v) => VIBE_LABELS_PT[v] || v)
      .join(", ");

    let pricePartPt = "Atua com lançamentos por drops fechados, peças 1/1 ou atendimento direto via Instagram.";
    if (b.price_found && b.avg_price) {
      const minItem = b.min_item ? ` (${b.min_item})` : "";
      const maxItem = b.max_item ? ` (${b.max_item})` : "";
      pricePartPt = `No catálogo analisado, as peças vão de ${formatBrlSpy(b.min_price)}${minItem} até ${formatBrlSpy(b.max_price)}${maxItem}, registrando média de preço de ${formatBrlSpy(b.avg_price)}.`;
    }

    return [
      `C:\\EMORPHOSIS\\${b.state || "SP"}> analisar --marca "${b.name}" --ig @${b.handle}`,
      `[LOCAL] ${locStr} // GPS ${dmsStr}`,
      `[SOBRE] ${b.name} (@${b.handle}) é uma marca independente de ${locStr} voltada para ${catsPt}, com identidade ${vibesPt}. ${pricePartPt}`
    ].join("\n");
  }

  function startCmdTypewriter(targetEl, fullText) {
    if (cmdTypewriterTimer) {
      clearInterval(cmdTypewriterTimer);
      cmdTypewriterTimer = null;
    }
    if (!targetEl) return;
    targetEl.textContent = "";
    let idx = 0;
    const total = fullText.length;
    const step = 2;
    cmdTypewriterTimer = setInterval(() => {
      idx = Math.min(total, idx + step);
      targetEl.textContent = fullText.slice(0, idx);
      if (idx >= total) {
        clearInterval(cmdTypewriterTimer);
        cmdTypewriterTimer = null;
      }
    }, 16);
  }

  function formatDmsCoord(lat, lon) {
    const toDms = (val, posChar, negChar) => {
      const abs = Math.abs(Number(val) || 0);
      const deg = Math.floor(abs);
      const minFloat = (abs - deg) * 60;
      const min = Math.floor(minFloat);
      const sec = Math.round((minFloat - min) * 60);
      const dir = val >= 0 ? posChar : negChar;
      return `${String(deg).padStart(2, "0")}°${String(min).padStart(2, "0")}'${String(sec).padStart(2, "0")}"${dir}`;
    };
    return `${toDms(lat, "N", "S")} ${toDms(lon, "E", "W")}`;
  }

  function formatBrlSpy(val) {
    if (typeof val !== "number" || isNaN(val)) return "";
    return "R$ " + val.toFixed(2).replace(".", ",").replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  }

  function ensureMainStateMapElements() {
    if (!radarContainer) return;

    // Remove qualquer outline antigo do mapa principal caso exista
    const oldHitSvg = radarContainer.querySelector(".main-states-hit-svg");
    if (oldHitSvg) oldHitSvg.remove();

    if (!mainStatesBeaconsEl) {
      mainStatesBeaconsEl = document.createElement("div");
      mainStatesBeaconsEl.className = "main-states-beacons-layer";
      radarContainer.appendChild(mainStatesBeaconsEl);
    }

    if (!osModalBackdropEl) {
      osModalBackdropEl = document.createElement("div");
      osModalBackdropEl.id = "os-state-modal-backdrop";
      osModalBackdropEl.className = "os-state-modal-backdrop";
      osModalBackdropEl.hidden = true;
      osModalBackdropEl.innerHTML = `
        <section id="os-state-window" class="os-state-window" role="dialog" aria-modal="true" aria-label="Terminal Regional de Marcas"></section>
      `;
      osModalBackdropEl.addEventListener("click", (e) => {
        if (e.target === osModalBackdropEl) {
          closeStateOsWindow();
        }
      });
      document.body.appendChild(osModalBackdropEl);
      osWindowEl = osModalBackdropEl.querySelector("#os-state-window");
    }

    const oldDossier = document.getElementById("spy-mission-dossier");
    if (oldDossier) oldDossier.remove();
  }

  function buildMainMapStatesOverlay() {
    if (!radarContainer || !Object.keys(statesShapesData).length) return;
    ensureMainStateMapElements();

    const lang = (document.documentElement.getAttribute("lang") || "pt").toLowerCase();
    const isEn = lang.startsWith("en");

    mainStatesBeaconsEl.innerHTML = "";
    STATE_ORDER.filter((uf) => statesShapesData[uf]).forEach((uf, idx) => {
      const st = statesShapesData[uf];
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "main-state-beacon";
      btn.setAttribute("data-beacon-uf", uf);
      const countLabel = st.count === 1 ? (isEn ? "1 BRAND" : "1 MARCA") : `${st.count} ${isEn ? "BRANDS" : "MARCAS"}`;
      btn.setAttribute("aria-label", `${st.name} (${uf}): ${countLabel}`);

      btn.innerHTML = `
        <span class="msb-pulse" style="animation-delay:${(idx * 0.25).toFixed(2)}s"></span>
        <span class="msb-reticle" aria-hidden="true"></span>
        <span class="msb-pill">
          <span class="msb-uf">${uf}</span>
          <span class="msb-cnt">${st.count}</span>
        </span>
        <span class="msb-tooltip" role="tooltip">
          <span class="msbt-kicker">⌖ SETOR ${uf} // ${st.name.toUpperCase()}</span>
          <strong class="msbt-main">${countLabel} ${isEn ? "MAPPED" : "MAPEADA(S)"}</strong>
          <span class="msbt-cta">${isEn ? "CLICK TO OPEN SECTOR TERMINAL ▸" : "CLIQUE P/ ABRIR JANELA DO ESTADO ▸"}</span>
        </span>
      `;

      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        openStateOsWindow(uf);
      });

      mainStatesBeaconsEl.appendChild(btn);
    });

    updateMainStatesPositions();
  }

  function updateMainStatesPositions() {
    if (!mainStatesBeaconsEl) return;
    const isMobileView = window.innerWidth <= 820;
    mainStatesBeaconsEl.classList.toggle("is-mobile-bottom-row", isMobileView);
    mainStatesBeaconsEl.style.display = showSpyTargets ? (isMobileView ? "flex" : "block") : "none";

    if (isMobileView) {
      const imgBotPos = imagePixelToScreen(1280, 1440);
      const safeTop = Math.max(150, Math.min(window.innerHeight - 195, imgBotPos.y + 8));
      mainStatesBeaconsEl.style.top = `${safeTop.toFixed(1)}px`;
    } else {
      mainStatesBeaconsEl.style.top = "";
    }

    STATE_ORDER.forEach((uf) => {
      const st = statesShapesData[uf];
      if (!st) return;
      const beacon = mainStatesBeaconsEl.querySelector(`.main-state-beacon[data-beacon-uf="${uf}"]`);
      if (!beacon) return;
      if (isMobileView) {
        beacon.style.left = "";
        beacon.style.top = "";
      } else {
        const pos = imagePixelToScreen(Number(st.pin_x) || 1058, Number(st.pin_y) || 888);
        beacon.style.left = `${pos.x.toFixed(1)}px`;
        beacon.style.top = `${pos.y.toFixed(1)}px`;
      }
      beacon.classList.toggle("is-active-uf", openStateUf === uf);
    });
  }

  function openStateOsWindow(uf) {
    if (!statesShapesData[uf]) return;
    openStateUf = uf;
    stateSearchQuery = "";
    isDossierCollapsed = false;
    const stateBrands = spyBrandsList.filter((b) => b.state === uf);
    if (stateBrands.length) {
      if (!lockedSpySlug || !stateBrands.some((b) => b.slug === lockedSpySlug)) {
        lockedSpySlug = stateBrands[0].slug;
      }
    } else {
      lockedSpySlug = null;
    }
    if (osModalBackdropEl) {
      osModalBackdropEl.hidden = false;
    }
    updateMainStatesPositions();
    renderStateOsWindow();
  }

  function closeStateOsWindow() {
    openStateUf = null;
    if (cmdTypewriterTimer) {
      clearInterval(cmdTypewriterTimer);
      cmdTypewriterTimer = null;
    }
    if (osModalBackdropEl) {
      osModalBackdropEl.hidden = true;
    }
    updateMainStatesPositions();
  }

  function stepStateBrandTarget(delta) {
    if (!openStateUf) return;
    const pool = getFilteredStateBrands();
    if (!pool.length) return;
    const currIdx = pool.findIndex((b) => b.slug === lockedSpySlug);
    const nextIdx = currIdx < 0 ? 0 : (currIdx + delta + pool.length) % pool.length;
    lockedSpySlug = pool[nextIdx].slug;
    isDossierCollapsed = false;
    updateStateWindowSelection();
  }

  function getFilteredStateBrands() {
    if (!openStateUf) return [];
    const q = stateSearchQuery.trim().toLowerCase();
    return spyBrandsList.filter((b) => {
      if (b.state !== openStateUf) return false;
      if (!q) return true;
      return (
        b.name.toLowerCase().includes(q) ||
        b.handle.toLowerCase().includes(q) ||
        (b.city && b.city.toLowerCase().includes(q))
      );
    });
  }

  function renderStateOsWindow() {
    if (!osWindowEl || !openStateUf || !statesShapesData[openStateUf]) return;

    const st = statesShapesData[openStateUf];
    const lang = (document.documentElement.getAttribute("lang") || "pt").toLowerCase();
    const isEn = lang.startsWith("en");
    const allStateBrands = spyBrandsList.filter((b) => b.state === openStateUf);

    osWindowEl.classList.toggle("is-maximized", isOsWinMaximized);

    const stateTabsHtml = STATE_ORDER.filter((u) => statesShapesData[u])
      .map((u) => {
        const info = statesShapesData[u];
        return `<button type="button" class="os-uf-tab${u === openStateUf ? " active" : ""}" data-switch-uf="${u}" title="${info.name}">
          <span>${u}</span>
          <small>${info.count}</small>
        </button>`;
      })
      .join("");

    const cityLabelsSvg = (st.cities || [])
      .slice(0, 12)
      .map(
        (c) => `
        <g class="os-city-ref" transform="translate(${c.x}, ${c.y})">
          <circle r="3.4" class="os-city-ref-dot" />
          <text x="8" y="4" class="os-city-ref-label">${c.city.toUpperCase()}</text>
        </g>`
      )
      .join("");

    osWindowEl.innerHTML = `
      <!-- Barra de Título Estilo Aplicativo de Computador -->
      <header class="os-win-titlebar" id="os-win-titlebar">
        <div class="os-win-title-left">
          <span class="os-win-app-dot"></span>
          <span class="os-win-path">C:\\EMORPHOSIS\\SAT_RECON\\SETOR_${st.uf}.EXE</span>
          <span class="os-win-sep">//</span>
          <strong class="os-win-sector-name">${st.name.toUpperCase()} (${st.count} ${isEn ? "TARGETS" : "MARCAS"})</strong>
        </div>
        <div class="os-win-controls">
          <button type="button" class="os-win-ctrl-btn" id="os-win-max-btn" title="${isEn ? "Maximize / Restore window" : "Maximizar / Restaurar janela"}">${isOsWinMaximized ? "❐" : "□"}</button>
          <button type="button" class="os-win-ctrl-btn os-win-close-btn" id="os-win-close-btn" title="${isEn ? "Close window (Esc)" : "Fechar janela (Esc)"}">✕</button>
        </div>
      </header>

      <!-- Barra de Ferramentas do Aplicativo: Seletor de Estados + Busca de Marca na Região -->
      <div class="os-win-toolbar">
        <div class="os-win-uf-tabs" role="tablist" aria-label="Alternar estado">
          ${stateTabsHtml}
        </div>
        <div class="os-win-search-box">
          <span class="os-search-icon" aria-hidden="true">⌖</span>
          <input
            type="search"
            id="os-state-search-input"
            class="os-state-search-input"
            placeholder="${isEn ? `Search target in ${st.uf}...` : `Filtrar alvo em ${st.name}...`}"
            value="${stateSearchQuery.replace(/"/g, "&quot;")}"
            autocomplete="off"
          />
        </div>
      </div>

      <!-- Palco Principal da Janela: Imagem de Grade enviada pelo usuário no fundo + Estado Traçado em Branco com Glow + Ícones de Missão + Prompt CMD no Canto Inferior Esquerdo -->
      <div class="os-win-stage" id="os-win-stage">
        <div class="os-map-canvas-frame" id="os-map-canvas-frame">
          <!-- Contorno Branco Brilhante (Glow) do Estado (viewBox 1000x660) -->
          <svg class="os-state-map-svg" id="os-state-map-svg" viewBox="0 0 1000 660" preserveAspectRatio="none">
            <defs>
              <filter id="stateWhiteGlow" x="-25%" y="-25%" width="150%" height="150%">
                <feGaussianBlur stdDeviation="4.5" result="blur1" />
                <feGaussianBlur stdDeviation="11" result="blur2" />
                <feMerge>
                  <feMergeNode in="blur2" />
                  <feMergeNode in="blur1" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            <!-- Estado Traçado em Branco com Efeito de Glow -->
            <path d="${st.window_svg_path}" class="os-state-glow-outer" filter="url(#stateWhiteGlow)" />
            <path d="${st.window_svg_path}" class="os-state-fill-outline" />

            <!-- Referências das Cidades Mapeadas -->
            ${cityLabelsSvg}

            <!-- Linha Vetorial Tracejada Conectando o Alvo Selecionado ao Prompt CMD no Canto Inferior Esquerdo -->
            <line id="os-win-lock-glow" class="os-win-lock-glow" x1="0" y1="0" x2="0" y2="0" />
            <line id="os-win-lock-line" class="os-win-lock-line" x1="0" y1="0" x2="0" y2="0" />
            <circle id="os-win-lock-ring" class="os-win-lock-ring" cx="0" cy="0" r="14" />
          </svg>

          <!-- Camada de Ícones de Missão de Espião de Cada Marca do Estado -->
          <div class="os-state-targets-layer" id="os-state-targets-layer">
            ${allStateBrands
              .map((b, idx) => {
                const leftPct = ((Number(b.state_x) || 500) / 1000) * 100;
                const topPct = ((Number(b.state_y) || 330) / 660) * 100;
                const codeNum = String(idx + 1).padStart(2, "0");
                const avgTxt = b.price_found && b.avg_price ? `MÉDIA ${formatBrlSpy(b.avg_price)}` : "DROP / SOB CONSULTA";
                const targetLoc = b.location || (b.city ? `${b.city} - ${b.state}` : b.state);
                return `
                  <button
                    type="button"
                    class="os-brand-target${b.slug === lockedSpySlug ? " is-locked" : ""}"
                    data-target-slug="${b.slug}"
                    style="left:${leftPct.toFixed(2)}%; top:${topPct.toFixed(2)}%;"
                    aria-label="Alvo ${b.name} (${targetLoc})"
                  >
                    <span class="obt-scan" style="animation-delay:${((idx * 0.21) % 2.8).toFixed(2)}s"></span>
                    <span class="obt-reticle" aria-hidden="true"></span>
                    <span class="obt-core" aria-hidden="true"></span>
                    <span class="obt-tooltip" role="tooltip">
                      <span class="obtt-kicker">⌖ ALVO #${codeNum}</span>
                      <strong class="obtt-name">${b.name}</strong>
                      <span class="obtt-city">📍 ${targetLoc.toUpperCase()}</span>
                      <span class="obtt-meta">@${b.handle} • ${avgTxt}</span>
                    </span>
                  </button>
                `;
              })
              .join("")}
          </div>
        </div>

        <!-- HUD de Coordenadas do Estado no Canto Superior Esquerdo do Palco -->
        <div class="os-stage-hud-top">
          <span class="os-hud-tag"><span class="spy-led"></span>SAT_LINK // ${st.name.toUpperCase()} [${st.uf}]</span>
          <span class="os-hud-sub">${allStateBrands.length} ${isEn ? "ACTIVE TARGETS IN SECTOR — CLICK ANY POINT TO ANALYZE" : "ALVO(S) NO SETOR — CLIQUE EM QUALQUER PONTO PARA ANALISAR"}</span>
        </div>

        <!-- Prompt de Comando (CMD) Inserido no Canto Inferior Esquerdo da Janela -->
        <aside id="os-win-dossier" class="os-win-cmd" aria-label="Prompt de comando sobre a marca selecionada"></aside>
      </div>

      <!-- Barra de Status Inferior da Janela de Computador -->
      <footer class="os-win-statusbar">
        <span>STATUS: ${isEn ? "SECTOR ONLINE // CMD TERMINAL ACTIVE" : "SETOR ONLINE // PROMPT DE COMANDO ATIVO"}</span>
        <span>${st.cities.length} ${isEn ? "CITIES MAPPED IN" : "CIDADE(S) MAPEADA(S) EM"} ${st.uf}</span>
      </footer>
    `;

    // Eventos da janela
    const closeBtn = osWindowEl.querySelector("#os-win-close-btn");
    const maxBtn = osWindowEl.querySelector("#os-win-max-btn");
    if (closeBtn) closeBtn.addEventListener("click", closeStateOsWindow);
    if (maxBtn) {
      maxBtn.addEventListener("click", () => {
        isOsWinMaximized = !isOsWinMaximized;
        osWindowEl.classList.toggle("is-maximized", isOsWinMaximized);
        maxBtn.textContent = isOsWinMaximized ? "❐" : "□";
        requestAnimationFrame(updateStateWinVectorLine);
      });
    }

    osWindowEl.querySelectorAll(".os-uf-tab").forEach((tabBtn) => {
      tabBtn.addEventListener("click", () => {
        const nextUf = tabBtn.getAttribute("data-switch-uf");
        if (nextUf && nextUf !== openStateUf) {
          openStateOsWindow(nextUf);
        }
      });
    });

    const searchInput = osWindowEl.querySelector("#os-state-search-input");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        stateSearchQuery = e.target.value || "";
        const matches = getFilteredStateBrands();
        if (matches.length && !matches.some((b) => b.slug === lockedSpySlug)) {
          lockedSpySlug = matches[0].slug;
        }
        updateStateWindowSelection();
      });
    }

    osWindowEl.querySelectorAll(".os-brand-target").forEach((tBtn) => {
      tBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        const slug = tBtn.getAttribute("data-target-slug");
        if (slug) {
          lockedSpySlug = slug;
          isDossierCollapsed = false;
          updateStateWindowSelection();
        }
      });
    });

    updateStateWindowSelection();
  }

  function updateStateWindowSelection() {
    if (!osWindowEl || !openStateUf) return;

    const q = stateSearchQuery.trim().toLowerCase();
    osWindowEl.querySelectorAll(".os-brand-target").forEach((tBtn) => {
      const slug = tBtn.getAttribute("data-target-slug");
      const b = spyBrandsList.find((item) => item.slug === slug);
      const matches =
        !q ||
        (b &&
          (b.name.toLowerCase().includes(q) ||
            b.handle.toLowerCase().includes(q) ||
            (b.city && b.city.toLowerCase().includes(q))));
      tBtn.classList.toggle("is-dimmed", !matches);
      tBtn.classList.toggle("is-locked", slug === lockedSpySlug);
    });

    renderStateWindowDossier();
    requestAnimationFrame(updateStateWinVectorLine);
  }

  function renderStateWindowDossier() {
    if (!osWindowEl || !openStateUf) return;
    const dossierEl = osWindowEl.querySelector("#os-win-dossier");
    if (!dossierEl) return;

    const lang = (document.documentElement.getAttribute("lang") || "pt").toLowerCase();
    const isEn = lang.startsWith("en");
    const stateBrands = spyBrandsList.filter((b) => b.state === openStateUf);
    const currIdx = stateBrands.findIndex((b) => b.slug === lockedSpySlug);
    const b = currIdx >= 0 ? stateBrands[currIdx] : stateBrands[0];

    if (!b) {
      dossierEl.innerHTML = "";
      return;
    }

    const codeNum = String((currIdx >= 0 ? currIdx : 0) + 1).padStart(2, "0");
    const totalInState = String(stateBrands.length).padStart(2, "0");
    const locStr = b.location || (b.city ? `${b.city} - ${b.state || "SP"}` : (b.state || "SP"));

    if (isDossierCollapsed) {
      if (cmdTypewriterTimer) {
        clearInterval(cmdTypewriterTimer);
        cmdTypewriterTimer = null;
      }
      dossierEl.className = "os-win-cmd is-collapsed";
      dossierEl.innerHTML = `
        <div class="cmd-titlebar">
          <span class="cmd-title-text"><span class="cmd-prompt-badge">&gt;_</span> CMD.EXE // ${b.name.toUpperCase()} (${locStr})</span>
          <button type="button" class="spy-nav-btn" id="os-dossier-expand-btn" title="${isEn ? "Expand command prompt" : "Expandir prompt de comando"}">▴</button>
        </div>
      `;
      const expBtn = dossierEl.querySelector("#os-dossier-expand-btn");
      if (expBtn) {
        expBtn.addEventListener("click", () => {
          isDossierCollapsed = false;
          renderStateWindowDossier();
          requestAnimationFrame(updateStateWinVectorLine);
        });
      }
      return;
    }

    const sameCityBrands = b.city ? stateBrands.filter((other) => other.city === b.city) : [];
    const switcherPool = sameCityBrands.length > 1 ? sameCityBrands : stateBrands;
    const switcherLabel =
      sameCityBrands.length > 1
        ? isEn
          ? `SWITCH BRAND IN ${b.city.toUpperCase()} (${sameCityBrands.length}):`
          : `TROCAR MARCA EM ${b.city.toUpperCase()} (${sameCityBrands.length}):`
        : isEn
        ? `SWITCH BRAND IN ${openStateUf} (${stateBrands.length}):`
        : `TROCAR MARCA EM ${openStateUf} (${stateBrands.length}):`;

    const sectorHtml =
      switcherPool.length > 1
        ? `<div class="spy-sector-strip">
             <span class="spy-sector-label">${switcherLabel}</span>
             <div class="spy-sector-chips">
               ${switcherPool
                 .map(
                   (sb) =>
                     `<button type="button" class="spy-sector-chip${sb.slug === b.slug ? " active" : ""}" data-lock-slug="${sb.slug}">${sb.name}</button>`
                 )
                 .join("")}
             </div>
           </div>`
        : "";

    dossierEl.className = "os-win-cmd is-active";
    dossierEl.innerHTML = `
      <div class="cmd-titlebar">
        <span class="cmd-title-text"><span class="cmd-prompt-badge">&gt;_</span> C:\\WINDOWS\\SYSTEM32\\CMD.EXE — [${codeNum}/${totalInState}]</span>
        <div class="spy-dossier-nav">
          <button type="button" class="spy-nav-btn" id="os-dossier-prev-btn" title="${isEn ? "Previous brand" : "Marca anterior"}">◂</button>
          <button type="button" class="spy-nav-btn" id="os-dossier-next-btn" title="${isEn ? "Next brand" : "Próxima marca"}">▸</button>
          <button type="button" class="spy-nav-btn" id="os-dossier-min-btn" title="${isEn ? "Minimize prompt" : "Minimizar prompt"}">_</button>
        </div>
      </div>

      <div class="cmd-body">
        <div class="cmd-brand-header">
          <div class="spy-thumb-frame">
            <img src="${b.img}" alt="${b.name}" width="44" height="44" loading="lazy" />
            <span class="spy-thumb-scanline" aria-hidden="true"></span>
          </div>
          <div class="cmd-brand-meta">
            <strong class="cmd-brand-name">${b.name}</strong>
            <div class="cmd-brand-loc-row">
              <span class="cmd-city-badge">📍 ${locStr.toUpperCase()}</span>
              <span class="cmd-brand-sub">@${b.handle}</span>
            </div>
          </div>
        </div>

        <div class="cmd-terminal-screen" aria-live="polite">
          <span id="cmd-typed-output" class="cmd-typed-output"></span><span class="cmd-cursor" aria-hidden="true">█</span>
        </div>

        ${sectorHtml}

        <div class="spy-dossier-actions">
          <a href="${b.url}" target="_blank" rel="noopener noreferrer" class="spy-action-btn spy-action-primary">
            ${isEn ? "OFFICIAL INSTAGRAM ↗" : "INSTAGRAM OFICIAL ↗"}
          </a>
          ${
            b.store_url
              ? `<a href="${b.store_url}" target="_blank" rel="noopener noreferrer" class="spy-action-btn spy-action-secondary">
                   ${isEn ? "OFFICIAL SITE ↗" : "SITE OFICIAL ↗"}
                 </a>`
              : `<a href="m4rcas.html" class="spy-action-btn spy-action-secondary">
                   ${isEn ? "OPEN CATALOG ▸" : "VER CATÁLOGO ▸"}
                 </a>`
          }
        </div>
      </div>
    `;

    const typedEl = dossierEl.querySelector("#cmd-typed-output");
    const narrativeText = buildBrandCmdNarrative(b, isEn);
    startCmdTypewriter(typedEl, narrativeText);

    const prevBtn = dossierEl.querySelector("#os-dossier-prev-btn");
    const nextBtn = dossierEl.querySelector("#os-dossier-next-btn");
    const minBtn = dossierEl.querySelector("#os-dossier-min-btn");
    if (prevBtn) prevBtn.addEventListener("click", () => stepStateBrandTarget(-1));
    if (nextBtn) nextBtn.addEventListener("click", () => stepStateBrandTarget(1));
    if (minBtn) {
      minBtn.addEventListener("click", () => {
        isDossierCollapsed = true;
        renderStateWindowDossier();
        requestAnimationFrame(updateStateWinVectorLine);
      });
    }

    dossierEl.querySelectorAll(".spy-sector-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        const s = chip.getAttribute("data-lock-slug");
        if (s) {
          lockedSpySlug = s;
          updateStateWindowSelection();
        }
      });
    });

    const activeChip = dossierEl.querySelector(".spy-sector-chip.active");
    if (activeChip && activeChip.scrollIntoView) {
      activeChip.scrollIntoView({ block: "nearest", inline: "center" });
    }
  }

  function updateStateWinVectorLine() {
    if (!osWindowEl || !openStateUf) return;
    const stageEl = osWindowEl.querySelector("#os-win-stage");
    const frameEl = osWindowEl.querySelector("#os-map-canvas-frame");
    const svgEl = osWindowEl.querySelector("#os-state-map-svg");
    const line = osWindowEl.querySelector("#os-win-lock-line");
    const glow = osWindowEl.querySelector("#os-win-lock-glow");
    const ring = osWindowEl.querySelector("#os-win-lock-ring");
    const dossierEl = osWindowEl.querySelector("#os-win-dossier");

    if (stageEl && frameEl) {
      const sw = stageEl.clientWidth || 800;
      const sh = stageEl.clientHeight || 520;
      const scale = Math.min(sw / 1000, sh / 660);
      const fw = Math.round(1000 * scale);
      const fh = Math.round(660 * scale);
      frameEl.style.width = `${fw}px`;
      frameEl.style.height = `${fh}px`;
    }

    if (!svgEl || !line || !glow || !ring || !dossierEl || !lockedSpySlug) return;

    const b = spyBrandsList.find((item) => item.slug === lockedSpySlug && item.state === openStateUf);
    if (!b) {
      line.style.opacity = "0";
      glow.style.opacity = "0";
      ring.style.opacity = "0";
      return;
    }

    const tx = Number(b.state_x) || 500;
    const ty = Number(b.state_y) || 330;

    // Converte o canto superior direito do Dossiê (no canto inferior esquerdo da janela) para coordenadas viewBox 1000x660
    const svgRect = svgEl.getBoundingClientRect();
    const dosRect = dossierEl.getBoundingClientRect();
    let dx = 285;
    let dy = 480;
    if (svgRect.width > 0 && svgRect.height > 0 && dosRect.width > 0) {
      const anchorScreenX = dosRect.right - 14;
      const anchorScreenY = dosRect.top + 18;
      dx = ((anchorScreenX - svgRect.left) / svgRect.width) * 1000;
      dy = ((anchorScreenY - svgRect.top) / svgRect.height) * 660;
      dx = Math.max(20, Math.min(980, dx));
      dy = Math.max(20, Math.min(640, dy));
    }

    line.setAttribute("x1", tx.toFixed(1));
    line.setAttribute("y1", ty.toFixed(1));
    line.setAttribute("x2", dx.toFixed(1));
    line.setAttribute("y2", dy.toFixed(1));

    glow.setAttribute("x1", tx.toFixed(1));
    glow.setAttribute("y1", ty.toFixed(1));
    glow.setAttribute("x2", dx.toFixed(1));
    glow.setAttribute("y2", dy.toFixed(1));

    ring.setAttribute("cx", tx.toFixed(1));
    ring.setAttribute("cy", ty.toFixed(1));

    line.style.opacity = "1";
    glow.style.opacity = "1";
    ring.style.opacity = "1";
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && openStateUf) {
      closeStateOsWindow();
    }
  });

  let leftControlsEl = null;

  function initDreamCommandPrompt() {
    if (!radarContainer || document.getElementById("dream-cmd-overlay")) return;

    const overlay = document.createElement("div");
    overlay.id = "dream-cmd-overlay";
    overlay.className = "dream-cmd-overlay";
    overlay.innerHTML = `
      <div class="dream-cmd-window" id="dream-cmd-window" role="dialog" aria-modal="true" aria-label="Prompt de Comando Emorphosis">
        <header class="cmd-titlebar dream-cmd-titlebar">
          <span class="cmd-title-text"><span class="cmd-prompt-badge">&gt;_</span> C:\\WINDOWS\\SYSTEM32\\CMD.EXE — PROTOCOLO_EMORPHOSIS.BAT</span>
          <button type="button" class="spy-nav-btn" id="dream-cmd-close-btn" title="Fechar">✕</button>
        </header>
        <div class="dream-cmd-body">
          <div class="dream-cmd-screen" id="dream-cmd-screen">
            <span id="dream-cmd-typed" class="cmd-typed-output"></span><span id="dream-cmd-cursor" class="cmd-cursor">█</span>
          </div>
          <form id="dream-cmd-form" class="dream-cmd-form" autocomplete="off">
            <span class="dream-input-prefix">&gt;</span>
            <input
              type="text"
              id="dream-cmd-input"
              class="dream-cmd-input"
              placeholder="Digite qual é o seu maior sonho e pressione Enter..."
              required
              maxlength="180"
            />
            <button type="submit" class="dream-cmd-submit">ENVIAR ↵</button>
          </form>
        </div>
      </div>

      <!-- Tela Preta Opaca em Tela Cheia com #emorphosis Glitch no Centro + Frases Espalhadas Piscando -->
      <div id="dream-blackout-stage" class="dream-blackout-stage" hidden aria-live="assertive">
        <div id="dream-scattered-layer" class="dream-scattered-layer" aria-hidden="true"></div>
        <div id="dream-center-emorphosis" class="dream-center-emorphosis" data-text="#emorphosis">#emorphosis</div>
      </div>
    `;

    document.body.appendChild(overlay);

    const typedEl = overlay.querySelector("#dream-cmd-typed");
    const formEl = overlay.querySelector("#dream-cmd-form");
    const inputEl = overlay.querySelector("#dream-cmd-input");
    const closeBtn = overlay.querySelector("#dream-cmd-close-btn");
    const blackoutEl = overlay.querySelector("#dream-blackout-stage");
    const scatteredLayerEl = overlay.querySelector("#dream-scattered-layer");
    const centerTagEl = overlay.querySelector("#dream-center-emorphosis");
    const winEl = overlay.querySelector("#dream-cmd-window");

    let dreamTimers = [];
    const clearDreamTimers = () => {
      dreamTimers.forEach((t) => clearTimeout(t));
      dreamTimers = [];
    };

    const closeDreamPrompt = () => {
      clearDreamTimers();
      if (winEl) winEl.classList.add("is-closing");
      overlay.classList.add("is-closing");
      setTimeout(() => {
        if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
      }, 380);
    };

    if (closeBtn) {
      closeBtn.addEventListener("click", closeDreamPrompt);
    }

    const typeLines = (text, speedMs, onDone) => {
      if (!typedEl) return;
      typedEl.textContent = "";
      let i = 0;
      const step = () => {
        i = Math.min(text.length, i + 2);
        typedEl.textContent = text.slice(0, i);
        if (i < text.length) {
          dreamTimers.push(setTimeout(step, speedMs));
        } else if (typeof onDone === "function") {
          onDone();
        }
      };
      step();
    };

    const introPrompt = "C:\\EMORPHOSIS\\NUCLEO> iniciar_conexao --usuario\n> Qual é o seu maior sonho?";
    typeLines(introPrompt, 20, () => {
      if (inputEl) inputEl.focus();
    });

    if (formEl && inputEl) {
      formEl.addEventListener("submit", (e) => {
        e.preventDefault();
        const userDream = inputEl.value.trim();
        if (!userDream) return;

        formEl.hidden = true;

        // Salva a resposta no diretório do servidor (/sonhos/ e api/save_dream.php)
        (async () => {
          try {
            let city = "";
            let region = "";
            try {
              const cachedPx = sessionStorage.getItem(ANON_PIXEL_KEY);
              if (cachedPx) {
                const parsed = JSON.parse(cachedPx);
                city = parsed.city || "";
                region = parsed.region || "";
              }
            } catch (_) {}
            await fetch("api/save_dream.php", {
              method: "POST",
              keepalive: true,
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ dream: userDream, city, region })
            });
          } catch (_) {}
        })();

        const confirmAndShortText =
          `C:\\EMORPHOSIS\\NUCLEO> "${userDream}"\n` +
          `> [CONFIRMAÇÃO] Resposta recebida com sucesso.\n\n` +
          `> sonho registrado, ajude os outros, ajude a mim, ajude a si mesmo e todos nos emergiremos`;

        typeLines(confirmAndShortText, 20, () => {
          // Oculta a janela do prompt e materializa #emorphosis no centro da tela com fundo preto opaco
          dreamTimers.push(
            setTimeout(() => {
              if (winEl) winEl.style.display = "none";
              if (blackoutEl) {
                blackoutEl.hidden = false;
                blackoutEl.classList.add("is-active");
              }
              if (centerTagEl) {
                centerTagEl.classList.add("is-materialized");
              }

              const phrases = [
                "ESPALHE A MENSAGEM",
                "INFECTE OS OUTROS",
                "DESTRUA OS PRECONCEITOS",
                "LUTE PELO QUE É SEU"
              ];

              // Posições espalhadas por toda a tela (evitando a faixa central onde está #emorphosis)
              const slots = [
                { left: "14%", top: "14%", rot: "-2deg" },
                { left: "80%", top: "16%", rot: "2deg" },
                { left: "22%", top: "30%", rot: "1.5deg" },
                { left: "78%", top: "31%", rot: "-1.5deg" },
                { left: "15%", top: "70%", rot: "-1.8deg" },
                { left: "83%", top: "68%", rot: "2deg" },
                { left: "24%", top: "84%", rot: "1.2deg" },
                { left: "76%", top: "85%", rot: "-1.5deg" },
                { left: "50%", top: "21%", rot: "0deg" },
                { left: "50%", top: "79%", rot: "0deg" }
              ];

              // Cria nós espalhados pela tela e pisca várias vezes em sequência
              const spawnWave = (waveIdx) => {
                if (!scatteredLayerEl) return;
                scatteredLayerEl.innerHTML = "";
                const shuffled = [...slots].sort(() => Math.random() - 0.5);
                const picks = shuffled.slice(0, 4);
                phrases.forEach((txt, pIdx) => {
                  const pos = picks[pIdx % picks.length];
                  const el = document.createElement("div");
                  const variant = (waveIdx + pIdx) % 3 === 1 ? " is-inverted" : (waveIdx + pIdx) % 3 === 2 ? " is-white" : "";
                  el.className = "dream-scattered-phrase" + variant;
                  el.setAttribute("data-text", txt);
                  el.textContent = txt;
                  el.style.left = pos.left;
                  el.style.top = pos.top;
                  el.style.setProperty("--phrase-rot", pos.rot);
                  el.style.animationDelay = `${(pIdx * 0.04).toFixed(2)}s`;
                  scatteredLayerEl.appendChild(el);
                });
              };

              const totalWaves = 9;
              const waveIntervalMs = 340;
              dreamTimers.push(
                setTimeout(() => {
                  for (let w = 0; w < totalWaves; w++) {
                    dreamTimers.push(
                      setTimeout(() => {
                        spawnWave(w);
                      }, w * waveIntervalMs)
                    );
                  }

                  dreamTimers.push(
                    setTimeout(() => {
                      closeDreamPrompt();
                    }, totalWaves * waveIntervalMs + 320)
                  );
                }, 620)
              );
            }, 680)
          );
        });
      });
    }
  }

  if (radarContainer) {
    initDreamCommandPrompt();

    Promise.all([
      fetch("assets/data/marcas.json?v=20261119a").then((r) => (r.ok ? r.json() : [])),
      fetch("assets/data/brazil_states_shapes.json?v=20261119a").then((r) => (r.ok ? r.json() : {}))
    ])
      .then(([brands, shapes]) => {
        if (Array.isArray(brands)) spyBrandsList = brands;
        if (shapes && typeof shapes === "object") statesShapesData = shapes;
        buildMainMapStatesOverlay();
      })
      .catch(() => {});
  }

  function renderBrazilMapRadar() {
    if (!radarContainer) return;

    if (!hudEl) {
      hudEl = document.createElement("div");
      hudEl.className = "map-radar-hud";
      hudEl.innerHTML = `<span class="map-radar-hud-dot"></span><span class="map-radar-hud-text"></span>`;
      radarContainer.appendChild(hudEl);
    }

    if (!leftControlsEl) {
      leftControlsEl = document.createElement("div");
      leftControlsEl.className = "map-left-controls";
      leftControlsEl.innerHTML = `
        <button type="button" class="map-left-action-btn map-radar-spy-toggle-btn active" title="Mostrar/ocultar setores estaduais com marcas no mapa">⌖ 10 ESTADOS</button>
        <button type="button" class="map-left-action-btn map-radar-gps-btn" title="Calibrar posição com permissão do navegador">📍 GPS</button>
      `;
      const spyToggleBtn = leftControlsEl.querySelector(".map-radar-spy-toggle-btn");
      if (spyToggleBtn) {
        spyToggleBtn.addEventListener("click", () => {
          showSpyTargets = !showSpyTargets;
          spyToggleBtn.classList.toggle("active", showSpyTargets);
          updateMainStatesPositions();
        });
      }
      const gpsBtn = leftControlsEl.querySelector(".map-radar-gps-btn");
      if (gpsBtn) {
        gpsBtn.addEventListener("click", async () => {
          const info = await requestBrowserGeolocationPermission(true);
          if (info) {
            clientPxPromise = Promise.resolve(info);
            await sendPresenceHeartbeat();
          } else {
            alert("Permita o acesso à localização no cadeado da barra de endereço do navegador para calibrar seu ponto no mapa.");
          }
        });
      }
      radarContainer.appendChild(leftControlsEl);
    }

    const hudPos = imagePixelToScreen(534, 326);
    hudEl.style.left = `${hudPos.x.toFixed(1)}px`;
    hudEl.style.top = `${hudPos.y.toFixed(1)}px`;

    const isMobileView = window.innerWidth <= 820;
    leftControlsEl.classList.toggle("is-mobile-above-hud", isMobileView);
    if (isMobileView) {
      // No telefone: centraliza o botão de estados (+ GPS se visível) na mesma linha horizontal acima da barra "RADAR ATIVO"
      const hudHeight = hudEl.offsetHeight || 26;
      leftControlsEl.style.left = "50%";
      leftControlsEl.style.top = `${(hudPos.y - hudHeight - 6).toFixed(1)}px`;
    } else {
      // No desktop: posiciona os 2 botões levemente maiores à esquerda do mapa do Brasil
      const leftMapPos = imagePixelToScreen(465, 515);
      const clampedLeftX = Math.max(16, Math.min(window.innerWidth - 170, leftMapPos.x - 135));
      const clampedLeftY = Math.max(110, Math.min(window.innerHeight - 160, leftMapPos.y));
      leftControlsEl.style.left = `${clampedLeftX.toFixed(1)}px`;
      leftControlsEl.style.top = `${clampedLeftY.toFixed(1)}px`;
    }

    const gpsBtn = leftControlsEl.querySelector(".map-radar-gps-btn");
    if (gpsBtn) {
      gpsBtn.style.display = hasExactBrowserGps ? "none" : "inline-flex";
    }

    const count = activeUsersList.length || 1;
    // Total acumulado de pessoas únicas (por IP): independe de quem está online agora e nunca diminui
    const uniqueTotal = Math.max(1, totalUniqueVisitors || 0);
    const lang = (document.documentElement.getAttribute("lang") || "pt").toLowerCase();
    const isEn = lang.startsWith("en");
    const hudTextEl = hudEl.querySelector(".map-radar-hud-text");
    if (hudTextEl) {
      if (isEn) {
        hudTextEl.textContent = `LIVE RADAR // ${count} ACTIVE ${count === 1 ? "USER" : "USERS"}`;
      } else {
        hudTextEl.textContent = `RADAR ATIVO // ${count} ${count === 1 ? "USUÁRIO ONLINE" : "USUÁRIOS ONLINE"}`;
      }
    }

    const spyToggleBtn = leftControlsEl.querySelector(".map-radar-spy-toggle-btn");
    if (spyToggleBtn) {
      spyToggleBtn.textContent = isEn ? "⌖ 10 STATES" : "⌖ 10 ESTADOS";
      spyToggleBtn.classList.toggle("active", showSpyTargets);
    }

    // Contador dedicado de visitantes únicos (por IP) na H0M3
    const counterNum = document.getElementById("unique-visitors-number");
    const counterLabel = document.getElementById("unique-visitors-label");
    if (counterNum) {
      counterNum.textContent = String(uniqueTotal).padStart(6, "0");
    }
    if (counterLabel) {
      counterLabel.textContent = isEn ? "PEOPLE HAVE ENTERED" : "PESSOAS JÁ ENTRARAM";
    }

    radarContainer.querySelectorAll(".map-user-node").forEach((n) => n.remove());

    const sortedUsers = [...activeUsersList].sort((a, b) => (b.is_self ? 1 : 0) - (a.is_self ? 1 : 0));
    const bucketCounts = {};

    sortedUsers.forEach((u, idx) => {
      const mx = Number(u.mx);
      const my = Number(u.my);
      if (isNaN(mx) || isNaN(my)) return;

      const baseImgPt = clampInsideBrazilGreenBorder(mx, my, 8);
      const bucketKey = `${Math.round(baseImgPt.imgX / 5)}_${Math.round(baseImgPt.imgY / 5)}`;
      const rankInCity = bucketCounts[bucketKey] || 0;
      bucketCounts[bucketKey] = rankInCity + 1;

      let offsetPxX = 0;
      let offsetPxY = 0;
      if (rankInCity > 0) {
        const angle = ((rankInCity - 1) * 137.5 * Math.PI) / 180;
        const radiusPx = 5 + Math.floor((rankInCity - 1) / 5) * 4;
        offsetPxX = Math.cos(angle) * radiusPx;
        offsetPxY = Math.sin(angle) * radiusPx;
      }

      const clampedImgPt = clampInsideBrazilGreenBorder(
        baseImgPt.imgX + offsetPxX,
        baseImgPt.imgY + offsetPxY,
        8
      );
      const screenPos = imagePixelToScreen(clampedImgPt.imgX, clampedImgPt.imgY);

      const node = document.createElement("div");
      node.className = "map-user-node" + (u.is_self ? " is-self" : "");
      node.style.left = `${screenPos.x.toFixed(1)}px`;
      node.style.top = `${screenPos.y.toFixed(1)}px`;
      node.setAttribute("tabindex", "0");

      const cityLabel = u.city ? String(u.city).toUpperCase() : "BRASIL";
      const regLabel = u.region ? String(u.region).toUpperCase() : "BR";
      const selfTag = u.is_self ? (isEn ? " • YOU" : " • VOCÊ") : "";
      const statusTag = isEn ? "ONLINE" : "ATIVO AGORA";
      const tooltipText = `${cityLabel}, ${regLabel}${selfTag} • ${statusTag}`;
      node.setAttribute("aria-label", tooltipText);

      const pulse = document.createElement("span");
      pulse.className = "map-user-pulse";
      pulse.style.animationDelay = `${(idx * 0.37) % 2.2}s`;

      const core = document.createElement("span");
      core.className = "map-user-core";

      const tooltip = document.createElement("span");
      tooltip.className = "map-user-tooltip";
      tooltip.textContent = tooltipText;

      node.appendChild(pulse);
      node.appendChild(core);
      node.appendChild(tooltip);
      radarContainer.appendChild(node);
    });

    updateMainStatesPositions();
  }

  let clientPxPromise = null;

  async function sendPresenceHeartbeat() {
    const uid = getOrCreateUid();

    if (!clientPxPromise) {
      clientPxPromise = resolveClientAnonymousPixel();
    }
    const px = await clientPxPromise;

    const payload = { uid };
    if (px && typeof px.mx === "number" && typeof px.my === "number") {
      payload.mx = px.mx;
      payload.my = px.my;
      if (px.city) payload.city = px.city;
      if (px.region) payload.region = px.region;
    }

    try {
      const res = await fetch("api/presence.php?t=" + Date.now(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) return;
      const data = await res.json();
      if (data && data.ok && Array.isArray(data.users)) {
        activeUsersList = data.users;
        if (typeof data.unique_visitors === "number") {
          // Só aceita valores maiores ou iguais: o contador nunca regride na tela
          totalUniqueVisitors = Math.max(totalUniqueVisitors, data.unique_visitors);
        }
        renderBrazilMapRadar();
      }
    } catch (e) {}
  }

  sendPresenceHeartbeat();
  setInterval(sendPresenceHeartbeat, 25000);

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      sendPresenceHeartbeat();
    }
  });

  if (radarContainer) {
    window.addEventListener("resize", () => {
      requestAnimationFrame(() => {
        renderBrazilMapRadar();
        if (openStateUf) updateStateWinVectorLine();
      });
    });
    window.addEventListener("emorphosis:langchange", () => {
      renderBrazilMapRadar();
      buildMainMapStatesOverlay();
      if (openStateUf) renderStateOsWindow();
    });
    const bgImg = document.querySelector(".home-bg-img");
    if (bgImg) {
      bgImg.addEventListener("load", renderBrazilMapRadar);
    }
  }

  // ==========================================================================
  // 4. Canvas fallback (#bg-matrix-waves)
  // ==========================================================================
  const canvas = document.getElementById("bg-matrix-waves");
  if (!canvas) return;

  const ctx = canvas.getContext("2d", { alpha: false });
  let width = 0;
  let height = 0;
  let animId = null;
  let t = 0;

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function render() {
    ctx.fillStyle = "#010401";
    ctx.fillRect(0, 0, width, height);

    const spacing = 10;
    const cols = Math.ceil(width / spacing);
    const rows = Math.ceil(height / spacing);

    for (let r = 0; r < rows; r++) {
      const y = r * spacing;
      const ny = y * 0.0045;

      for (let c = 0; c < cols; c++) {
        const x = c * spacing;
        const nx = x * 0.0038;

        const wave =
          Math.sin(nx * 2.2 + Math.cos(ny * 2.1 + t * 0.6) * 2.4 + t * 0.4) +
          Math.cos(ny * 2.6 - Math.sin(nx * 1.7 - t * 0.35) * 1.9);

        const ridge = Math.abs(((wave * 2.3) % 1 + 1) % 1 - 0.5) * 2;
        const intensity = Math.pow(ridge, 3.2);

        if (intensity > 0.08) {
          const green = Math.min(255, Math.floor(45 + intensity * 210));
          const red = Math.floor(intensity * 35);
          const radius = 1.1 + intensity * 2.1;

          ctx.fillStyle = `rgb(${red}, ${green}, ${Math.floor(intensity * 48)})`;
          ctx.beginPath();
          ctx.arc(x, y, radius, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }

    t += 0.008;
    animId = requestAnimationFrame(render);
  }

  window.addEventListener("resize", resize);
  resize();

  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (prefersReduced) {
    render();
    cancelAnimationFrame(animId);
  } else {
    render();
  }
})();
