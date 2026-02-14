const I18N = {
  en: {
    tab: "Repo Inspector - Pages",
    heroKicker: "STATIC MODE",
    heroTitle: "Repo Inspector",
    heroSubtitle:
      "Use pre-generated reports from GitHub Actions or live data from your Vercel API.",
    repoLabel: "GitHub repository URL",
    loadButton: "Load report",
    invalidUrl: "Enter a valid GitHub URL like https://github.com/owner/repo",
    loading: "Loading report...",
    noReport: "Report not found.",
    reportReady: "Report loaded.",
    totalScore: "Total score",
    source: "Source",
    flow: "Flow",
    sourceValue: "web/reports/*.json",
    flowValue: "Actions -> Pages",
    apiLabel: "API",
    apiLocal: "local reports",
    apiRemote: "vercel api",
    reportTitle: "Repository report",
    reportRepo: "Repository",
    pass: "PASS",
    warn: "WARN",
    fail: "FAIL",
    codeLines: "Code lines",
    codeFiles: "Code files",
    scanned: "Scanned",
    sampledNote: "Line metrics were sampled because repository contains many files.",
    downloadJson: "Download JSON",
    checkAgain: "Check again",
    openGenerator: "Open SVG/JSON generator",
    showOnlyIssues: "Show only issues",
    recommendations: "Recommendations",
    openActions: "Open Actions workflow",
    generateHint: "Generate report via workflow generate-report.yml and reload this page.",
    apiHint: "Set API_BASE in web/config.js to your Vercel URL for live API mode.",
    noStacks: "None",
  },
  ru: {
    tab: "Repo Inspector - Pages",
    heroKicker: "\u0421\u0422\u0410\u0422\u0418\u0427\u0415\u0421\u041a\u0418\u0419 \u0420\u0415\u0416\u0418\u041c",
    heroTitle: "Repo Inspector",
    heroSubtitle:
      "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 \u0433\u043e\u0442\u043e\u0432\u044b\u0435 \u043e\u0442\u0447\u0435\u0442\u044b \u0438\u0437 GitHub Actions \u0438\u043b\u0438 \u0436\u0438\u0432\u044b\u0435 \u0434\u0430\u043d\u043d\u044b\u0435 \u0441 Vercel API.",
    repoLabel: "\u0421\u0441\u044b\u043b\u043a\u0430 \u043d\u0430 GitHub-\u0440\u0435\u043f\u043e\u0437\u0438\u0442\u043e\u0440\u0438\u0439",
    loadButton: "\u0417\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u044c \u043e\u0442\u0447\u0435\u0442",
    invalidUrl: "\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u0443\u044e \u0441\u0441\u044b\u043b\u043a\u0443 \u0432\u0438\u0434\u0430 https://github.com/owner/repo",
    loading: "\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u043e\u0442\u0447\u0435\u0442\u0430...",
    noReport: "\u041e\u0442\u0447\u0435\u0442 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d.",
    reportReady: "\u041e\u0442\u0447\u0435\u0442 \u0437\u0430\u0433\u0440\u0443\u0436\u0435\u043d.",
    totalScore: "\u0418\u0442\u043e\u0433\u043e\u0432\u044b\u0439 score",
    source: "\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a",
    flow: "\u041f\u043e\u0442\u043e\u043a",
    sourceValue: "web/reports/*.json",
    flowValue: "Actions -> Pages",
    apiLabel: "API",
    apiLocal: "\u043b\u043e\u043a\u0430\u043b\u044c\u043d\u044b\u0435 \u043e\u0442\u0447\u0435\u0442\u044b",
    apiRemote: "vercel api",
    reportTitle: "\u041e\u0442\u0447\u0435\u0442 \u043f\u043e \u0440\u0435\u043f\u043e\u0437\u0438\u0442\u043e\u0440\u0438\u044e",
    reportRepo: "\u0420\u0435\u043f\u043e\u0437\u0438\u0442\u043e\u0440\u0438\u0439",
    pass: "PASS",
    warn: "WARN",
    fail: "FAIL",
    codeLines: "\u0421\u0442\u0440\u043e\u043a\u0438 \u043a\u043e\u0434\u0430",
    codeFiles: "\u0424\u0430\u0439\u043b\u044b \u043a\u043e\u0434\u0430",
    scanned: "\u041f\u0440\u043e\u0441\u043a\u0430\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u043e",
    sampledNote:
      "\u041c\u0435\u0442\u0440\u0438\u043a\u0438 \u0441\u0442\u0440\u043e\u043a \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u044b \u043f\u043e \u0432\u044b\u0431\u043e\u0440\u043a\u0435 \u0438\u0437-\u0437\u0430 \u0431\u043e\u043b\u044c\u0448\u043e\u0433\u043e \u0447\u0438\u0441\u043b\u0430 \u0444\u0430\u0439\u043b\u043e\u0432.",
    downloadJson: "\u0421\u043a\u0430\u0447\u0430\u0442\u044c JSON",
    checkAgain: "\u041f\u0440\u043e\u0432\u0435\u0440\u0438\u0442\u044c \u0437\u0430\u043d\u043e\u0432\u043e",
    openGenerator: "\u041e\u0442\u043a\u0440\u044b\u0442\u044c SVG/JSON \u0433\u0435\u043d\u0435\u0440\u0430\u0442\u043e\u0440",
    showOnlyIssues: "\u041f\u043e\u043a\u0430\u0437\u044b\u0432\u0430\u0442\u044c \u0442\u043e\u043b\u044c\u043a\u043e \u043f\u0440\u043e\u0431\u043b\u0435\u043c\u044b",
    recommendations: "\u0420\u0435\u043a\u043e\u043c\u0435\u043d\u0434\u0430\u0446\u0438\u0438",
    openActions: "\u041e\u0442\u043a\u0440\u044b\u0442\u044c workflow \u0432 Actions",
    generateHint: "\u0421\u0433\u0435\u043d\u0435\u0440\u0438\u0440\u0443\u0439\u0442\u0435 \u043e\u0442\u0447\u0435\u0442 \u0447\u0435\u0440\u0435\u0437 workflow generate-report.yml \u0438 \u043f\u0435\u0440\u0435\u0437\u0430\u0433\u0440\u0443\u0437\u0438\u0442\u0435 \u0441\u0442\u0440\u0430\u043d\u0438\u0446\u0443.",
    apiHint: "\u0423\u043a\u0430\u0436\u0438\u0442\u0435 API_BASE \u0432 web/config.js \u0434\u043b\u044f \u0440\u0435\u0436\u0438\u043c\u0430 \u0441 \u0436\u0438\u0432\u044b\u043c API.",
    noStacks: "\u041d\u0435\u0442",
  },
};

