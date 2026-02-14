const CLIENT_I18N_DEFAULT = {
  status: {
    en: { queued: "queued", running: "running", done: "done", failed: "failed" },
    ru: { queued: "в очереди", running: "выполняется", done: "завершено", failed: "ошибка" },
  },
  text: {
    en: {
      enterRepoUrl: "Please enter a repository URL.",
      failedToStart: "Failed to start scan.",
      failedToFetch: "Failed to fetch job status.",
      scanFailed: "Scan failed.",
      noTrend: "Not enough data for trend.",
      trendAria: "Score trend",
      notAvailable: "n/a",
      none: "None",
      failedToLoadJson: "Failed to load JSON",
      privateRepoTokenPrompt:
        "Repository not found. If it is private, provide a GitHub token and try again. Token is not stored.",
      invalidGeneratorRepoUrl: "Enter a valid GitHub URL like https://github.com/owner/repo",
      apiLabelReportJson: "Report JSON",
      apiLabelReportMarkdown: "Report Markdown",
      apiLabelReportText: "Report TXT",
      apiLabelHistory: "Repo history",
      apiLabelLatest: "Repo latest",
      apiLabelStatsJson: "Repository stats JSON",
      apiLabelStatsSvg: "Repository stats SVG",
      apiLabelQualityJson: "Quality stats JSON",
      apiLabelQualitySvg: "Quality stats SVG",
      apiLabelHealth: "Health",
      apiLabelMetrics: "Metrics",
      copy: "Copy",
      copied: "Copied",
    },
    ru: {
      enterRepoUrl: "Введите ссылку на репозиторий.",
      failedToStart: "Не удалось запустить проверку.",
      failedToFetch: "Не удалось получить статус задачи.",
      scanFailed: "Проверка завершилась с ошибкой.",
      noTrend: "Недостаточно данных для графика.",
      trendAria: "Тренд оценки",
      notAvailable: "н/д",
      none: "Ничего",
      failedToLoadJson: "Не удалось загрузить JSON",
      apiLabelReportJson: "Отчет JSON",
      apiLabelReportMarkdown: "Отчет Markdown",
      apiLabelReportText: "Отчет TXT",
      apiLabelHistory: "История репозитория",
      apiLabelLatest: "Последний отчет репозитория",
      apiLabelStatsJson: "Статистика репозитория JSON",
      apiLabelStatsSvg: "Статистика репозитория SVG",
      apiLabelQualityJson: "Статистика оценки JSON",
      apiLabelQualitySvg: "Статистика оценки SVG",
      apiLabelHealth: "Состояние сервиса",
      apiLabelMetrics: "Метрики сервиса",
      copy: "Копировать",
      copied: "Скопировано",
    },
  },
};

function readClientI18n() {
  const node = document.getElementById("i18n-client");
  if (!node) return CLIENT_I18N_DEFAULT;
  try {
    const parsed = JSON.parse(node.textContent || "{}");
    if (!parsed || typeof parsed !== "object") return CLIENT_I18N_DEFAULT;
    return {
      status: parsed.status || CLIENT_I18N_DEFAULT.status,
      text: parsed.text || CLIENT_I18N_DEFAULT.text,
    };
  } catch {
    return CLIENT_I18N_DEFAULT;
  }
}

const CLIENT_I18N = readClientI18n();
const STATUS_I18N = CLIENT_I18N.status || CLIENT_I18N_DEFAULT.status;
const TEXT_I18N = CLIENT_I18N.text || CLIENT_I18N_DEFAULT.text;
const GENERATOR_THEME_KEYS = [
  "bg_start",
  "bg_end",
  "border",
  "panel",
  "overlay",
  "chip_bg",
  "chip_text",
  "text",
  "muted",
  "accent",
  "accent_2",
  "accent_soft",
  "track",
  "pass",
  "warn",
  "fail",
];
const HEX_COLOR_RE = /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;

