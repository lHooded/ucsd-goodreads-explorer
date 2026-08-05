/** Curators explorer — thin client over /api/* */

let METRICS = [];
let SCALE_MODES = [];
let PRESETS = {};
let PACK = null;
let LAST = [];
let TIMER = null;
let SEARCH_TIMER = null;

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
  if (raw === undefined || raw === null || String(raw).trim() === "") return fallback;
  const v = Number(raw);
  return Number.isFinite(v) ? v : fallback;
}

function checked(id) {
  return Boolean($(id)?.checked);
}

function pct(x) {
  return x == null || !Number.isFinite(x) ? "—" : `${(100 * x).toFixed(1)}%`;
}

function syncLabels() {
  $("deweight-val").textContent = String(Math.trunc(num("deweight", 15)));
  $("purity-val").textContent = String(Math.trunc(num("purity", 55)));
  const m = METRICS.find((x) => x.id === $("metric").value);
  $("metric-blurb").textContent = m?.blurb || "";
  const s = SCALE_MODES.find((x) => x.id === $("scale-mode").value);
  $("scale-blurb").textContent = s?.blurb || "";
}

function collectParams() {
  return {
    metric: $("metric").value || "love",
    scale_mode: $("scale-mode").value || "adjusted",
    deweight: num("deweight", 15),
    purity: num("purity", 55),
    bayesian_m: num("bayesian-m", 30),
    min_votes: Math.trunc(num("min-votes", 25)),
    limit: Math.trunc(num("limit", 200)),
    q: ($("q").value || "").trim(),
    sf_only: checked("sf-only"),
    fiction_only: checked("fiction-only"),
    exclude_comics: checked("exclude-comics"),
    exclude_picture_books: checked("exclude-picture"),
    exclude_derivatives: checked("exclude-derivatives"),
    exclude_collections: checked("exclude-collections"),
    collapse_duplicates: checked("collapse-duplicates"),
    apply_format_weight: checked("format-weight"),
  };
}

function applySliderPreset(id) {
  const p = PRESETS[id];
  if (!p) return;
  if (p.deweight != null) $("deweight").value = p.deweight;
  if (p.purity != null) $("purity").value = p.purity;
  document.querySelectorAll("#presets button").forEach((b) => {
    b.classList.toggle("active", b.dataset.id === id);
  });
  syncLabels();
  scheduleRank();
}

function renderPresets() {
  const box = $("presets");
  box.innerHTML = "";
  for (const [id, p] of Object.entries(PRESETS)) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.dataset.id = id;
    btn.textContent = p.label || id;
    btn.title = p.notes || "";
    btn.addEventListener("click", () => applySliderPreset(id));
    box.appendChild(btn);
  }
}

function renderPackLists() {
  if (!PACK) return;
  const pos = PACK.positive_authors || [];
  const neg = PACK.negative_authors || [];
  const neu = PACK.neutral_titles || [];
  $("pos-count").textContent = `(${pos.length})`;
  $("neg-count").textContent = `(${neg.length})`;
  $("neu-count").textContent = `(${neu.length})`;

  const fill = (el, items, kind) => {
    el.innerHTML = items
      .map((it, i) => {
        const label = kind === "neutral" ? it : it.name || it.match || it.author_id;
        return `<div class="pack-row"><span>${escapeHtml(label)}</span>
          <button type="button" data-kind="${kind}" data-i="${i}" title="Remove">×</button></div>`;
      })
      .join("");
  };
  fill($("pos-list"), pos, "positive");
  fill($("neg-list"), neg, "negative");
  fill($("neu-list"), neu, "neutral");
}

async function pushPack() {
  const res = await fetch("/api/taste", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: "update",
      positive_authors: PACK.positive_authors,
      negative_authors: PACK.negative_authors,
      neutral_titles: PACK.neutral_titles,
    }),
  });
  const data = await res.json();
  PACK = data.pack;
  $("pack-meta").textContent = `hash ${data.pack_hash} · ${
    data.uses_mint || data.matches_mint ? "using mint table" : "live pack recompute"
  }`;
  renderPackLists();
  scheduleRank();
}