const REPO_RE = /^https?:\/\/github\.com\/([^/\s]+)\/([^/\s#]+?)(?:\.git)?\/?$/;
const CATEGORY_NAME_BY_ID = {
  docs: { en: "Docs", ru: "\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0446\u0438\u044f" },
  ci: { en: "CI", ru: "CI" },
  security: { en: "Security", ru: "\u0411\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u044c" },
  quality: { en: "Quality", ru: "\u041a\u0430\u0447\u0435\u0441\u0442\u0432\u043e" },
  maintenance: { en: "Maintenance", ru: "\u041f\u043e\u0434\u0434\u0435\u0440\u0436\u043a\u0430" },
  governance: { en: "Governance", ru: "\u0423\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435" },
};

const refs = {
  body: document.body,
  langSwitch: document.getElementById("lang-switch"),
  heroKicker: document.getElementById("hero-kicker"),
  heroTitle: document.getElementById("hero-title"),
  heroSubtitle: document.getElementById("hero-subtitle"),
  repoLabel: document.getElementById("repo-label"),
  loadBtn: document.getElementById("load-btn"),
  form: document.getElementById("scan-form"),
  input: document.getElementById("repo_url"),
  error: document.getElementById("form-error"),
  actionHelp: document.getElementById("action-help"),
  reportRoot: document.getElementById("report-root"),
  previewScoreLabel: document.getElementById("preview-score-label"),
  previewStatusLabel: document.getElementById("preview-status-label"),
  previewFlowLabel: document.getElementById("preview-flow-label"),
  previewStatusValue: document.getElementById("preview-status-value"),
  previewFlowValue: document.getElementById("preview-flow-value"),
  previewApiLabel: document.getElementById("preview-api-label"),
  previewApiValue: document.getElementById("preview-api-value"),
  openGenerator: document.getElementById("open-generator"),
};

let lang = "en";

function tr(key) {
  return (I18N[lang] && I18N[lang][key]) || I18N.en[key] || key;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeApiBase(raw) {
  const value = String(raw || "").trim();
  if (!value) return "";
  return value.replace(/\/$/, "");
}

function getApiBase() {
  const cfg = window.REPO_INSPECTOR_CONFIG || {};
  const fromConfig = normalizeApiBase(cfg.API_BASE);
  if (fromConfig) return fromConfig;

  const fromQuery = normalizeApiBase(new URLSearchParams(window.location.search).get("api_base"));
  if (fromQuery) return fromQuery;

  return "";
}

const API_BASE = getApiBase();
const USE_REMOTE_API = Boolean(API_BASE);

function initRevealAnimations() {
  const cards = Array.from(document.querySelectorAll(".card"));
  cards.forEach((node, index) => {
    node.classList.add("reveal");
    node.style.setProperty("--reveal-delay", `${Math.min(index * 55, 420)}ms`);
  });
  if (!("IntersectionObserver" in window)) {
    cards.forEach((node) => node.classList.add("is-visible"));
    return;
  }
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) entry.target.classList.add("is-visible");
      });
    },
    { threshold: 0.12 }
  );
  cards.forEach((node) => observer.observe(node));
}

