/** UCSD favorites explorer — thin client over /api/* */

let METHODS = [];
let META = {};
let TIMER = null;
let LAST_RESULTS = [];
let GENRE_TIMER = null;
let GENRE_STATE = {
  require: [],
  include: [],
  exclude: [],
};
/** Active prevalence gates (intersected). Default SF on first load. */
let GATE_STATE = ["sf"];
let TASTE = {
  literary: [],
  literary_sf_extras: [],
  non_literary: [],
  stats: {},
};

const $ = (id) => document.getElementById(id);

function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function num(id, fallback) {
  const raw = $(id)?.value;
  if (raw === undefined || raw === null || String(raw).trim() === "") {
    return fallback;
  }
  const v = Number(raw);
  return Number.isFinite(v) ? v : fallback;
}

function intNum(id, fallback, { min = null, max = null } = {}) {
  let v = Math.trunc(num(id, fallback));
  if (min != null && v < min) v = min;
  if (max != null && v > max) v = max;
  return v;
}

function checked(id) {
  return Boolean($(id)?.checked);
}

function pct(x) {
  return x == null || !Number.isFinite(x) ? "—" : `${(100 * x).toFixed(1)}%`;
}

function syncTasteLabels() {
  const on = checked("taste-enabled");
  $("taste-controls").hidden = !on;
  $("taste-min-lit-val").textContent = `${num("taste-min-lit", 0)}%`;
  $("taste-max-com-val").textContent = `${num("taste-max-com", 100)}%`;
  const net = num("taste-min-net", -100);
  $("taste-min-net-val").textContent = `${net > 0 ? "+" : ""}${net}%`;
  if ($("taste-min-lit-hits-val")) {
    $("taste-min-lit-hits-val").textContent = String(num("taste-min-lit-hits", 0));
  }
  syncCuratorStrictness();
}

function syncCuratorStrictness() {
  const method = $("method")?.value || "";
  const isCurator = method.startsWith("curator_");
  const isDeep = method.startsWith("curator_deep_");
  const isGeom = method === "curator_deep_pct_geom";
  const isPct = method.includes("_pct_");
  const wrap = $("curator-strictness-wrap");
  if (wrap) wrap.hidden = !isCurator;
  const normieWrap = $("normie-strictness-wrap");
  if (normieWrap) normieWrap.hidden = !isDeep;
  const covWrap = $("coverage-wrap");
  if (covWrap) covWrap.hidden = !isPct;
  const geomWrap = $("geom-score-wrap");
  if (geomWrap) geomWrap.hidden = !isGeom;
  const cs = intNum("curator-strictness", 0, { min: 0, max: 100 });
  const nd = intNum("normie-depth", 0, { min: 0, max: 100 });
  const np = intNum("normie-purity", 0, { min: 0, max: 100 });
  const cov = intNum("coverage-weight", 100, { min: 0, max: 100 });
  const el = $("curator-strictness-val");
  if (el) el.textContent = cs === 0 ? "0 (off)" : String(cs);
  const ndEl = $("normie-depth-val");
  if (ndEl) ndEl.textContent = nd === 0 ? "0 (off)" : String(nd);
  const npEl = $("normie-purity-val");
  if (npEl) npEl.textContent = np === 0 ? "0 (off)" : String(np);
  const covEl = $("coverage-val");
  if (covEl) covEl.textContent = String(cov);
  const covRead = $("coverage-readout");
  if (covRead) {
    if (cov >= 100) covRead.textContent = " · full cohort";
    else if (cov <= 0) covRead.textContent = " · among raters only";
    else covRead.textContent = ` · ${cov}% cohort / ${100 - cov}% raters`;
  }
  const readout = $("normie-deep-readout");
  if (readout && isDeep) {
    if (nd <= 0) {
      readout.textContent = " · no min depth";
    } else {
      const t = nd / 100;
      const minDeep = Math.round(Math.exp(Math.log(2) + t * (Math.log(20) - Math.log(2))));
      readout.textContent = ` · ≥${minDeep} non-normie poll ★≥4`;
    }
  } else if (readout) {
    readout.textContent = "";
  }
  const pureOut = $("normie-purity-readout");
  if (pureOut && isDeep) {
    if (np <= 0) {
      pureOut.textContent = " · no share floor";
    } else {
      const share = 0.35 + (np / 100) * 0.45;
      const comCap = 0.15 - (np / 100) * 0.07;
      pureOut.textContent = ` · deep_share ≥ ${share.toFixed(2)} · com ≤ ${comCap.toFixed(2)}`;
    }
  } else if (pureOut) {
    pureOut.textContent = "";
  }
  // geom-ratio / pct-power stored as tenths on the range input
  const gTenths = intNum("geom-ratio", 20, { min: 10, max: 50 });
  const pTenths = intNum("pct-power", 25, { min: 10, max: 60 });
  const g = gTenths / 10;
  const xp = pTenths / 10;
  const gVal = $("geom-ratio-val");
  if (gVal) gVal.textContent = g.toFixed(1);
  const pVal = $("pct-power-val");
  if (pVal) pVal.textContent = xp.toFixed(1);
  const gRead = $("geom-ratio-readout");
  if (gRead) {
    const w5 = (g * g).toFixed(1);
    const w4 = g.toFixed(1);
    gRead.textContent = ` · 5:4:3 = ${w5}:${w4}:1`;
  }
  const mode = $("curator-strictness-mode")?.value || "deweight";
  const hint = $("curator-strictness-hint");
  if (hint) {
    hint.textContent =
      mode === "gate"
        ? "0 = off (everyone). 100 ≈ top 100 curators by weight. Deep methods still soft-penalize commercial anti-signal share. Log-linear shrink in between."
        : "0 = off (everyone, full curator weights). 100 ≈ top 100 by weight (log-linear shrink). Mild within-elite deweight as you raise it.";
  }
}