function removePackItem(kind, i) {
  if (!PACK) return;
  if (kind === "positive") PACK.positive_authors.splice(i, 1);
  else if (kind === "negative") PACK.negative_authors.splice(i, 1);
  else PACK.neutral_titles.splice(i, 1);
  pushPack();
}

function addAuthor(side, author) {
  if (!PACK || !author?.author_id) return;
  const list = side === "positive" ? PACK.positive_authors : PACK.negative_authors;
  if (list.some((a) => String(a.author_id) === String(author.author_id))) return;
  list.push({
    author_id: String(author.author_id),
    name: author.name || author.match,
    match: author.match || author.name,
  });
  pushPack();
}

async function authorSearch(q, suggestEl, side) {
  if (!q || q.length < 2) {
    suggestEl.hidden = true;
    suggestEl.innerHTML = "";
    return;
  }
  const res = await fetch(`/api/authors?q=${encodeURIComponent(q)}&limit=12`);
  const data = await res.json();
  const rows = data.results || [];
  if (!rows.length) {
    suggestEl.hidden = true;
    suggestEl.innerHTML = "";
    return;
  }
  suggestEl.hidden = false;
  suggestEl.innerHTML = rows
    .map(
      (a) =>
        `<button type="button" data-aid="${escapeHtml(a.author_id)}" data-name="${escapeHtml(
          a.name || ""
        )}">${escapeHtml(a.name)} <span class="mono">${escapeHtml(a.author_id)}</span></button>`
    )
    .join("");
  suggestEl.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      addAuthor(side, { author_id: btn.dataset.aid, name: btn.dataset.name, match: btn.dataset.name });
      suggestEl.hidden = true;
      suggestEl.innerHTML = "";
      if (side === "positive") $("pos-search").value = "";
      else $("neg-search").value = "";
    });
  });
}

function renderStats(payload) {
  const c = payload.cohort || {};
  const p = payload.params || {};
  const ms = payload.elapsed_ms != null ? `${payload.elapsed_ms} ms` : "—";
  $("stats").innerHTML = `
    <div class="stat"><div class="v">${payload.n_results ?? 0}</div><div class="l">Shown</div></div>
    <div class="stat"><div class="v">${c.n_curators ?? "—"}</div><div class="l">Curators</div></div>
    <div class="stat"><div class="v">${escapeHtml(c.cohort_kind || "—")}</div><div class="l">Cohort</div></div>
    <div class="stat"><div class="v">${escapeHtml(String(p.scale_mode || ""))}</div><div class="l">Scale</div></div>
    <div class="stat"><div class="v">${ms}</div><div class="l">Query</div></div>
  `;
}

function renderResults(rows) {
  LAST = rows || [];
  const tb = $("results");
  if (!LAST.length) {
    tb.innerHTML = `<tr><td colspan="7">No results.</td></tr>`;
    return;
  }
  tb.innerHTML = LAST.map(
    (r) => `
    <tr data-id="${escapeHtml(r.work_id)}">
      <td class="mono">${r.rank}</td>
      <td class="title-cell">${escapeHtml(r.title)}</td>
      <td>${escapeHtml(r.author)}</td>
      <td class="mono">${r.n}</td>
      <td class="mono">${r.mean == null ? "—" : r.mean.toFixed(3)}</td>
      <td class="mono">${pct(r.p5)}</td>
      <td class="mono">${r.score == null ? "—" : r.score.toFixed(4)}</td>
    </tr>`
  ).join("");
  tb.querySelectorAll("tr[data-id]").forEach((tr) => {
    tr.addEventListener("click", () => openBook(tr.dataset.id));
  });
}