function parseRepoUrl(url) {
  const match = REPO_RE.exec(String(url || "").trim());
  if (!match) return null;
  return { owner: match[1], repo: match[2] };
}

function currentRepoPath() {
  const host = window.location.hostname;
  const parts = window.location.pathname.split("/").filter(Boolean);
  if (host.endsWith(".github.io") && parts.length > 0) {
    const owner = host.replace(".github.io", "");
    const repo = parts[0];
    return { owner, repo };
  }
  return null;
}

function renderHelp(repoUrl) {
  const ghRepo = currentRepoPath();
  const actionUrl = ghRepo
    ? `https://github.com/${ghRepo.owner}/${ghRepo.repo}/actions/workflows/generate-report.yml`
    : "";
  const localCmd = `python scripts/generate_report.py --repo-url "${repoUrl}" --lang ${lang}`;
  const apiHint = !USE_REMOTE_API ? `<p>${escapeHtml(tr("apiHint"))}</p>` : "";

  refs.actionHelp.classList.remove("hidden");
  refs.actionHelp.classList.add("muted");
  refs.actionHelp.innerHTML = `
    <p>${escapeHtml(tr("generateHint"))}</p>
    ${apiHint}
    ${
      actionUrl
        ? `<p><a class="link" href="${escapeHtml(actionUrl)}" target="_blank" rel="noopener">${escapeHtml(
            tr("openActions")
          )}</a></p>`
        : ""
    }
    <pre>${escapeHtml(localCmd)}</pre>
  `;
}