function t(lang, key) {
  const dict = TEXT_I18N[lang] || TEXT_I18N.en;
  return dict[key] || TEXT_I18N.en[key] || key;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

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

async function postScan(repoUrl, githubToken = "") {
  const body = { repo_url: repoUrl };
  const token = String(githubToken || "").trim();
  if (token) body.github_token = token;
  const response = await fetch("/api/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok) {
    const error = new Error(payload.detail || "Failed to start scan.");
    error.status = response.status;
    throw error;
  }
  return payload;
}

async function fetchJob(jobId, lang) {
  const response = await fetch(`/api/jobs/${jobId}?lang=${encodeURIComponent(lang)}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || t(lang, "failedToFetch"));
  }
  return payload;
}

function initIndexPage() {
  const form = document.getElementById("scan-form");
  const errorEl = document.getElementById("form-error");
  const tokenPanel = document.getElementById("token-panel");
  const tokenInput = document.getElementById("github_token");
  const lang = document.body.dataset.lang || "en";
  if (!form || !errorEl) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorEl.textContent = "";
    const formData = new FormData(form);
    const repoUrl = String(formData.get("repo_url") || "").trim();
    const githubToken = String(formData.get("github_token") || "").trim();
    if (!repoUrl) {
      errorEl.textContent = t(lang, "enterRepoUrl");
      return;
    }

    try {
      const payload = await postScan(repoUrl, githubToken);
      window.location.href = `/jobs/${payload.job_id}?lang=${encodeURIComponent(lang)}`;
    } catch (error) {
      const status = error && typeof error === "object" ? Number(error.status || 0) : 0;
      if (status === 404 && tokenPanel) {
        tokenPanel.classList.remove("hidden");
        if (!githubToken) {
          errorEl.textContent = t(lang, "privateRepoTokenPrompt");
          if (tokenInput) tokenInput.focus();
          return;
        }
      }
      errorEl.textContent = error instanceof Error ? error.message : t(lang, "failedToStart");
    }
  });
}

function initProgressPage() {
  const body = document.body;
  const jobId = body.dataset.jobId;
  const lang = body.dataset.lang || "en";
  const statusLabel = body.dataset.statusLabel || "Status";
  const statusEl = document.getElementById("status-line");
  const progressEl = document.getElementById("job-progress");
  const errorEl = document.getElementById("job-error");
  if (!jobId || !statusEl || !progressEl || !errorEl) return;

  const timer = setInterval(async () => {
    try {
      const payload = await fetchJob(jobId, lang);
      const localizedStatus = (STATUS_I18N[lang] && STATUS_I18N[lang][payload.status]) || payload.status;
      statusEl.textContent = `${statusLabel}: ${localizedStatus}`;
      const progress = Number(payload.progress || 0);
      progressEl.style.width = `${progress}%`;
      progressEl.textContent = `${progress}%`;
      if (payload.status === "done") {
        clearInterval(timer);
        window.location.href = `/report/${jobId}?lang=${encodeURIComponent(lang)}`;
      }
      if (payload.status === "failed") {
        clearInterval(timer);
        errorEl.textContent = payload.error_message || t(lang, "scanFailed");
      }
    } catch (error) {
      clearInterval(timer);
      errorEl.textContent = error instanceof Error ? error.message : t(lang, "failedToFetch");
    }
  }, 1000);
}

function parseInlineHistory() {
  const node = document.getElementById("history-data");
  if (!node) return [];
  try {
    const parsed = JSON.parse(node.textContent || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

async function fetchRepoHistory(owner, repo) {
  if (!owner || !repo) return null;
  try {
    const response = await fetch(`/api/repos/${encodeURIComponent(owner)}/${encodeURIComponent(repo)}/history`);
    if (!response.ok) return null;
    const payload = await response.json();
    return Array.isArray(payload.history) ? payload.history : null;
  } catch {
    return null;
  }
}

function buildSmoothPath(points) {
  if (!points.length) return "";
  let path = `M ${points[0].x} ${points[0].y}`;
  for (let i = 1; i < points.length; i += 1) {
    const prev = points[i - 1];
    const current = points[i];
    const cx = (prev.x + current.x) / 2;
    path += ` C ${cx} ${prev.y}, ${cx} ${current.y}, ${current.x} ${current.y}`;
  }
  return path;
}

function renderTrendChart(root, history, lastScoreLabel, lang, fallbackEl) {
  if (!Array.isArray(history) || history.length < 2) {
    if (fallbackEl) fallbackEl.classList.remove("hidden");
    root.innerHTML = "";
    return;
  }
  if (fallbackEl) fallbackEl.classList.add("hidden");

  const width = 1020;
  const height = 300;
  const padX = 42;
  const padY = 32;
  const min = 0;
  const max = 100;
  const yLines = [0, 25, 50, 75, 100];

  const points = history.map((item, index) => {
    const x = padX + (index * (width - padX * 2)) / Math.max(history.length - 1, 1);
    const y = height - padY - ((Number(item.score_total || 0) - min) * (height - padY * 2)) / (max - min);
    return { x, y, item };
  });

  const linePath = buildSmoothPath(points);
  const baselineY = height - padY;
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${baselineY} L ${points[0].x} ${baselineY} Z`;
  const step = Math.max(1, Math.ceil(points.length / 9));

  const grid = yLines
    .map((value) => {
      const y = height - padY - ((value - min) * (height - padY * 2)) / (max - min);
      return `
        <line x1="${padX}" y1="${y}" x2="${width - padX}" y2="${y}" class="trend-grid-line"></line>
        <text x="${padX - 8}" y="${y + 4}" text-anchor="end" class="trend-axis-label">${value}</text>
      `;
    })
    .join("");

  const xLabels = points
    .map((point, index) => {
      if (index % step !== 0 && index !== points.length - 1) return "";
      const label = point.item.commit_short || t(lang, "notAvailable");
      return `<text x="${point.x}" y="${height - 8}" text-anchor="middle" class="trend-axis-label">${escapeHtml(label)}</text>`;
    })
    .join("");

  const circles = points
    .map((point) => {
      const commit = point.item.commit_short || t(lang, "notAvailable");
      const score = Number(point.item.score_total || 0);
      const delta = Number(point.item.delta || 0);
      const deltaText = delta > 0 ? `+${delta}` : String(delta);
      return `
        <circle cx="${point.x}" cy="${point.y}" r="4.4" class="trend-point">
          <title>${escapeHtml(commit)} | ${score}/100 | Δ ${deltaText}</title>
        </circle>
      `;
    })
    .join("");

  const last = history[history.length - 1];
  const lastCommit = last.commit_short || t(lang, "notAvailable");

  root.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(t(lang, "trendAria"))}">
      <defs>
        <linearGradient id="trend-area-gradient" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.36"></stop>
          <stop offset="100%" stop-color="#22d3ee" stop-opacity="0.02"></stop>
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="${width}" height="${height}" fill="transparent"></rect>
      ${grid}
      <path d="${areaPath}" class="trend-area"></path>
      <path d="${linePath}" class="trend-line"></path>
      ${circles}
      ${xLabels}
    </svg>
    <p class="muted">${lastScoreLabel}: ${last.score_total}/100 (${lastCommit})</p>
  `;

  const line = root.querySelector(".trend-line");
  if (line && typeof line.getTotalLength === "function") {
    const length = line.getTotalLength();
    line.style.strokeDasharray = `${length}`;
    line.style.strokeDashoffset = `${length}`;
    requestAnimationFrame(() => {
      line.style.strokeDashoffset = "0";
    });
  }
}

function apiRows(owner, repo, jobId, lang) {
  const base = "";
  const ownerEnc = encodeURIComponent(owner);
  const repoEnc = encodeURIComponent(repo);
  return [
    { label: t(lang, "apiLabelReportJson"), path: `${base}/api/report/${jobId}.json?lang=${encodeURIComponent(lang)}` },
    { label: t(lang, "apiLabelReportMarkdown"), path: `${base}/api/report/${jobId}.md?lang=${encodeURIComponent(lang)}` },
    { label: t(lang, "apiLabelReportText"), path: `${base}/api/report/${jobId}.txt?lang=${encodeURIComponent(lang)}` },
    { label: t(lang, "apiLabelHistory"), path: `${base}/api/repos/${ownerEnc}/${repoEnc}/history` },
    { label: t(lang, "apiLabelLatest"), path: `${base}/api/repos/${ownerEnc}/${repoEnc}/latest` },
    {
      label: t(lang, "apiLabelStatsJson"),
      path: `${base}/api/stats/repo/${ownerEnc}/${repoEnc}.json?langs_count=8`,
    },
    {
      label: t(lang, "apiLabelStatsSvg"),
      path: `${base}/api/stats/repo/${ownerEnc}/${repoEnc}.svg?theme=ocean&langs_count=5&animate=true&animation=all`,
    },
    {
      label: t(lang, "apiLabelQualityJson"),
      path: `${base}/api/stats/quality/${ownerEnc}/${repoEnc}.json`,
    },
    {
      label: t(lang, "apiLabelQualitySvg"),
      path: `${base}/api/stats/quality/${ownerEnc}/${repoEnc}.svg?theme=ocean&animate=true&animation=ring`,
    },
    { label: t(lang, "apiLabelHealth"), path: `${base}/health` },
    { label: t(lang, "apiLabelMetrics"), path: `${base}/metrics` },
  ];
}

function debounce(fn, timeoutMs) {
  let timer = null;
  return (...args) => {
    if (timer) window.clearTimeout(timer);
    timer = window.setTimeout(() => fn(...args), timeoutMs);
  };
}

function parseGeneratorRepoRef(value) {
  const input = String(value || "").trim();
  if (!input) return null;

  const urlMatch = input.match(/^https?:\/\/github\.com\/([^/\s]+)\/([^/\s?#]+)(?:[/?#].*)?$/i);
  if (urlMatch) {
    const owner = urlMatch[1];
    const repo = urlMatch[2].replace(/\.git$/i, "");
    return owner && repo ? { owner, repo } : null;
  }

  const shortMatch = input.match(/^([^/\s]+)\/([^/\s]+)$/);
  if (shortMatch) {
    const owner = shortMatch[1];
    const repo = shortMatch[2].replace(/\.git$/i, "");
    return owner && repo ? { owner, repo } : null;
  }

  return null;
}

function normalizeHexColor(value) {
  const raw = String(value || "").trim();
  if (!HEX_COLOR_RE.test(raw)) return null;
  if (raw.length === 4) {
    return `#${raw[1]}${raw[1]}${raw[2]}${raw[2]}${raw[3]}${raw[3]}`.toUpperCase();
  }
  return raw.toUpperCase();
}