async function rank() {
  syncLabels();
  $("data-meta").textContent = "Ranking…";
  const params = collectParams();
  const res = await fetch("/api/rank", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (data.error) {
    $("data-meta").textContent = `Error: ${data.error}`;
    return;
  }
  renderStats(data);
  renderResults(data.results || []);
  const c = data.cohort || {};
  $("data-meta").textContent = `${data.n_results} books · ${c.n_curators} curators (${c.cohort_kind}/${c.source}) · ${data.elapsed_ms} ms`;
}

function scheduleRank() {
  clearTimeout(TIMER);
  TIMER = setTimeout(rank, 280);
}

function starBars(stars, nOrW) {
  const total = Number(nOrW) || Object.values(stars || {}).reduce((a, b) => a + Number(b || 0), 0) || 1;
  return [5, 4, 3, 2, 1]
    .map((s) => {
      const v = Number((stars || {})[String(s)] || 0);
      const w = (100 * v) / total;
      return `<div class="star-row"><span>${s}★</span><span class="bar"><i style="width:${w.toFixed(
        1
      )}%"></i></span><span class="mono">${v.toFixed ? (Number.isInteger(v) ? v : v.toFixed(1)) : v}</span></div>`;
    })
    .join("");
}

async function openBook(workId) {
  const params = collectParams();
  const res = await fetch(`/api/book/${encodeURIComponent(workId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (data.error) return;
  const b = data.book;
  $("drawer-title").textContent = b.title;
  $("drawer-sub").textContent = `${b.author} · n=${b.n} · mean=${
    b.mean == null ? "—" : b.mean.toFixed(2)
  } · ${b.book_url || ""}`;
  const h = data.histograms || {};
  const g = h.global;
  const c = h.curators;
  let html = "";
  if (g) {
    html += `<div class="hist-block"><h3>${escapeHtml(g.label)}</h3>
      <p class="hint">n=${g.n} · mean=${g.mean == null ? "—" : g.mean.toFixed(2)} · P(5★)=${pct(g.p5)}</p>
      <div class="star-dist">${starBars(g.stars, g.n)}</div></div>`;
  }
  if (c) {
    const denom = c.weighted ? c.w_sum : c.n;
    html += `<div class="hist-block"><h3>${escapeHtml(c.label)}</h3>
      <p class="hint">raters=${c.n}${c.weighted ? ` · weightΣ=${(c.w_sum || 0).toFixed(1)}` : ""} · mean=${
        c.mean == null ? "—" : c.mean.toFixed(2)
      } · top=${pct(c.p5)}</p>
      <div class="star-dist">${starBars(c.stars, denom)}</div></div>`;
  }
  $("drawer-hists").innerHTML = html;
  $("drawer-note").textContent =
    "Curator hist uses the same deweight/purity/pack cohort as the current ranking.";
  $("drawer").hidden = false;
}

function copyList() {
  const text = LAST.map((r) => `${r.rank}. ${r.title} — ${r.author}`).join("\n");
  navigator.clipboard?.writeText(text).then(() => {
    const btn = $("copy-list");
    btn.classList.add("copied");
    btn.textContent = "Copied";
    setTimeout(() => {
      btn.classList.remove("copied");
      btn.textContent = "Copy list";
    }, 1200);
  });
}

async function init() {
  const meta = await (await fetch("/api/meta")).json();
  METRICS = meta.metrics || [];
  SCALE_MODES = meta.scale_modes || [];
  const d = meta.defaults || {};

  $("metric").innerHTML = METRICS.map(
    (m) => `<option value="${escapeHtml(m.id)}">${escapeHtml(m.label)}</option>`
  ).join("");
  $("scale-mode").innerHTML = SCALE_MODES.map(
    (s) => `<option value="${escapeHtml(s.id)}">${escapeHtml(s.label)}</option>`
  ).join("");

  if (d.metric) $("metric").value = d.metric;
  if (d.scale_mode) $("scale-mode").value = d.scale_mode;
  if (d.deweight != null) $("deweight").value = d.deweight;
  if (d.purity != null) $("purity").value = d.purity;
  if (d.bayesian_m != null) $("bayesian-m").value = d.bayesian_m;
  if (d.min_votes != null) $("min-votes").value = d.min_votes;
  if (d.limit != null) $("limit").value = d.limit;
  if (d.sf_only != null) $("sf-only").checked = Boolean(d.sf_only);

  const taste = await (await fetch("/api/taste")).json();
  PACK = taste.pack;
  PRESETS = taste.presets || {};
  $("pack-meta").textContent = `hash ${taste.pack_hash} · ${
    taste.uses_mint || taste.matches_mint ? "using mint table" : "live pack recompute"
  }`;
  renderPresets();
  renderPackLists();
  applySliderPreset("default_literary");

  $("metric").addEventListener("change", () => {
    syncLabels();
    scheduleRank();
  });
  $("scale-mode").addEventListener("change", () => {
    syncLabels();
    scheduleRank();
  });
  ["deweight", "purity"].forEach((id) => {
    $(id).addEventListener("input", () => {
      syncLabels();
      scheduleRank();
    });
  });
  ["bayesian-m", "min-votes", "limit", "q"].forEach((id) => {
    $(id).addEventListener("change", scheduleRank);
    $(id).addEventListener("keydown", (e) => {
      if (e.key === "Enter") scheduleRank();
    });
  });
  [
    "sf-only",
    "fiction-only",
    "exclude-comics",
    "exclude-picture",
    "exclude-derivatives",
    "exclude-collections",
    "collapse-duplicates",
    "format-weight",
  ].forEach((id) => $(id).addEventListener("change", scheduleRank));

  $("recompute").addEventListener("click", rank);
  $("copy-list").addEventListener("click", copyList);
  $("drawer-close").addEventListener("click", () => {
    $("drawer").hidden = true;
  });
  $("drawer").addEventListener("click", (e) => {
    if (e.target === $("drawer")) $("drawer").hidden = true;
  });

  $("pack-toggle").addEventListener("click", () => {
    const ed = $("pack-editor");
    ed.hidden = !ed.hidden;
    $("pack-toggle").textContent = ed.hidden ? "Edit packs" : "Hide packs";
  });
  $("pack-reset").addEventListener("click", async () => {
    const data = await (
      await fetch("/api/taste", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "reset" }),
      })
    ).json();
    PACK = data.pack;
    $("pack-meta").textContent = `hash ${data.pack_hash} · reset · ${
      data.uses_mint || data.matches_mint ? "mint" : "live"
    }`;
    renderPackLists();
    applySliderPreset("default_literary");
  });

  document.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-kind][data-i]");
    if (!btn) return;
    removePackItem(btn.dataset.kind, Number(btn.dataset.i));
  });

  $("pos-search").addEventListener("input", () => {
    clearTimeout(SEARCH_TIMER);
    SEARCH_TIMER = setTimeout(
      () => authorSearch($("pos-search").value.trim(), $("pos-suggest"), "positive"),
      220
    );
  });
  $("neg-search").addEventListener("input", () => {
    clearTimeout(SEARCH_TIMER);
    SEARCH_TIMER = setTimeout(
      () => authorSearch($("neg-search").value.trim(), $("neg-suggest"), "negative"),
      220
    );
  });
  $("neu-add-btn").addEventListener("click", () => {
    const t = ($("neu-add").value || "").trim();
    if (!t || !PACK) return;
    if (!PACK.neutral_titles.includes(t)) PACK.neutral_titles.push(t);
    $("neu-add").value = "";
    pushPack();
  });

  syncLabels();
  await rank();
}

init().catch((err) => {
  $("data-meta").textContent = `Init failed: ${err}`;
  console.error(err);
});