function applyLangSwitch() {
  refs.body.dataset.lang = lang;
  refs.langSwitch.classList.toggle("lang-ru", lang === "ru");
  refs.langSwitch.classList.toggle("lang-en", lang === "en");
  refs.langSwitch.querySelectorAll(".link").forEach((node) => {
    node.classList.toggle("active", node.dataset.lang === lang);
  });

  refs.heroKicker.textContent = tr("heroKicker");
  refs.heroTitle.textContent = tr("heroTitle");
  refs.heroSubtitle.textContent = tr("heroSubtitle");
  refs.repoLabel.textContent = tr("repoLabel");
  refs.loadBtn.textContent = tr("loadButton");

  refs.previewScoreLabel.textContent = tr("totalScore");
  refs.previewStatusLabel.textContent = tr("source");
  refs.previewFlowLabel.textContent = tr("flow");
  refs.previewStatusValue.textContent = tr("sourceValue");
  refs.previewFlowValue.textContent = tr("flowValue");
  refs.previewApiLabel.textContent = tr("apiLabel");
  refs.previewApiValue.textContent = USE_REMOTE_API ? API_BASE : tr("apiLocal");
  if (refs.openGenerator) refs.openGenerator.textContent = tr("openGenerator");
  document.title = tr("tab");
}

function animateScoreDial(root) {
  const dial = root.querySelector(".score-dial");
  if (!dial) return;
  const scoreNumber = dial.querySelector(".score-number");
  const rawTarget = Number(dial.dataset.scoreTarget || 0);
  const target = Number.isFinite(rawTarget) ? Math.max(0, Math.min(100, rawTarget)) : 0;

  const reducedMotion =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reducedMotion) {
    dial.style.setProperty("--score", `${target}`);
    if (scoreNumber) scoreNumber.textContent = `${Math.round(target)}`;
    return;
  }

  dial.style.setProperty("--score", "0");
  if (scoreNumber) scoreNumber.textContent = "0";

  const durationMs = 1200;
  const start = performance.now();
  const easing = (value) => 1 - (1 - value) ** 3;

  const frame = (now) => {
    const progress = Math.min((now - start) / durationMs, 1);
    const value = target * easing(progress);
    dial.style.setProperty("--score", value.toFixed(2));
    if (scoreNumber) scoreNumber.textContent = `${Math.round(value)}`;
    if (progress < 1) requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}

function statusLabel(status) {
  if (status === "pass") return tr("pass");
  if (status === "warn") return tr("warn");
  if (status === "fail") return tr("fail");
  return String(status || "").toUpperCase();
}

function categoryName(category) {
  const id = String(category.id || "").toLowerCase();
  const byId = CATEGORY_NAME_BY_ID[id];
  if (byId) return byId[lang];
  return String(category.name || id || "Category");
}

function normalizeReportFromApiResponse(payload, repoUrl) {
  if (!payload || typeof payload !== "object") return null;
  const quality = payload.quality && typeof payload.quality === "object" ? payload.quality : null;
  if (!quality) return null;

  if (quality.report && typeof quality.report === "object") {
    return quality.report;
  }

  const categories = Array.isArray(quality.category_scores)
    ? quality.category_scores.map((item) => ({
        id: item.id || "unknown",
        name: item.name || String(item.id || "Unknown"),
        score: Number(item.score || 0),
        weight: Number(item.weight || 0),
        checks: [],
        recommendations: [],
      }))
    : [];

  return {
    repo_url: repoUrl,
    score_total: Number(quality.score_total || 0),
    project_metrics: {
      total_code_lines: Number(quality.total_code_lines || 0),
      total_code_files: Number(quality.total_code_files || 0),
      scanned_code_files: Number(quality.scanned_code_files || 0),
      sampled: false,
      by_extension: [],
    },
    detected_stacks: Array.isArray(quality.detected_stacks) ? quality.detected_stacks : [],
    categories,
  };
}