function generatorCustomThemeParams() {
  const result = {};
  GENERATOR_THEME_KEYS.forEach((key) => {
    const node = document.getElementById(`gen-color-${key}`);
    const value = normalizeHexColor(node?.value || "");
    if (value) result[key] = value;
  });
  return result;
}

function syncGeneratorCustomThemeVisibility() {
  const theme = document.getElementById("gen-theme")?.value || "ocean";
  const format = document.getElementById("gen-format")?.value || "svg";
  const panel = document.getElementById("gen-custom-theme-panel");
  const show = theme === "custom" && format === "svg";
  if (!panel) return;
  panel.classList.toggle("hidden", !show);
  GENERATOR_THEME_KEYS.forEach((key) => {
    const node = document.getElementById(`gen-color-${key}`);
    if (!node) return;
    node.disabled = !show;
  });
}

function selectedGeneratorHideFlags() {
  return Array.from(document.querySelectorAll(".gen-hide-option:checked:not(:disabled)"))
    .map((node) => String(node.value || "").trim())
    .filter(Boolean);
}

function syncGeneratorHideField() {
  const hiddenInput = document.getElementById("gen-hide");
  const summaryNode = document.getElementById("gen-hide-summary-text");
  const lang = document.body.dataset.lang || "en";
  if (!hiddenInput) return;
  const selected = selectedGeneratorHideFlags();
  hiddenInput.value = selected.join(",");
  if (summaryNode) {
    summaryNode.textContent = selected.length ? selected.join(", ") : t(lang, "none");
  }
}

