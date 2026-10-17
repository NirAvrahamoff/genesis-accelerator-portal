// Admin dashboard: filtering, sorting, details dialog and charts.
// All user-supplied text is inserted with textContent, never innerHTML.
(function () {
  const rows = JSON.parse(document.getElementById("appData").textContent);
  const charts = JSON.parse(document.getElementById("chartData").textContent);
  const tbody = document.querySelector("#apps tbody");
  const $ = (id) => document.getElementById(id);
  const filters = { q: $("q"), sector: $("fSector"), stage: $("fStage"), funding: $("fFunding"), score: $("fScore") };
  let sortKey = "submitted_at";
  let sortDesc = true;

  function cell(text, className) {
    const td = document.createElement("td");
    td.textContent = text ?? "";
    if (className) td.className = className;
    return td;
  }

  function visibleRows() {
    const q = filters.q.value.trim().toLowerCase();
    const minScore = Number(filters.score.value);
    return rows
      .filter((r) =>
        (!q || `${r.full_name} ${r.company_name}`.toLowerCase().includes(q)) &&
        (!filters.sector.value || r.primary_sector === filters.sector.value) &&
        (!filters.stage.value || r.startup_stage === filters.stage.value) &&
        (!filters.funding.value || r.raised_funding === filters.funding.value) &&
        r.fit_score >= minScore)
      .sort((a, b) => {
        const A = a[sortKey], B = b[sortKey];
        const cmp = typeof A === "number" ? A - B : String(A).localeCompare(String(B));
        return sortDesc ? -cmp : cmp;
      });
  }

  function render() {
    const list = visibleRows();
    tbody.replaceChildren(...list.map((r) => {
      const tr = document.createElement("tr");
      tr.append(
        cell(r.submitted_at.slice(0, 10)),
        cell(r.full_name),
        cell(r.company_name),
        cell(r.primary_sector),
        cell(r.startup_stage),
        cell(r.raised_funding),
        cell(r.revenue_label),
      );
      const score = cell(r.fit_score, "num");
      const badge = document.createElement("span");
      badge.className = `score score-${r.band}`;
      badge.textContent = r.fit_score;
      score.replaceChildren(badge);
      const action = document.createElement("td");
      const btn = document.createElement("button");
      btn.className = "btn btn-ghost btn-small";
      btn.textContent = "Details";
      btn.addEventListener("click", () => openDetails(r));
      action.append(btn);
      tr.append(score, action);
      return tr;
    }));
    $("countLabel").textContent = `Showing ${list.length} of ${rows.length}`;
    document.querySelectorAll("#apps th[data-key]").forEach((th) => {
      th.classList.toggle("sorted", th.dataset.key === sortKey);
      th.dataset.dir = th.dataset.key === sortKey ? (sortDesc ? "desc" : "asc") : "";
    });
  }

  const DETAIL_FIELDS = [
    ["Founder", "full_name"], ["Role", "role_in_company"], ["Email", "email"], ["Phone", "phone"],
    ["LinkedIn", "linkedin"], ["Website", "website_link"], ["Sector", "primary_sector"], ["Stage", "startup_stage"],
    ["Co-founders", "cofounders_label"], ["Time on startup", "time_label"], ["Funding", "raised_funding"],
    ["Revenue", "revenue_label"], ["Hopes to gain", "gain_from_program"], ["Description", "startup_description", true],
    ["Customers", "current_customers", true], ["Goals (6 months)", "goals_next_6_months", true],
    ["What makes the team unique", "team_unique", true],
  ];

  function openDetails(r) {
    $("dTitle").textContent = `${r.company_name} · Fit Score ${r.fit_score}`;
    const items = DETAIL_FIELDS.filter(([, key]) => r[key]).map(([label, key, full]) => {
      const div = document.createElement("div");
      if (full) div.className = "full";
      const dt = document.createElement("dt");
      dt.textContent = label;
      const dd = document.createElement("dd");
      dd.textContent = r[key];
      div.append(dt, dd);
      return div;
    });
    $("dBody").replaceChildren(...items);
    $("details").showModal();
  }
  $("dClose").addEventListener("click", () => $("details").close());

  Object.values(filters).forEach((el) => el.addEventListener("input", render));
  $("reset").addEventListener("click", () => {
    filters.q.value = "";
    ["sector", "stage", "funding"].forEach((k) => (filters[k].value = ""));
    filters.score.value = "0";
    render();
  });
  document.querySelectorAll("#apps th[data-key]").forEach((th) => {
    th.addEventListener("click", () => {
      sortDesc = th.dataset.key === sortKey ? !sortDesc : true;
      sortKey = th.dataset.key;
      render();
    });
  });
  render();

  // Charts
  if (!window.Chart) return;
  const css = getComputedStyle(document.documentElement);
  const accent = css.getPropertyValue("--accent").trim();
  const ink = css.getPropertyValue("--muted").trim();
  Chart.defaults.color = ink;
  Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
  const base = {
    plugins: { legend: { display: false } },
    scales: { x: { grid: { display: false } }, y: { beginAtZero: true, ticks: { precision: 0 } } },
    maintainAspectRatio: false,
  };
  const bar = (id, pairs, colors, horizontal) => new Chart($(id), {
    type: "bar",
    data: { labels: pairs.map((p) => p[0]), datasets: [{ data: pairs.map((p) => p[1]), backgroundColor: colors, borderRadius: 4 }] },
    options: horizontal ? { ...base, indexAxis: "y", scales: { x: base.scales.y, y: { grid: { display: false } } } } : base,
  });
  bar("sectorChart", charts.sector, accent, true);
  bar("stageChart", charts.stage, accent);
  const band = (s) => (s >= 7 ? css.getPropertyValue("--good") : s >= 4 ? css.getPropertyValue("--mid") : css.getPropertyValue("--low")).trim();
  bar("scoreChart", charts.score, charts.score.map((p) => band(Number(p[0]))));
})();