function renderReport(report, repoUrl, jsonHref) {
  const categories = Array.isArray(report.categories) ? report.categories : [];
  const metrics = report.project_metrics && typeof report.project_metrics === "object" ? report.project_metrics : {};
  const stacks = Array.isArray(report.detected_stacks) ? report.detected_stacks : [];

  let passCount = 0;
  let warnCount = 0;
  let failCount = 0;
  categories.forEach((category) => {
    const checks = Array.isArray(category.checks) ? category.checks : [];
    checks.forEach((check) => {
      if (check.status === "pass") passCount += 1;
      if (check.status === "warn") warnCount += 1;
      if (check.status === "fail") failCount += 1;
    });
  });

  const categoriesHtml = categories
    .map((category) => {
      const weight = Number(category.weight || 0);
      const score = Number(category.score || 0);
      const pct = weight > 0 ? Math.max(0, Math.min(100, Math.round((score / weight) * 100))) : 0;
      const checks = Array.isArray(category.checks) ? category.checks : [];
      const recommendations = Array.isArray(category.recommendations) ? category.recommendations : [];

      const checksHtml = checks
        .map(
          (check) => `
            <li class="check-item" data-status="${escapeHtml(check.status || "")}">
              <span class="badge ${escapeHtml(check.status || "warn")}">${escapeHtml(statusLabel(check.status))}</span>
              <div>
                <p class="check-name">${escapeHtml(check.name || "")}</p>
                <p class="muted">${escapeHtml(check.details || "")}</p>
              </div>
            </li>`
        )
        .join("");

      const recHtml = recommendations.length
        ? `
          <h3>${escapeHtml(tr("recommendations"))}</h3>
          <ul class="recommendations">${recommendations.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
        : "";

      return `
        <section class="card category-card span-6">
          <div class="category-head">
            <h2>${escapeHtml(categoryName(category))}</h2>
            <span class="category-score">${score}/${weight}</span>
          </div>
          <div class="progress-track"><div class="progress-fill" style="width:${pct}%">${pct}%</div></div>
          <ul class="checks">${checksHtml}</ul>
          ${recHtml}
        </section>`;
    })
    .join("");

  const byExt = Array.isArray(metrics.by_extension) ? metrics.by_extension : [];
  const byExtHtml = byExt.length
    ? `
      <section class="card lines-card span-6">
        <div class="category-head"><h2>${escapeHtml(tr("codeLines"))}</h2></div>
        <ul class="checks">
          ${byExt
            .map(
              (item) => `
            <li class="check-item">
              <span class="pill">${escapeHtml(item.extension || "")}</span>
              <div>
                <p class="check-name">${Number(item.lines || 0)}</p>
                <p class="muted">${Number(item.files || 0)} files</p>
              </div>
            </li>`
            )
            .join("")}
        </ul>
      </section>`
    : "";

  const sampledNote = metrics.sampled ? `<p class="muted">${escapeHtml(tr("sampledNote"))}</p>` : "";
  const stackHtml = stacks.length
    ? stacks.map((stack) => `<span class="pill">${escapeHtml(stack)}</span>`).join("")
    : `<span class="pill">${escapeHtml(tr("noStacks"))}</span>`;

  refs.reportRoot.innerHTML = `
    <section class="card report-top span-12">
      <div class="report-summary-grid">
        <div>
          <p class="kicker">${escapeHtml(tr("reportTitle"))}</p>
          <h1>${escapeHtml(tr("reportRepo"))}: <a class="link" href="${escapeHtml(repoUrl)}" target="_blank" rel="noopener">${escapeHtml(repoUrl)}</a></h1>
          <div class="status-overview">
            <span class="status-chip pass"><strong>${passCount}</strong> ${escapeHtml(tr("pass"))}</span>
            <span class="status-chip warn"><strong>${warnCount}</strong> ${escapeHtml(tr("warn"))}</span>
            <span class="status-chip fail"><strong>${failCount}</strong> ${escapeHtml(tr("fail"))}</span>
          </div>
          <div class="metric-grid">
            <div class="metric-card"><span class="metric-title">${escapeHtml(tr("codeLines"))}</span><span class="metric-value">${Number(metrics.total_code_lines || 0)}</span></div>
            <div class="metric-card"><span class="metric-title">${escapeHtml(tr("codeFiles"))}</span><span class="metric-value">${Number(metrics.total_code_files || 0)}</span></div>
            <div class="metric-card"><span class="metric-title">${escapeHtml(tr("scanned"))}</span><span class="metric-value">${Number(metrics.scanned_code_files || 0)}</span></div>
          </div>
          ${sampledNote}
          <div class="pill-row">${stackHtml}</div>
          <div class="actions">
            <a class="button secondary" href="${escapeHtml(jsonHref)}" target="_blank" rel="noopener">${escapeHtml(tr("downloadJson"))}</a>
            <a class="button" href="./index.html">${escapeHtml(tr("checkAgain"))}</a>
          </div>
          <label class="toggle"><input id="issues-only" type="checkbox"> ${escapeHtml(tr("showOnlyIssues"))}</label>
        </div>
        <aside class="score-panel">
          <div class="score-dial" data-score-target="${Number(report.score_total || 0)}" style="--score:0">
            <div class="score-dial-inner">
              <span class="score-number">0</span>
              <span class="score-max">/100</span>
            </div>
          </div>
          <p class="score-label">${escapeHtml(tr("totalScore"))}</p>
        </aside>
      </div>
    </section>
    ${byExtHtml}
    ${categoriesHtml}
  `;

  const toggle = document.getElementById("issues-only");
  const checks = Array.from(refs.reportRoot.querySelectorAll(".check-item[data-status]"));
  if (toggle) {
    toggle.addEventListener("change", () => {
      const onlyIssues = toggle.checked;
      checks.forEach((node) => {
        const status = node.getAttribute("data-status") || "";
        node.classList.toggle("hidden", onlyIssues && status === "pass");
      });
      refs.reportRoot.querySelectorAll(".category-card").forEach((section) => {
        const visible = section.querySelectorAll(".check-item[data-status]:not(.hidden)").length;
        section.classList.toggle("category-empty", visible === 0);
      });
    });
  }

  animateScoreDial(refs.reportRoot);
  initRevealAnimations();
}

async function loadFromLocalReports(parsed, repoUrl) {
  const fileName = `${parsed.owner}__${parsed.repo}.${lang}.json`;
  const path = `./reports/${fileName}`;
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(tr("noReport"));
  }
  const report = await response.json();
  return { report, jsonHref: path };
}

async function loadFromRemoteApi(parsed, repoUrl) {
  const endpoint = `${API_BASE}/api?owner=${encodeURIComponent(parsed.owner)}&repo=${encodeURIComponent(parsed.repo)}&kind=quality&format=json&include_report=true&locale=${encodeURIComponent(lang)}`;
  const response = await fetch(endpoint, { cache: "no-store" });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || tr("noReport"));
  }
  const payload = await response.json();
  const report = normalizeReportFromApiResponse(payload, repoUrl);
  if (!report) {
    throw new Error(tr("noReport"));
  }
  return { report, jsonHref: endpoint };
}

async function loadReport(repoUrl) {
  const parsed = parseRepoUrl(repoUrl);
  if (!parsed) {
    refs.error.textContent = tr("invalidUrl");
    return;
  }

  refs.error.textContent = tr("loading");
  refs.reportRoot.innerHTML = "";
  refs.actionHelp.classList.add("hidden");

  try {
    const loaded = USE_REMOTE_API
      ? await loadFromRemoteApi(parsed, repoUrl)
      : await loadFromLocalReports(parsed, repoUrl);
    refs.error.textContent = tr("reportReady");
    renderReport(loaded.report, repoUrl, loaded.jsonHref);
  } catch (error) {
    refs.error.textContent = error instanceof Error ? error.message : tr("noReport");
    renderHelp(repoUrl);
  }
}

refs.langSwitch.querySelectorAll(".link").forEach((node) => {
  node.addEventListener("click", (event) => {
    event.preventDefault();
    lang = node.dataset.lang || "en";
    applyLangSwitch();
  });
});

refs.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const repoUrl = String(refs.input.value || "").trim();
  await loadReport(repoUrl);
});

applyLangSwitch();
initRevealAnimations();