function syncGeneratorHideOptionsByKind() {
  const kind = document.getElementById("gen-kind")?.value || "repo";
  const options = Array.from(document.querySelectorAll(".gen-hide-option"));
  options.forEach((input) => {
    const allowed = String(input.dataset.kinds || "repo,quality")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    const isSupported = allowed.includes(kind);
    input.disabled = !isSupported;
    if (!isSupported) input.checked = false;
    input.closest(".multi-select-option")?.classList.toggle("is-disabled", !isSupported);
  });
  syncGeneratorHideField();
}

function buildGeneratorPath() {
  const owner = (document.getElementById("gen-owner")?.value || "").trim();
  const repo = (document.getElementById("gen-repo")?.value || "").trim();
  const kind = document.getElementById("gen-kind")?.value || "repo";
  const format = document.getElementById("gen-format")?.value || "svg";
  if (!owner || !repo) return "";

  const theme = document.getElementById("gen-theme")?.value || "ocean";
  const locale = document.getElementById("gen-locale")?.value || "en";
  const title = (document.getElementById("gen-title")?.value || "").trim();
  const hide = (document.getElementById("gen-hide")?.value || "").trim();
  const width = Number(document.getElementById("gen-width")?.value || 760);
  const langs = Number(document.getElementById("gen-langs")?.value || 4);
  const animate = Boolean(document.getElementById("gen-animate")?.checked);
  const animation = document.getElementById("gen-animation")?.value || "all";
  const duration = Number(document.getElementById("gen-duration")?.value || 1400);

  const ownerEnc = encodeURIComponent(owner);
  const repoEnc = encodeURIComponent(repo);
  const params = new URLSearchParams();
  let path = `/api/stats/${kind}/${ownerEnc}/${repoEnc}.${format}`;

  if (format === "svg") {
    params.set("theme", theme);
    params.set("locale", locale);
    params.set("card_width", String(Math.max(640, Math.min(1400, width))));
    if (title) params.set("title", title);
    if (hide) params.set("hide", hide);
    params.set("animate", animate ? "true" : "false");
    params.set("animation", animation);
    params.set("duration", String(Math.max(350, Math.min(7000, duration))));
    if (kind === "repo") params.set("langs_count", String(Math.max(1, Math.min(10, langs))));
    if (theme === "custom") {
      const custom = generatorCustomThemeParams();
      Object.entries(custom).forEach(([key, value]) => {
        params.set(key, value);
      });
    }
  } else if (kind === "repo") {
    params.set("langs_count", String(Math.max(1, Math.min(30, langs))));
  }

  const qs = params.toString();
  if (qs) path += `?${qs}`;
  return path;
}