function renderTasteChips() {
  const render = (elId, list, side) => {
    $(elId).innerHTML = (list || [])
      .map(
        (s) =>
          `<span class="chip" data-side="${side}">${escapeHtml(s.match || s)}</span>`
      )
      .join("");
  };
  render("taste-lit-chips", TASTE.literary, "literary");
  render("taste-sf-chips", TASTE.literary_sf_extras, "literary_sf");
  render(
    "taste-com-chips",
    TASTE.non_literary || TASTE.commercial,
    "non_literary"
  );
  const st = TASTE.stats || {};
  const bits = [];
  if (st.n_users_with_taste != null) {
    bits.push(`${st.n_users_with_taste.toLocaleString()} users with signal hits`);
  }
  if (st.n_lit_lean != null) {
    bits.push(`${st.n_lit_lean.toLocaleString()} lit-lean (SF extras off)`);
  }
  if (TASTE.notes) bits.push(TASTE.notes);
  $("taste-list-note").textContent = bits.join(" · ");
}

const PREFS_KEY = "ucsd_explorer_prefs_v2";

const PERSIST_IDS = [
  "method",
  "min-votes",
  "max-n",
  "bayesian-m",
  "curator-strictness",
  "curator-strictness-mode",
  "normie-depth",
  "normie-purity",
  "personal-power",
  "comedy-cap",
  "geom-ratio",
  "pct-power",
  "coverage-weight",
  "limit",
  "year-min",
  "year-max",
  "q",
  "fiction-only",
  "exclude-derivatives",
  "exclude-comics",
  "exclude-picture-books",
  "collapse-duplicates",
  "exclude-collections",
  "apply-format-weight",
  "taste-enabled",
  "taste-include-sf",
  "taste-lit-fours",
  "taste-min-lit",
  "taste-max-com",
  "taste-min-net",
  "taste-min-lit-hits",
  "taste-min-hits",
];

function savePrefs() {
  const prefs = {};
  for (const id of PERSIST_IDS) {
    const el = $(id);
    if (!el) continue;
    if (el.type === "checkbox") {
      prefs[id] = el.checked;
    } else {
      const v = el.value;
      // Don't persist blank year fields — they would override intentional empties awkwardly
      if ((id === "year-min" || id === "year-max") && !String(v || "").trim()) {
        continue;
      }
      prefs[id] = v;
    }
  }
  prefs.genres = {
    require: [...GENRE_STATE.require],
    include: [...GENRE_STATE.include],
    exclude: [...GENRE_STATE.exclude],
  };
  prefs.genre_gates = [...GATE_STATE];
  try {
    localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
  } catch (_) {
    /* ignore quota / private mode */
  }
}

function loadPrefs() {
  let prefs;
  try {
    prefs = JSON.parse(localStorage.getItem(PREFS_KEY) || "null");
  } catch (_) {
    return;
  }
  if (!prefs || typeof prefs !== "object") return;
  for (const id of PERSIST_IDS) {
    if (!(id in prefs)) continue;
    const el = $(id);
    if (!el) continue;
    if (el.type === "checkbox") {
      el.checked = Boolean(prefs[id]);
    } else if (prefs[id] != null && String(prefs[id]).trim() !== "") {
      el.value = String(prefs[id]);
    }
  }
  if (prefs.genres && typeof prefs.genres === "object") {
    GENRE_STATE.require = [...(prefs.genres.require || [])];
    GENRE_STATE.include = [...(prefs.genres.include || [])];
    GENRE_STATE.exclude = [...(prefs.genres.exclude || [])];
  } else if (prefs["sf-only"] === false) {
    GENRE_STATE = { require: [], include: [], exclude: [] };
  }
  if (Array.isArray(prefs.genre_gates)) {
    GATE_STATE = [...prefs.genre_gates];
  } else {
    // Migrate old SF include-tag preset → prevalence gate
    const sfPreset = META.sf_preset_include || [];
    const looksSf =
      GENRE_STATE.include.length > 0 &&
      GENRE_STATE.include.every((t) => sfPreset.includes(t)) &&
      !GENRE_STATE.require.length &&
      !GENRE_STATE.exclude.length;
    if (looksSf) {
      GATE_STATE = ["sf"];
      GENRE_STATE.include = [];
    } else if (
      !GENRE_STATE.require.length &&
      !GENRE_STATE.include.length &&
      !GENRE_STATE.exclude.length
    ) {
      GATE_STATE = ["sf"];
    } else {
      GATE_STATE = [];
    }
  }
}

function applySfPreset() {
  GATE_STATE = ["sf"];
  // Clear legacy SF include tags — prevalence gate owns SF now
  const sfPreset = new Set(META.sf_preset_include || []);
  GENRE_STATE.include = GENRE_STATE.include.filter((t) => !sfPreset.has(t));
  renderGenreChips();
  renderGateToggles();
}

function clearGenres() {
  GATE_STATE = [];
  GENRE_STATE = { require: [], include: [], exclude: [] };
  renderGenreChips();
  renderGateToggles();
}

function toggleGate(gateId) {
  const i = GATE_STATE.indexOf(gateId);
  if (i >= 0) GATE_STATE.splice(i, 1);
  else GATE_STATE.push(gateId);
  renderGateToggles();
  savePrefs();
  scheduleRank();
}

function renderGateToggles() {
  document.querySelectorAll(".gate-toggle[data-gate]").forEach((btn) => {
    const g = btn.getAttribute("data-gate");
    btn.classList.toggle("active", GATE_STATE.includes(g));
  });
  const labels = {
    sf: "SF",
    fantasy: "fantasy",
    coming_of_age: "coming-of-age",
    lgbtq: "LGBTQ",
    western: "western",
  };
  const sum = $("gate-summary");
  if (!sum) return;
  if (!GATE_STATE.length) {
    sum.textContent = "No prevalence gate (tag filters only / all genres).";
    return;
  }
  const names = GATE_STATE.map((g) => labels[g] || g);
  sum.textContent =
    names.length === 1
      ? `Gate: ${names[0]} (prevalence)`
      : `Gates ∩: ${names.join(" ∩ ")} (must pass all)`;
}

function genreAddBucket() {
  const el = document.querySelector('input[name="genre-add-bucket"]:checked');
  return el?.value || "include";
}