async function refreshGeneratorPreview() {
  const lang = document.body.dataset.lang || "en";
  const urlNode = document.getElementById("gen-url");
  const mdNode = document.getElementById("gen-md");
  const image = document.getElementById("gen-preview-image");
  const jsonNode = document.getElementById("gen-preview-json");
  const svgWrap = document.getElementById("gen-svg-wrap");
  const openNode = document.getElementById("gen-open-url");
  const format = document.getElementById("gen-format")?.value || "svg";
  if (!urlNode || !mdNode || !image || !jsonNode || !svgWrap || !openNode) return;

  const path = buildGeneratorPath();
  if (!path) {
    urlNode.value = "";
    mdNode.value = "";
    svgWrap.classList.remove("hidden");
    jsonNode.classList.add("hidden");
    image.removeAttribute("src");
    jsonNode.textContent = "";
    openNode.setAttribute("href", "#");
    return;
  }

  const absolute = `${window.location.origin}${path}`;
  urlNode.value = absolute;
  openNode.setAttribute("href", absolute);

  if (format === "svg") {
    mdNode.value = `![Repo Inspector Card](${absolute})`;
    svgWrap.classList.remove("hidden");
    jsonNode.classList.add("hidden");
    image.src = `${absolute}${absolute.includes("?") ? "&" : "?"}_ts=${Date.now()}`;
    return;
  }

  mdNode.value = "";
  svgWrap.classList.add("hidden");
  jsonNode.classList.remove("hidden");
  try {
    const response = await fetch(absolute);
    const payload = await response.json();
    jsonNode.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    jsonNode.textContent = error instanceof Error ? error.message : t(lang, "failedToLoadJson");
  }
}

function initGeneratorPage() {
  const lang = document.body.dataset.lang || "en";
  const required = [
    "gen-owner",
    "gen-repo",
    "gen-kind",
    "gen-format",
    "gen-theme",
    "gen-locale",
    "gen-title",
    "gen-hide",
    "gen-width",
    "gen-langs",
    "gen-animate",
    "gen-animation",
    "gen-duration",
    "gen-copy-url",
    "gen-copy-md",
  ];
  if (required.some((id) => !document.getElementById(id))) return;

  const controls = required
    .map((id) => document.getElementById(id))
    .filter((node) => node && node.tagName !== "BUTTON");
  const delayedPreview = debounce(() => {
    void refreshGeneratorPreview();
  }, 180);
  controls.forEach((node) => {
    node.addEventListener("input", delayedPreview);
    node.addEventListener("change", delayedPreview);
  });
  GENERATOR_THEME_KEYS.forEach((key) => {
    const node = document.getElementById(`gen-color-${key}`);
    if (!node) return;
    node.addEventListener("input", delayedPreview);
    node.addEventListener("change", delayedPreview);
  });
  document.querySelectorAll(".gen-hide-option").forEach((node) => {
    node.addEventListener("change", () => {
      syncGeneratorHideField();
      delayedPreview();
    });
  });
  document.getElementById("gen-theme")?.addEventListener("change", () => {
    syncGeneratorCustomThemeVisibility();
  });
  document.getElementById("gen-format")?.addEventListener("change", () => {
    syncGeneratorCustomThemeVisibility();
  });
  document.getElementById("gen-kind")?.addEventListener("change", () => {
    syncGeneratorHideOptionsByKind();
  });
  const hidePanel = document.getElementById("gen-hide-panel");
  document.addEventListener("click", (event) => {
    if (!hidePanel) return;
    if (!hidePanel.contains(event.target)) hidePanel.removeAttribute("open");
  });

  const copyUrl = document.getElementById("gen-copy-url");
  const copyMd = document.getElementById("gen-copy-md");
  const urlNode = document.getElementById("gen-url");
  const mdNode = document.getElementById("gen-md");
  const importInput = document.getElementById("gen-repo-url");
  const importButton = document.getElementById("gen-import-repo");
  const importError = document.getElementById("gen-import-error");
  const ownerNode = document.getElementById("gen-owner");
  const repoNode = document.getElementById("gen-repo");

  const applyRepoImport = () => {
    const parsed = parseGeneratorRepoRef(importInput?.value || "");
    if (!parsed) {
      if (importError) importError.textContent = t(lang, "invalidGeneratorRepoUrl");
      return;
    }
    if (ownerNode) ownerNode.value = parsed.owner;
    if (repoNode) repoNode.value = parsed.repo;
    if (importError) importError.textContent = "";
    delayedPreview();
  };

  importButton?.addEventListener("click", applyRepoImport);
  importInput?.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    applyRepoImport();
  });
  importInput?.addEventListener("input", () => {
    if (importError) importError.textContent = "";
  });

  copyUrl?.addEventListener("click", async () => {
    const text = urlNode?.value || "";
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Ignore clipboard errors for unsupported environments.
    }
  });

  copyMd?.addEventListener("click", async () => {
    const text = mdNode?.value || "";
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Ignore clipboard errors for unsupported environments.
    }
  });

  syncGeneratorHideOptionsByKind();
  syncGeneratorCustomThemeVisibility();
  void refreshGeneratorPreview();
}

function renderApiEndpoints(owner, repo, jobId, lang) {
  const root = document.getElementById("api-endpoints");
  if (!root || !owner || !repo || !jobId) return;
  const rows = apiRows(owner, repo, jobId, lang);
  root.innerHTML = rows
    .map(
      (row, index) => `
      <div class="api-row" style="--row-delay:${Math.min(index * 35, 240)}ms">
        <div class="api-label">${escapeHtml(row.label)}</div>
        <a class="api-path link" href="${escapeHtml(row.path)}" target="_blank" rel="noopener">${escapeHtml(row.path)}</a>
        <button class="api-copy" type="button" data-copy="${escapeHtml(row.path)}">${t(lang, "copy")}</button>
      </div>
    `
    )
    .join("");

  root.querySelectorAll(".api-copy").forEach((node) => {
    node.addEventListener("click", async () => {
      const value = node.getAttribute("data-copy") || "";
      try {
        await navigator.clipboard.writeText(value);
        const before = node.textContent;
        node.textContent = t(lang, "copied");
        window.setTimeout(() => {
          node.textContent = before || t(lang, "copy");
        }, 1100);
      } catch {
        node.textContent = t(lang, "copy");
      }
    });
  });
}