function addGenreTag(shelf) {
  const g = String(shelf || "")
    .toLowerCase()
    .trim()
    .replace(/\s+/g, "-");
  if (!g) return;
  const bucket = genreAddBucket();
  for (const b of ["require", "include", "exclude"]) {
    GENRE_STATE[b] = GENRE_STATE[b].filter((x) => x !== g);
  }
  GENRE_STATE[bucket].push(g);
  renderGenreChips();
  savePrefs();
  scheduleRank();
}

function removeGenreTag(bucket, shelf) {
  GENRE_STATE[bucket] = GENRE_STATE[bucket].filter((x) => x !== shelf);
  renderGenreChips();
  savePrefs();
  scheduleRank();
}

function renderGenreChips() {
  for (const bucket of ["require", "include", "exclude"]) {
    const el = $(`genre-${bucket}-chips`);
    if (!el) continue;
    const tags = GENRE_STATE[bucket] || [];
    el.innerHTML = tags
      .map(
        (g) =>
          `<button type="button" class="chip genre-chip" data-bucket="${bucket}" data-shelf="${escapeHtml(
            g
          )}" title="Remove">${escapeHtml(g)} ×</button>`
      )
      .join("");
  }
  const bits = [];
  if (GATE_STATE.length) {
    bits.push(
      GATE_STATE.length === 1
        ? `${GATE_STATE[0]} gate`
        : `gates ∩ ${GATE_STATE.join(" ∩ ")}`
    );
  }
  if (GENRE_STATE.require.length) bits.push(`require ${GENRE_STATE.require.join(", ")}`);
  if (GENRE_STATE.include.length) {
    bits.push(`any of ${GENRE_STATE.include.join(", ")}`);
  }
  if (GENRE_STATE.exclude.length) bits.push(`exclude ${GENRE_STATE.exclude.join(", ")}`);
  const sum = $("genre-summary");
  if (sum) {
    sum.textContent = bits.length
      ? bits.join(" · ")
      : "No genre filter (all genres).";
  }
  renderGateToggles();
}

async function suggestGenres(q) {
  const box = $("genre-suggest");
  if (!box) return;
  if (!q || q.length < 1) {
    box.hidden = true;
    box.innerHTML = "";
    return;
  }
  try {
    const res = await fetch(`/api/genres?q=${encodeURIComponent(q)}&limit=25`);
    const data = await res.json();
    const rows = data.genres || [];
    if (!rows.length) {
      box.hidden = true;
      box.innerHTML = "";
      return;
    }
    box.hidden = false;
    box.innerHTML = rows
      .map(
        (r) =>
          `<button type="button" data-shelf="${escapeHtml(r.shelf)}">${escapeHtml(
            r.shelf
          )} <span class="mono">${Number(r.n_works).toLocaleString()} works</span></button>`
      )
      .join("");
  } catch (_) {
    box.hidden = true;
  }
}

function getParams() {
  const params = {
    method: $("method").value,
    min_votes: intNum("min-votes", 50, { min: 1 }),
    max_n: intNum("max-n", 0, { min: 0 }),
    bayesian_m: num("bayesian-m", 50),
    curator_strictness: intNum("curator-strictness", 0, { min: 0, max: 100 }),
    curator_strictness_mode: $("curator-strictness-mode")?.value || "deweight",
    normie_depth: intNum("normie-depth", 0, { min: 0, max: 100 }),
    normie_purity: intNum("normie-purity", 0, { min: 0, max: 100 }),
    personal_power: $("personal-power")?.checked ? "1" : "0",
    comedy_cap: $("comedy-cap")?.checked ? "1" : "0",
    geom_ratio: intNum("geom-ratio", 20, { min: 10, max: 50 }) / 10,
    pct_power: intNum("pct-power", 25, { min: 10, max: 60 }) / 10,
    coverage_weight: intNum("coverage-weight", 100, { min: 0, max: 100 }) / 100,
    limit: intNum("limit", 200, { min: 1 }),
    q: $("q").value.trim(),
    genre_require: [...GENRE_STATE.require],
    genre_include: [...GENRE_STATE.include],
    genre_exclude: [...GENRE_STATE.exclude],
    genre_gates: [...GATE_STATE],
    fiction_only: checked("fiction-only"),
    exclude_derivatives: checked("exclude-derivatives"),
    exclude_comics: checked("exclude-comics"),
    exclude_picture_books: checked("exclude-picture-books"),
    collapse_duplicates: checked("collapse-duplicates"),
    exclude_collections: checked("exclude-collections"),
    apply_format_weight: checked("apply-format-weight"),
  };
  const ymin = $("year-min")?.value?.trim();
  const ymax = $("year-max")?.value?.trim();
  if (ymin) params.year_min = Math.trunc(Number(ymin));
  if (ymax) params.year_max = Math.trunc(Number(ymax));
  if (checked("taste-enabled")) {
    params.taste_enabled = true;
    params.taste_min_lit = num("taste-min-lit", 0) / 100;
    params.taste_max_nonlit = num("taste-max-com", 100) / 100;
    params.taste_min_net = num("taste-min-net", -100) / 100;
    params.taste_min_hits = intNum("taste-min-hits", 2, { min: 1 });
    params.taste_min_lit_hits = intNum("taste-min-lit-hits", 0, { min: 0 });
    params.taste_include_sf_extras = checked("taste-include-sf");
    params.taste_literary_fives_only = !checked("taste-lit-fours");
  }
  return params;
}

function scheduleRank() {
  if (TIMER) clearTimeout(TIMER);
  TIMER = setTimeout(() => {
    TIMER = null;
    rerank();
  }, 180);
}