function animateScoreDial() {
  const dial = document.querySelector(".score-dial");
  if (!dial) return;
  const scoreNumber = dial.querySelector(".score-number");
  const rawTarget = Number(dial.dataset.scoreTarget || 0);
  const target = Number.isFinite(rawTarget) ? Math.max(0, Math.min(100, rawTarget)) : 0;
  const reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (reducedMotion) {
    dial.style.setProperty("--score", `${target}`);
    if (scoreNumber) scoreNumber.textContent = `${Math.round(target)}`;
    return;
  }

  dial.style.setProperty("--score", "0");
  if (scoreNumber) scoreNumber.textContent = "0";

  const durationMs = 1200;
  const start = performance.now();
  const easing = (value) => 1 - Math.pow(1 - value, 3);
  const frame = (now) => {
    const progress = Math.min((now - start) / durationMs, 1);
    const value = target * easing(progress);
    dial.style.setProperty("--score", value.toFixed(2));
    if (scoreNumber) scoreNumber.textContent = `${Math.round(value)}`;
    if (progress < 1) {
      requestAnimationFrame(frame);
    } else {
      dial.style.setProperty("--score", `${target}`);
      if (scoreNumber) scoreNumber.textContent = `${Math.round(target)}`;
    }
  };
  requestAnimationFrame(frame);
}

async function initReportPage() {
  const body = document.body;
  const lang = body.dataset.lang || "en";
  const owner = body.dataset.repoOwner || "";
  const repo = body.dataset.repoName || "";
  const jobId = body.dataset.jobId || "";
  const root = document.getElementById("trend-chart");
  const fallbackEl = document.getElementById("trend-fallback");
  const lastScoreLabel = body.dataset.lastScoreLabel || "Last score";

  let history = parseInlineHistory();
  const fromApi = await fetchRepoHistory(owner, repo);
  if (Array.isArray(fromApi) && fromApi.length) {
    history = fromApi;
  }
  if (root) {
    renderTrendChart(root, history, lastScoreLabel, lang, fallbackEl);
  }
  animateScoreDial();
  renderApiEndpoints(owner, repo, jobId, lang);

  const checks = Array.from(document.querySelectorAll(".check-item"));
  const passCountEl = document.getElementById("pass-count");
  const warnCountEl = document.getElementById("warn-count");
  const failCountEl = document.getElementById("fail-count");
  const issuesOnlyToggle = document.getElementById("issues-only");

  if (checks.length) {
    let passCount = 0;
    let warnCount = 0;
    let failCount = 0;
    checks.forEach((node) => {
      const status = node.getAttribute("data-status") || "";
      if (status === "pass") passCount += 1;
      if (status === "warn") warnCount += 1;
      if (status === "fail") failCount += 1;
    });
    if (passCountEl) passCountEl.textContent = String(passCount);
    if (warnCountEl) warnCountEl.textContent = String(warnCount);
    if (failCountEl) failCountEl.textContent = String(failCount);
  }

  if (issuesOnlyToggle) {
    issuesOnlyToggle.addEventListener("change", () => {
      const issuesOnly = issuesOnlyToggle.checked;
      checks.forEach((node) => {
        const status = node.getAttribute("data-status");
        const hidden = issuesOnly && status === "pass";
        node.classList.toggle("hidden", hidden);
      });
      document.querySelectorAll(".category-card").forEach((section) => {
        const visibleChecks = section.querySelectorAll(".check-item:not(.hidden)");
        section.classList.toggle("category-empty", visibleChecks.length === 0);
      });
    });
  }
}

const page = document.body.dataset.page;
initRevealAnimations();
if (page === "index") initIndexPage();
if (page === "progress") initProgressPage();
if (page === "report") initReportPage();
if (page === "generator") initGeneratorPage();