async function rerank() {
  syncTasteLabels();
  const params = getParams();
  $("filter-summary").textContent = "Computing…";
  const t0 = performance.now();
  const res = await fetch("/api/rank", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok) {
    $("filter-summary").textContent = data.error || "Rank failed";
    return;
  }
  const ms = performance.now() - t0;
  const g = data.genres || {};
  const gBits = [];
  if ((g.require || []).length) gBits.push(`require:${g.require.join("+")}`);
  if ((g.include || []).length) gBits.push(`any:${g.include.slice(0, 4).join("|")}${(g.include.length > 4 ? "…" : "")}`);
  if ((g.exclude || []).length) gBits.push(`ex:${g.exclude.join("|")}`);
  const scope = gBits.length ? gBits.join(" · ") : "all genres";
  let summary =
    `${data.n_results} books · ${scope} · min n≥${data.min_votes ?? params.min_votes}` +
    `${data.max_n ? ` · max n≤${data.max_n}` : ""} · ${(ms / 1000).toFixed(2)}s`;
  const cat = data.catalog || {};
  const catBits = [];
  if (cat.fiction_only) catBits.push("fiction");
  if (cat.exclude_derivatives) catBits.push("no derivatives");
  if (cat.exclude_comics) catBits.push("no comics");
  if (cat.exclude_picture_books) catBits.push("no picture books");
  if (cat.collapse_duplicates) catBits.push("deduped");
  if (cat.exclude_collections) catBits.push("no collections");
  else if (cat.apply_format_weight) catBits.push("collections deweighted");
  if (catBits.length) summary += ` · ${catBits.join(" · ")}`;
  if (data.year_min || data.year_max) {
    summary += ` · years ${data.year_min || "…"}–${data.year_max || "…"}`;
  }
  if (data.curator_strictness != null && String(params.method || "").startsWith("curator_")) {
    const mode = data.curator_strictness_mode || "deweight";
    summary += ` · curator ${mode} ${Math.round(data.curator_strictness)}`;
    if (mode === "deweight" && data.curator_deweight_exp != null) {
      summary += ` (α=${Number(data.curator_deweight_exp).toFixed(2)})`;
    }
    if (data.normie_depth != null && String(params.method || "").startsWith("curator_deep_")) {
      summary += ` · depth ${Math.round(data.normie_depth)} · purity ${Math.round(data.normie_purity || 0)}`;
      if (data.personal_power) summary += " · personal★5";
      if (data.comedy_cap) summary += " · comedy-cap";
    }
    if (data.geom_ratio != null && params.method === "curator_deep_pct_geom") {
      summary += ` · geom q=${Number(data.geom_ratio).toFixed(1)} · pct^${Number(data.pct_power).toFixed(1)}`;
    }
    if (data.coverage_weight != null && String(params.method || "").includes("_pct_")) {
      summary += ` · coverage ${Math.round(100 * Number(data.coverage_weight))}`;
    }
  }
  if (data.taste_enabled) {
    summary += ` · ${Number(data.n_eligible_users || 0).toLocaleString()} taste-eligible users`;
    const sf = data.taste?.include_sf_extras ? "SF extras on" : "poll literary only";
    const litStars = data.taste?.literary_include_fours !== false ? "lit ★≥4" : "lit ★=5";
    $("taste-summary").textContent =
      `Using ${Number(data.n_eligible_users || 0).toLocaleString()} users · ${sf} · ${litStars} · ` +
      `min lit ${(100 * (data.taste?.min_lit || 0)).toFixed(0)}% · ` +
      `max non-lit ${(100 * (data.taste?.max_com || 0)).toFixed(0)}% · ` +
      `min net ${(100 * (data.taste?.min_net || 0)).toFixed(0)}% · ` +
      `≥${data.taste?.min_lit_hits || 0} lit books · ` +
      `≥${data.taste?.min_hits || 1} total hits (non-lit ★=5).`;
  } else if ($("taste-summary")) {
    $("taste-summary").textContent = META.taste_available
      ? "Taste filter off — rankings use all SF raters."
      : "Taste tables not built yet (run python -m ucsd_explorer.taste).";
  }
  $("filter-summary").textContent = summary;

  $("stats-row").innerHTML = [
    ["Listed", String(data.n_results)],
    ["Method", params.method],
    ["Global P(5★)", pct(data.globals?.global_p5)],
    ["Server", `${(ms / 1000).toFixed(2)}s`],
  ]
    .map(
      ([l, v]) =>
        `<div class="stat"><div class="v">${escapeHtml(v)}</div><div class="l">${escapeHtml(l)}</div></div>`
    )
    .join("");

  LAST_RESULTS = Array.isArray(data.results) ? data.results : [];
  const copyBtn = $("copy-results");
  if (copyBtn) copyBtn.disabled = LAST_RESULTS.length === 0;

  const tbody = $("results").querySelector("tbody");
  tbody.innerHTML = data.results
    .map((r) => {
      return `<tr data-id="${escapeHtml(r.book_id)}">
        <td class="mono">${r.rank}</td>
        <td class="title-cell">${escapeHtml(r.title)}</td>
        <td>${escapeHtml(r.author)}</td>
        <td class="mono">${r.n.toLocaleString()}</td>
        <td class="mono">${r.n5.toLocaleString()}</td>
        <td class="mono">${pct(r.p5)}</td>
        <td class="mono">${r.std != null ? r.std.toFixed(2) : "—"}</td>
        <td class="mono">${r.polarization != null ? r.polarization.toFixed(3) : "—"}</td>
        <td class="mono">${Number.isFinite(r.score) ? r.score.toFixed(4) : "—"}</td>
      </tr>`;
    })
    .join("");
}

function closeDrawer() {
  $("drawer").hidden = true;
  $("drawer-body").innerHTML = "";
}

async function copyResultsList() {
  const btn = $("copy-results");
  const lines = LAST_RESULTS.map((r) => {
    const title = String(r.title || "").trim();
    const author = String(r.author || "").trim();
    if (!title) return "";
    return author ? `${title} — ${author}` : title;
  }).filter(Boolean);
  if (!lines.length) return;
  const text = lines.join("\n");
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }
  if (btn) {
    const prev = btn.textContent;
    btn.textContent = `Copied ${lines.length}`;
    btn.classList.add("copied");
    setTimeout(() => {
      btn.textContent = prev || "Copy list";
      btn.classList.remove("copied");
    }, 1400);
  }
}

async function openBook(bookId, simMethod) {
  const method = simMethod || "cosine";
  const params = {
    ...getParams(),
    limit: 25,
    sim_method: method,
    sim_limit: 20,
  };
  const res = await fetch(`/api/book/${encodeURIComponent(bookId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok || data.error) {
    $("drawer-body").innerHTML = `<p>${escapeHtml(data.error || "Error")}</p>`;
    $("drawer").hidden = false;
    return;
  }
  const b = data.book;
  const renderHist = (stars, n, label, extraMeta) => {
    const rows = [5, 4, 3, 2, 1]
      .map((s) => {
        const c = (stars && stars[s]) || 0;
        const w = n ? Math.round((100 * c) / n) : 0;
        return `<div class="star-row"><span>${s}★</span>
          <div class="bar"><i style="width:${w}%"></i></div>
          <span class="mono">${Number(c).toLocaleString()} (${w}%)</span></div>`;
      })
      .join("");
    const meta = extraMeta
      ? `<p class="meta">${extraMeta}</p>`
      : `<p class="meta">n=${Number(n || 0).toLocaleString()}</p>`;
    return `<h3 class="drawer-h">${escapeHtml(label)}</h3>
      ${meta}
      <div class="star-dist">${rows}</div>`;
  };

  const overallHist = renderHist(b.stars || {}, b.n, "All raters (this edition)");
  let relevantHist = "";
  if (data.relevant_hist && !data.relevant_hist.error) {
    const rh = data.relevant_hist;
    if (!rh.n && !rh.n_raw) {
      relevantHist = `<h3 class="drawer-h">Ranking cohort</h3>
        <p class="hint">No ratings from the current ranking cohort on this edition.</p>`;
    } else {
      const bits = [
        `n_raw=${Number(rh.n_raw || 0).toLocaleString()}`,
        rh.weighted ? `weight Σ=${Number(rh.w_sum || rh.n || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })}` : null,
        rh.mean != null ? `mean ${Number(rh.mean).toFixed(2)}` : null,
        rh.p5 != null ? `P(5★) ${pct(rh.p5)}` : null,
        rh.pct_mean != null ? `shelf pct̄ ${pct(rh.pct_mean)}` : null,
        rh.pct_median != null ? `shelf pct med ${pct(rh.pct_median)}` : null,
      ].filter(Boolean);
      const label = rh.label
        ? `Ranking cohort · ${rh.label}`
        : "Ranking cohort";
      relevantHist = renderHist(rh.stars || {}, rh.n || rh.n_raw, label, bits.join(" · "));
    }
  } else if (data.filtered_hist && !data.filtered_hist.error) {
    const fh = data.filtered_hist;
    if (!fh.n) {
      relevantHist = `<h3 class="drawer-h">Taste-filtered raters</h3>
        <p class="hint">No taste-eligible users rated this edition under the current sliders.</p>`;
    } else {
      relevantHist = renderHist(
        fh.stars || {},
        fh.n,
        `Taste-filtered raters · mean ${fh.mean?.toFixed?.(2) ?? "?"} · P(5★) ${pct(fh.p5)}`
      );
    }
  } else if (data.hist_note) {
    relevantHist = `<p class="hint">${escapeHtml(data.hist_note)}</p>`;
  }
  let editionNote = "";
  if (data.better_edition) {
    const be = data.better_edition;
    editionNote = `<p class="hint">Heads-up: another edition of this title has far more ratings
      (<a href="#" id="better-edition" data-id="${escapeHtml(be.book_id)}">${escapeHtml(be.title)}</a>
      · ${escapeHtml(be.author)} · n=${Number(be.n).toLocaleString()}).</p>`;
  }
  let catalogNote = "";
  if (data.catalog && data.catalog.flags) {
    const c = data.catalog;
    catalogNote = `<p class="hint">Catalog flags: <span class="mono">${escapeHtml(c.flags)}</span>`;
    if (c.format_weight != null && c.format_weight < 1) {
      catalogNote += ` · format weight ${Number(c.format_weight).toFixed(2)}`;
    }
    catalogNote += `</p>`;
    if (c.is_duplicate && c.canonical_book_id) {
      catalogNote += `<p class="hint">Near-duplicate of
        <a href="#" id="canonical-edition" data-id="${escapeHtml(c.canonical_book_id)}">${escapeHtml(
          c.canonical_title || "canonical edition"
        )}</a>.</p>`;
    }
  }

  const supporters = (data.supporters || [])
    .map((s) => {
      const taste =
        s.lit_share != null
          ? ` · lit ${Math.round(100 * s.lit_share)}%` +
            (s.lit_weight != null ? ` · w ${s.lit_weight.toFixed(2)}` : "")
          : "";
      return `<div class="supporter">
        <div><strong>${escapeHtml(s.user_name)}</strong>
          · picky ${s.picky_weight.toFixed(2)}</div>
        <div class="mono" style="color:var(--muted);font-size:0.78rem">
          ${s.books_read} ratings · ${(100 * s.five_rate).toFixed(0)}% fives${taste}
        </div>
      </div>`;
    })
    .join("");

  const simMethods = data.sim_methods || META.sim_methods || [];
  const sim = data.similar || {};
  const simOpts = simMethods
    .map(
      (m) =>
        `<option value="${escapeHtml(m.id)}" ${m.id === (sim.method || method) ? "selected" : ""}>${escapeHtml(m.name)}</option>`
    )
    .join("");
  const simRows = (sim.results || [])
    .map(
      (r) => `<div class="sim-row" data-id="${escapeHtml(r.book_id)}">
        <div class="sim-title">${escapeHtml(r.title)}</div>
        <div class="mono sim-meta">${escapeHtml(r.author)} · ${r.both_fans} curator 5★ · ${r.score.toFixed(4)}</div>
      </div>`
    )
    .join("");

  $("drawer-body").innerHTML = `
    <h2>${escapeHtml(b.title)}</h2>
    <p class="sub">${escapeHtml(b.author)}
      ${b.book_url ? ` · <a href="${escapeHtml(b.book_url)}" target="_blank" rel="noopener">Goodreads</a>` : ""}
    </p>
    <p class="meta">
      n=${b.n.toLocaleString()} · mean ${b.mean?.toFixed?.(2) ?? "?"} ·
      σ ${b.std?.toFixed?.(2) ?? "?"} ·
      P(5★) ${pct(b.p5)} (Bayes ${pct(b.bayesian_p5)}) ·
      polar ${b.polarization?.toFixed?.(3) ?? "—"}
    </p>
    ${editionNote}
    ${catalogNote}
    ${relevantHist}
    ${overallHist}

    <h3 class="drawer-h">Similar books</h3>
    <label class="field">
      <span>Similarity</span>
      <select id="sim-method">${simOpts}</select>
    </label>
    <p class="hint">${escapeHtml(
      sim.curator_cohort
        ? `Curator-weighted · ${sim.curator_cohort}${sim.n_curators ? ` · ${Number(sim.n_curators).toLocaleString()} active` : ""}`
        : (simMethods.find((m) => m.id === (sim.method || method)) || {}).blurb || ""
    )}</p>
    <div class="sim-list" id="sim-list">${
      sim.note
        ? `<p class='hint'>${escapeHtml(sim.note)}</p>`
        : simRows || "<p class='hint'>No curator co-favorites found.</p>"
    }</div>

    <h3 class="drawer-h">5★ supporters (by literary weight)</h3>
    ${supporters || "<p class='hint'>No five-star events.</p>"}
  `;
  $("drawer").hidden = false;

  const better = $("better-edition");
  if (better) {
    better.addEventListener("click", (e) => {
      e.preventDefault();
      openBook(better.getAttribute("data-id"), simMethod);
    });
  }
  const canon = $("canonical-edition");
  if (canon) {
    canon.addEventListener("click", (e) => {
      e.preventDefault();
      openBook(canon.getAttribute("data-id"), simMethod);
    });
  }

  const simSel = $("sim-method");
  if (simSel) {
    simSel.addEventListener("change", () => openBook(bookId, simSel.value));
  }
  const simList = $("sim-list");
  if (simList) {
    simList.addEventListener("click", (e) => {
      const row = e.target.closest(".sim-row[data-id]");
      if (row) openBook(row.getAttribute("data-id"), simSel?.value || "cosine");
    });
  }
}

function wire() {
  for (const id of PERSIST_IDS) {
    const el = $(id);
    if (!el) continue;
    el.addEventListener("input", () => {
      if (id.startsWith("taste-")) syncTasteLabels();
      savePrefs();
      scheduleRank();
    });
    el.addEventListener("change", () => {
      if (id.startsWith("taste-")) syncTasteLabels();
      savePrefs();
      scheduleRank();
    });
  }
  $("rerank").addEventListener("click", rerank);
  const copyBtn = $("copy-results");
  if (copyBtn) copyBtn.addEventListener("click", copyResultsList);
  $("drawer-close").addEventListener("click", closeDrawer);
  $("drawer").addEventListener("click", (e) => {
    if (e.target === $("drawer")) closeDrawer();
  });
  $("results").querySelector("tbody").addEventListener("click", (e) => {
    const tr = e.target.closest("tr[data-id]");
    if (tr) openBook(tr.getAttribute("data-id"));
  });
  $("method").addEventListener("change", () => {
    const m = METHODS.find((x) => x.id === $("method").value);
    $("method-blurb").textContent = m?.blurb || "";
    syncCuratorStrictness();
  });
  const strictEl = $("curator-strictness");
  if (strictEl) {
    strictEl.addEventListener("input", () => {
      syncCuratorStrictness();
      scheduleRank();
    });
  }
  const modeEl = $("curator-strictness-mode");
  if (modeEl) {
    modeEl.addEventListener("change", () => {
      syncCuratorStrictness();
      scheduleRank();
    });
  }
  const normieEl = $("normie-depth");
  if (normieEl) {
    normieEl.addEventListener("input", () => {
      syncCuratorStrictness();
      scheduleRank();
    });
  }
  const purityEl = $("normie-purity");
  if (purityEl) {
    purityEl.addEventListener("input", () => {
      syncCuratorStrictness();
      scheduleRank();
    });
  }
  for (const id of ["personal-power", "comedy-cap"]) {
    const el = $(id);
    if (!el) continue;
    el.addEventListener("change", () => {
      savePrefs();
      scheduleRank();
    });
  }
  for (const id of ["geom-ratio", "pct-power", "coverage-weight"]) {
    const el = $(id);
    if (!el) continue;
    el.addEventListener("input", () => {
      syncCuratorStrictness();
      scheduleRank();
    });
  }

  const genreSearch = $("genre-search");
  if (genreSearch) {
    genreSearch.addEventListener("input", () => {
      if (GENRE_TIMER) clearTimeout(GENRE_TIMER);
      GENRE_TIMER = setTimeout(() => suggestGenres(genreSearch.value.trim()), 120);
    });
    genreSearch.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const q = genreSearch.value.trim();
        if (q) {
          addGenreTag(q);
          genreSearch.value = "";
          suggestGenres("");
        }
      }
    });
  }
  const genreSuggest = $("genre-suggest");
  if (genreSuggest) {
    genreSuggest.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-shelf]");
      if (!btn) return;
      addGenreTag(btn.getAttribute("data-shelf"));
      if (genreSearch) genreSearch.value = "";
      suggestGenres("");
    });
  }
  for (const bucket of ["require", "include", "exclude"]) {
    const el = $(`genre-${bucket}-chips`);
    if (!el) continue;
    el.addEventListener("click", (e) => {
      const chip = e.target.closest(".genre-chip[data-shelf]");
      if (!chip) return;
      removeGenreTag(chip.getAttribute("data-bucket"), chip.getAttribute("data-shelf"));
    });
  }
  $("genre-preset-clear")?.addEventListener("click", () => {
    clearGenres();
    savePrefs();
    rerank();
  });
  document.querySelectorAll(".gate-toggle[data-gate]").forEach((btn) => {
    btn.addEventListener("click", () => {
      toggleGate(btn.getAttribute("data-gate"));
    });
  });
  document.querySelectorAll("[data-preset]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const p = btn.getAttribute("data-preset");
      if (p === "favorites") {
        $("method").value = "five_rate_bayes";
        $("min-votes").value = "100";
        $("max-n").value = "0";
      } else if (p === "curator-pct-love") {
        $("method").value = "curator_pct_love";
        $("min-votes").value = "50";
        $("max-n").value = "0";
        $("bayesian-m").value = "40";
        $("curator-strictness").value = "35";
        $("curator-strictness-mode").value = "deweight";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-pure-pct-love") {
        $("method").value = "curator_pure_pct_love";
        $("min-votes").value = "40";
        $("max-n").value = "0";
        $("bayesian-m").value = "40";
        $("curator-strictness").value = "30";
        $("curator-strictness-mode").value = "deweight";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-deep-pct-love") {
        $("method").value = "curator_deep_pct_love";
        $("min-votes").value = "15";
        $("max-n").value = "0";
        $("bayesian-m").value = "30";
        $("curator-strictness").value = "0";
        $("curator-strictness-mode").value = "deweight";
        if ($("normie-depth")) $("normie-depth").value = "40";
        if ($("normie-purity")) $("normie-purity").value = "55";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-pct-tilt") {
        $("method").value = "curator_pct_tilt";
        $("min-votes").value = "40";
        $("max-n").value = "0";
        $("bayesian-m").value = "40";
        $("curator-strictness").value = "35";
        $("curator-strictness-mode").value = "deweight";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-deep-pct-tilt") {
        $("method").value = "curator_deep_pct_tilt";
        $("min-votes").value = "15";
        $("max-n").value = "0";
        $("bayesian-m").value = "30";
        $("curator-strictness").value = "0";
        $("curator-strictness-mode").value = "deweight";
        if ($("normie-depth")) $("normie-depth").value = "40";
        if ($("normie-purity")) $("normie-purity").value = "55";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-deep-pct-geom") {
        $("method").value = "curator_deep_pct_geom";
        $("min-votes").value = "15";
        $("max-n").value = "0";
        $("bayesian-m").value = "30";
        $("curator-strictness").value = "0";
        $("curator-strictness-mode").value = "deweight";
        if ($("normie-depth")) $("normie-depth").value = "40";
        if ($("normie-purity")) $("normie-purity").value = "55";
        if ($("geom-ratio")) $("geom-ratio").value = "20";
        if ($("pct-power")) $("pct-power").value = "25";
        if ($("coverage-weight")) $("coverage-weight").value = "80";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-pct-asymm") {
        $("method").value = "curator_pct_asymm";
        $("min-votes").value = "50";
        $("max-n").value = "0";
        $("bayesian-m").value = "40";
        $("curator-strictness").value = "40";
        $("curator-strictness-mode").value = "deweight";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-pct-gap") {
        $("method").value = "curator_pct_gap";
        $("min-votes").value = "60";
        $("max-n").value = "0";
        $("bayesian-m").value = "40";
        $("curator-strictness").value = "40";
        $("curator-strictness-mode").value = "deweight";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-pct-gem") {
        $("method").value = "curator_pct_gem";
        $("min-votes").value = "40";
        $("max-n").value = "8000";
        $("bayesian-m").value = "35";
        $("curator-strictness").value = "40";
        $("curator-strictness-mode").value = "deweight";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-pure-pct-gem") {
        $("method").value = "curator_pure_pct_gem";
        $("min-votes").value = "35";
        $("max-n").value = "8000";
        $("bayesian-m").value = "35";
        $("curator-strictness").value = "30";
        $("curator-strictness-mode").value = "deweight";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-pct-top") {
        $("method").value = "curator_pct_top";
        $("min-votes").value = "50";
        $("max-n").value = "0";
        $("bayesian-m").value = "40";
        $("curator-strictness").value = "35";
        $("curator-strictness-mode").value = "deweight";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-five") {
        $("method").value = "curator_five_rate";
        $("min-votes").value = "60";
        $("max-n").value = "0";
        $("bayesian-m").value = "40";
        $("curator-strictness").value = "0";
        $("curator-strictness-mode").value = "gate";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-pure-five") {
        $("method").value = "curator_pure_five_rate";
        $("min-votes").value = "40";
        $("max-n").value = "0";
        $("bayesian-m").value = "40";
        $("curator-strictness").value = "25";
        $("curator-strictness-mode").value = "deweight";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-gem") {
        $("method").value = "curator_gem";
        $("min-votes").value = "40";
        $("max-n").value = "8000";
        $("bayesian-m").value = "35";
        $("curator-strictness").value = "0";
        $("curator-strictness-mode").value = "gate";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "curator-mean") {
        $("method").value = "curator_mean";
        $("min-votes").value = "60";
        $("max-n").value = "0";
        $("bayesian-m").value = "50";
        $("curator-strictness").value = "0";
        $("curator-strictness-mode").value = "gate";
        $("taste-enabled").checked = false;
        syncTasteLabels();
      } else if (p === "combo-gem") {
        $("method").value = "combo_gem";
        $("min-votes").value = "80";
        $("max-n").value = "6000";
        $("bayesian-m").value = "45";
        $("taste-enabled").checked = true;
        $("taste-min-lit").value = "40";
        $("taste-max-com").value = "35";
        $("taste-min-net").value = "10";
        $("taste-min-hits").value = "3";
        $("taste-min-lit-hits").value = "5";
        syncTasteLabels();
      } else if (p === "combo-five") {
        $("method").value = "combo_five_rate";
        $("min-votes").value = "80";
        $("max-n").value = "0";
        $("bayesian-m").value = "50";
        $("taste-enabled").checked = true;
        $("taste-min-lit").value = "45";
        $("taste-max-com").value = "30";
        $("taste-min-net").value = "15";
        $("taste-min-hits").value = "3";
        $("taste-min-lit-hits").value = "6";
        syncTasteLabels();
      } else if (p === "picky-rate") {
        $("method").value = "picky_five_rate";
        $("min-votes").value = "100";
        $("max-n").value = "0";
        $("bayesian-m").value = "50";
      } else if (p === "combo-mean") {
        $("method").value = "combo_mean";
        $("min-votes").value = "80";
        $("max-n").value = "0";
        $("bayesian-m").value = "60";
      } else if (p === "combo-liked") {
        $("method").value = "combo_liked";
        $("min-votes").value = "80";
        $("max-n").value = "0";
        $("bayesian-m").value = "50";
      } else if (p === "picky-gem") {
        $("method").value = "picky_gem";
        $("min-votes").value = "80";
        $("max-n").value = "12000";
        $("bayesian-m").value = "45";
      } else if (p === "cross-five") {
        $("method").value = "cross_five";
        $("min-votes").value = "100";
        $("max-n").value = "0";
        $("bayesian-m").value = "50";
      } else if (p === "combo-love") {
        $("method").value = "combo_love";
        $("min-votes").value = "40";
        $("max-n").value = "2500";
        $("bayesian-m").value = "40";
        $("taste-enabled").checked = true;
        $("taste-min-lit").value = "40";
        $("taste-max-com").value = "35";
        $("taste-min-net").value = "10";
        $("taste-min-hits").value = "3";
        $("taste-min-lit-hits").value = "5";
        syncTasteLabels();
      } else if (p === "combo-power") {
        $("method").value = "combo_power";
        $("min-votes").value = "40";
        $("max-n").value = "0";
        $("bayesian-m").value = "60";
        $("taste-enabled").checked = true;
        $("taste-min-lit").value = "40";
        $("taste-max-com").value = "35";
        $("taste-min-net").value = "10";
        $("taste-min-hits").value = "3";
        $("taste-min-lit-hits").value = "5";
        syncTasteLabels();
      } else if (p === "imdb") {
        $("method").value = "imdb_bayes";
        $("min-votes").value = "80";
        $("max-n").value = "0";
      } else if (p === "lit-gem") {
        $("method").value = "lit_gem";
        $("min-votes").value = "30";
        $("max-n").value = "8000";
      } else if (p === "lit-five") {
        $("method").value = "lit_weighted_five_rate";
        $("min-votes").value = "40";
        $("max-n").value = "0";
      } else if (p === "picky") {
        $("method").value = "picky_five";
        $("min-votes").value = "50";
        $("max-n").value = "0";
      } else if (p === "divisive") {
        $("method").value = "polarization";
        $("min-votes").value = "80";
        $("max-n").value = "0";
      } else if (p === "gems") {
        $("method").value = "hidden_gem";
        $("min-votes").value = "40";
        $("max-n").value = "5000";
      }
      const m = METHODS.find((x) => x.id === $("method").value);
      $("method-blurb").textContent = m?.blurb || "";
      savePrefs();
      rerank();
    });
  });
  document.querySelectorAll("[data-taste-preset]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const name = btn.getAttribute("data-taste-preset");
      $("taste-enabled").checked = true;
      if (name === "off") {
        $("taste-min-lit").value = "0";
        $("taste-max-com").value = "100";
        $("taste-min-net").value = "-100";
        $("taste-min-hits").value = "1";
        $("taste-min-lit-hits").value = "0";
      } else if (name === "lean") {
        $("taste-min-lit").value = "40";
        $("taste-max-com").value = "40";
        $("taste-min-net").value = "0";
        $("taste-min-hits").value = "2";
        $("taste-min-lit-hits").value = "5";
      } else if (name === "strict") {
        $("taste-min-lit").value = "60";
        $("taste-max-com").value = "25";
        $("taste-min-net").value = "20";
        $("taste-min-hits").value = "3";
        $("taste-min-lit-hits").value = "10";
      }
      syncTasteLabels();
      savePrefs();
      rerank();
    });
  });
}

async function main() {
  wire();
  const res = await fetch("/api/meta");
  META = await res.json();
  if (META.error) throw new Error(META.error);
  METHODS = META.methods || [];
  $("list-title").textContent = META.list_title || "Favorites explorer";
  const nSf = META.n_works_sf;
  const worksBit =
    nSf != null
      ? `${(META.n_works || 0).toLocaleString()} works (${Number(nSf).toLocaleString()} SF)`
      : `${(META.n_works || 0).toLocaleString()} works`;
  $("data-meta").textContent =
    `${worksBit} · ${(META.n_five_star_events || 0).toLocaleString()} five-stars · ` +
    `global P(5★) ${pct(META.global_p5)} · ${META.ballot_model || ""}`;
  if ($("genre-section") && META.genres_available === false) {
    $("genre-section").hidden = true;
  }
  const sel = $("method");
  sel.innerHTML = METHODS.map(
    (m) => `<option value="${escapeHtml(m.id)}">${escapeHtml(m.name)}</option>`
  ).join("");
  sel.value = "curator_pct_love";
  loadPrefs();
  const noFilter =
    !GATE_STATE.length &&
    !GENRE_STATE.require.length &&
    !GENRE_STATE.include.length &&
    !GENRE_STATE.exclude.length;
  if (noFilter && META.genres_available !== false) {
    GATE_STATE = ["sf"];
  }
  renderGenreChips();
  if (![...sel.options].some((o) => o.value === sel.value)) {
    sel.value = "curator_five_rate";
  }
  if (![...sel.options].some((o) => o.value === sel.value) && METHODS[0]) {
    sel.value = METHODS[0].id;
  }
  $("method-blurb").textContent =
    METHODS.find((m) => m.id === sel.value)?.blurb || "";
  syncTasteLabels();

  try {
    const tasteRes = await fetch("/api/taste");
    if (tasteRes.ok) {
      TASTE = await tasteRes.json();
      renderTasteChips();
    }
  } catch (_) {
    /* optional */
  }

  await rerank();
}

main().catch((err) => {
  $("data-meta").textContent = String(err.message || err);
});
