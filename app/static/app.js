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
      all: "All",
      failedToLoadJson: "Failed to load JSON",
      privateRepoTokenPrompt:
        "Repository not found. If it is private, provide a GitHub token and try again. Token is not stored.",
      invalidGeneratorRepoUrl:
        "Enter a valid GitHub URL, stats API URL, or Markdown embed like ![...](https://.../api?...).",
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
      all: "Все",
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
const GENERATOR_SVG_ONLY_IDS = [
  "gen-theme",
  "gen-title",
  "gen-hide",
  "gen-width",
  "gen-animate",
  "gen-animation",
  "gen-duration",
  "gen-cache-seconds",
];
const GENERATOR_JSON_FIELDS = {
  repo: [
    "owner",
    "name",
    "full_name",
    "html_url",
    "description",
    "stars",
    "forks",
    "open_issues",
    "watchers",
    "default_branch",
    "primary_language",
    "license_name",
    "topics",
    "archived",
    "is_fork",
    "size_kb",
    "created_at",
    "updated_at",
    "pushed_at",
    "homepage",
    "has_releases",
    "has_tags",
    "languages",
    "language_total_bytes",
  ],
  quality: [
    "job_id",
    "commit_sha",
    "finished_at",
    "score_total",
    "report_url",
    "total_code_lines",
    "total_code_files",
    "scanned_code_files",
    "status_counts",
    "category_scores",
    "detected_stacks",
    "source",
    "report",
  ],
};
const GENERATOR_THEME_PRESETS = {
  ocean: {
    bg_start: "#F8FBFF",
    bg_end: "#EEF5FF",
    border: "#A8CBFF",
    panel: "#FFFFFF",
    overlay: "#EDF4FF",
    chip_bg: "#E7F0FF",
    chip_text: "#2D4E83",
    text: "#14284B",
    muted: "#3F6191",
    accent: "#16A4E0",
    accent_2: "#1AB9A2",
    accent_soft: "#B8DBFF",
    track: "#D3E3FB",
    pass: "#0F7F39",
    warn: "#B55A0C",
    fail: "#BE1D2D",
  },
  ember: {
    bg_start: "#2E120C",
    bg_end: "#431A12",
    border: "#8C3E2A",
    panel: "#35160F",
    overlay: "#2C130D",
    chip_bg: "#4C2117",
    chip_text: "#FFD6B7",
    text: "#FFEDE1",
    muted: "#E5B79A",
    accent: "#FF6A3D",
    accent_2: "#FFB347",
    accent_soft: "#6B2A1D",
    track: "#6A2F22",
    pass: "#58D68D",
    warn: "#FFC14A",
    fail: "#FF6E6E",
  },
  neon: {
    bg_start: "#090B1B",
    bg_end: "#140F2B",
    border: "#3D2E73",
    panel: "#130F28",
    overlay: "#1B1537",
    chip_bg: "#231B47",
    chip_text: "#CFFBFF",
    text: "#F4F6FF",
    muted: "#B5B9E0",
    accent: "#28F0E2",
    accent_2: "#FF4FD8",
    accent_soft: "#2E2A60",
    track: "#37346B",
    pass: "#55F08A",
    warn: "#FFD65A",
    fail: "#FF6B9A",
  },
  paper: {
    bg_start: "#FFFDF8",
    bg_end: "#F4EFE2",
    border: "#D8CCB1",
    panel: "#FFF9EE",
    overlay: "#F2EBDC",
    chip_bg: "#EADFC8",
    chip_text: "#5A4631",
    text: "#2F2518",
    muted: "#6F5D49",
    accent: "#8B5E34",
    accent_2: "#B08952",
    accent_soft: "#D8C3A3",
    track: "#D9CFBC",
    pass: "#2E7D32",
    warn: "#B26A00",
    fail: "#B64033",
  },
  forest: {
    bg_start: "#0F2018",
    bg_end: "#183129",
    border: "#2D5E4F",
    panel: "#153027",
    overlay: "#11251D",
    chip_bg: "#1E4236",
    chip_text: "#CFEFDF",
    text: "#EDFDF4",
    muted: "#A4C7B8",
    accent: "#3ECF8E",
    accent_2: "#80E3C1",
    accent_soft: "#255145",
    track: "#2C5044",
    pass: "#54D98C",
    warn: "#E3B84F",
    fail: "#F07F7F",
  },
};
const HEX_COLOR_RE = /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;
let generatorDefaultPalette = null;

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

function clampNumber(value, min, max, fallback) {
  const number = Number(value);
  if (!Number.isFinite(number)) return fallback;
  return Math.max(min, Math.min(max, number));
}

function parseBooleanValue(value, fallback = false) {
  if (value == null) return fallback;
  const normalized = String(value).trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalized)) return true;
  if (["0", "false", "no", "off"].includes(normalized)) return false;
  return fallback;
}

function extractGeneratorImportUrl(value) {
  const input = String(value || "").trim();
  if (!input) return "";
  const mdAngle = input.match(/!\[[^\]]*]\(\s*<([^>]+)>\s*\)/);
  if (mdAngle && mdAngle[1]) return mdAngle[1].trim();
  const mdPlain = input.match(/!\[[^\]]*]\(\s*([^\s)]+)(?:\s+["'][^"']*["'])?\s*\)/);
  if (mdPlain && mdPlain[1]) return mdPlain[1].trim();
  return input.replace(/^<|>$/g, "").trim();
}

function parseGeneratorApiImport(value) {
  const input = extractGeneratorImportUrl(value);
  if (!input) return null;
  let url = null;
  try {
    url = new URL(input, window.location.origin);
  } catch {
    return null;
  }

  let owner = "";
  let repo = "";
  let kind = "";
  let format = "";

  const params = url.searchParams;
  const ownerRaw = params.get("owner");
  const repoRaw = params.get("repo");
  if (ownerRaw && repoRaw) {
    owner = ownerRaw.trim();
    repo = repoRaw.trim().replace(/\.git$/i, "");
    kind = String(params.get("kind") || "repo").trim().toLowerCase();
    format = String(params.get("format") || "svg").trim().toLowerCase();
  } else {
    const statsMatch = url.pathname.match(/^\/api\/stats\/(repo|quality)\/([^/]+)\/([^/.]+)\.(svg|json)$/i);
    if (!statsMatch) return null;
    kind = statsMatch[1].toLowerCase();
    owner = decodeURIComponent(statsMatch[2]);
    repo = decodeURIComponent(statsMatch[3]).replace(/\.git$/i, "");
    format = statsMatch[4].toLowerCase();
  }

  if (!owner || !repo) return null;
  kind = kind === "quality" ? "quality" : "repo";
  format = format === "json" ? "json" : "svg";

  const parsed = {
    owner,
    repo,
    kind,
    format,
    theme: params.get("theme"),
    locale: params.get("locale"),
    title: params.get("title"),
    hide: params.get("hide"),
    width: params.get("card_width"),
    langs: params.get("langs_count"),
    animate: params.get("animate"),
    animation: params.get("animation"),
    duration: params.get("duration"),
    cacheSeconds: params.get("cache_seconds"),
    includeReport: params.get("include_report"),
    fields: params.get("fields"),
    colors: {},
  };

  GENERATOR_THEME_KEYS.forEach((key) => {
    const color = normalizeHexColor(params.get(key) || "");
    if (color) parsed.colors[key] = color;
  });
  return parsed;
}

function parseGeneratorImport(value) {
  const apiImport = parseGeneratorApiImport(value);
  if (apiImport) return apiImport;

  const input = extractGeneratorImportUrl(value);
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

function generatorPaletteFromInputs() {
  const palette = {};
  GENERATOR_THEME_KEYS.forEach((key) => {
    const node = document.getElementById(`gen-color-${key}`);
    const value = normalizeHexColor(node?.value || "");
    if (value) palette[key] = value;
  });
  return palette;
}

function applyGeneratorPalette(palette) {
  GENERATOR_THEME_KEYS.forEach((key) => {
    const node = document.getElementById(`gen-color-${key}`);
    const value = normalizeHexColor(palette?.[key] || "");
    if (node && value) node.value = value;
  });
}

function randomHexColor() {
  const value = Math.floor(Math.random() * 0xffffff);
  return `#${value.toString(16).padStart(6, "0").toUpperCase()}`;
}

function randomGeneratorPalette() {
  const palette = {};
  GENERATOR_THEME_KEYS.forEach((key) => {
    palette[key] = randomHexColor();
  });
  return palette;
}

function captureGeneratorDefaultPalette() {
  if (generatorDefaultPalette) return;
  generatorDefaultPalette = generatorPaletteFromInputs();
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
  ["gen-theme-preset", "gen-apply-preset", "gen-randomize-palette", "gen-reset-palette"].forEach((id) => {
    const node = document.getElementById(id);
    if (!node) return;
    node.disabled = !show;
    node.classList.toggle("is-disabled", !show);
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
  const format = document.getElementById("gen-format")?.value || "svg";
  const isSvg = format === "svg";
  const options = Array.from(document.querySelectorAll(".gen-hide-option"));
  options.forEach((input) => {
    const allowed = String(input.dataset.kinds || "repo,quality")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    const isSupported = isSvg && allowed.includes(kind);
    input.disabled = !isSupported;
    if (!isSupported) input.checked = false;
    input.closest(".multi-select-option")?.classList.toggle("is-disabled", !isSupported);
  });
  const panel = document.getElementById("gen-hide-panel");
  if (panel) {
    panel.classList.toggle("is-disabled", !isSvg);
    if (!isSvg) panel.removeAttribute("open");
  }
  syncGeneratorHideField();
}

function syncGeneratorControlVisibility() {
  const kind = document.getElementById("gen-kind")?.value || "repo";
  const format = document.getElementById("gen-format")?.value || "svg";
  const isSvg = format === "svg";
  const isJson = !isSvg;
  const isRepo = kind === "repo";
  const isQualityJson = !isSvg && kind === "quality";

  const svgOnlyRoot = document.getElementById("gen-svg-only-controls");
  const langsRoot = document.getElementById("gen-repo-langs-group");
  const qualityJsonRoot = document.getElementById("gen-quality-json-controls");
  const jsonFieldsRoot = document.getElementById("gen-json-fields-controls");
  if (svgOnlyRoot) svgOnlyRoot.classList.toggle("hidden", !isSvg);
  if (langsRoot) langsRoot.classList.toggle("hidden", !isRepo);
  if (qualityJsonRoot) qualityJsonRoot.classList.toggle("hidden", !isQualityJson);
  if (jsonFieldsRoot) jsonFieldsRoot.classList.toggle("hidden", !isJson);

  GENERATOR_SVG_ONLY_IDS.forEach((id) => {
    const node = document.getElementById(id);
    if (node) node.disabled = !isSvg;
  });
  const randomTheme = document.getElementById("gen-theme-random");
  if (randomTheme) {
    randomTheme.disabled = !isSvg;
    randomTheme.classList.toggle("is-disabled", !isSvg);
  }
  const includeReport = document.getElementById("gen-include-report");
  if (includeReport) includeReport.disabled = !isQualityJson;
  const langs = document.getElementById("gen-langs");
  if (langs) langs.disabled = !isRepo;
  const fields = document.getElementById("gen-fields");
  if (fields) fields.disabled = !isJson;
}

function selectedGeneratorPresetId() {
  const value = (document.getElementById("gen-theme-preset")?.value || "").trim().toLowerCase();
  return value in GENERATOR_THEME_PRESETS ? value : "ocean";
}

function applyGeneratorPresetPalette() {
  const presetId = selectedGeneratorPresetId();
  applyGeneratorPalette(GENERATOR_THEME_PRESETS[presetId]);
}

function resetGeneratorPalette() {
  captureGeneratorDefaultPalette();
  applyGeneratorPalette(generatorDefaultPalette || GENERATOR_THEME_PRESETS.ocean);
}

function randomizeGeneratorPalette() {
  applyGeneratorPalette(randomGeneratorPalette());
}

function pickRandomGeneratorTheme() {
  const themeNode = document.getElementById("gen-theme");
  if (!themeNode) return;
  const options = Array.from(themeNode.options)
    .map((node) => String(node.value || ""))
    .filter((item) => item && item !== "custom");
  if (!options.length) return;
  const next = options[Math.floor(Math.random() * options.length)];
  themeNode.value = next;
}

function setGeneratorHideSelection(checked) {
  document.querySelectorAll(".gen-hide-option:not(:disabled)").forEach((node) => {
    node.checked = checked;
  });
  syncGeneratorHideField();
}

function applyGeneratorHideFlags(rawValue) {
  const tokens = new Set(
    String(rawValue || "")
      .split(",")
      .map((item) => item.trim().toLowerCase())
      .filter(Boolean)
  );
  document.querySelectorAll(".gen-hide-option").forEach((node) => {
    if (node.disabled) {
      node.checked = false;
      return;
    }
    node.checked = tokens.has(String(node.value || "").trim().toLowerCase());
  });
  syncGeneratorHideField();
}

function selectedGeneratorFieldFlags() {
  return Array.from(document.querySelectorAll(".gen-field-option:checked:not(:disabled)"))
    .map((node) => String(node.value || "").trim())
    .filter(Boolean);
}

function syncGeneratorFieldsField() {
  const hiddenInput = document.getElementById("gen-fields");
  const summaryNode = document.getElementById("gen-fields-summary-text");
  const lang = document.body.dataset.lang || "en";
  if (!hiddenInput) return;

  const kind = document.getElementById("gen-kind")?.value || "repo";
  const total = kind === "quality" ? GENERATOR_JSON_FIELDS.quality.length : GENERATOR_JSON_FIELDS.repo.length;
  const selected = selectedGeneratorFieldFlags();

  if (!selected.length) {
    hiddenInput.value = "__none__";
  } else if (selected.length >= total) {
    hiddenInput.value = "";
  } else {
    hiddenInput.value = selected.join(",");
  }

  if (summaryNode) {
    if (!selected.length) {
      summaryNode.textContent = t(lang, "none");
    } else if (selected.length >= total) {
      summaryNode.textContent = t(lang, "all");
    } else {
      summaryNode.textContent = selected.join(", ");
    }
  }
}

function syncGeneratorFieldOptionsByKind() {
  const kind = document.getElementById("gen-kind")?.value || "repo";
  const format = document.getElementById("gen-format")?.value || "svg";
  const isJson = format === "json";
  const options = Array.from(document.querySelectorAll(".gen-field-option"));

  options.forEach((input) => {
    const allowed = String(input.dataset.kinds || "repo,quality")
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    const isSupported = isJson && allowed.includes(kind);
    input.disabled = !isSupported;
    input.closest(".multi-select-option")?.classList.toggle("is-disabled", !isSupported);
  });

  const panel = document.getElementById("gen-fields-panel");
  if (panel) {
    panel.classList.toggle("is-disabled", !isJson);
    if (!isJson) panel.removeAttribute("open");
  }
  syncGeneratorFieldsField();
}

function setGeneratorFieldSelection(checked) {
  document.querySelectorAll(".gen-field-option:not(:disabled)").forEach((node) => {
    node.checked = checked;
  });
  syncGeneratorFieldsField();
}

function applyGeneratorFieldFlags(rawValue) {
  const tokens = new Set(
    String(rawValue || "")
      .split(",")
      .map((item) => item.trim().toLowerCase())
      .filter(Boolean)
  );
  const explicitNone = tokens.has("__none__") || tokens.has("none");
  const hasExplicitSelection = tokens.size > 0;

  document.querySelectorAll(".gen-field-option").forEach((node) => {
    if (node.disabled) return;
    if (!hasExplicitSelection) {
      node.checked = true;
      return;
    }
    node.checked = !explicitNone && tokens.has(String(node.value || "").trim().toLowerCase());
  });
  syncGeneratorFieldsField();
}

function applyGeneratorImportToForm(parsed) {
  const ownerNode = document.getElementById("gen-owner");
  const repoNode = document.getElementById("gen-repo");
  const kindNode = document.getElementById("gen-kind");
  const formatNode = document.getElementById("gen-format");
  const themeNode = document.getElementById("gen-theme");
  const localeNode = document.getElementById("gen-locale");
  const titleNode = document.getElementById("gen-title");
  const widthNode = document.getElementById("gen-width");
  const langsNode = document.getElementById("gen-langs");
  const animateNode = document.getElementById("gen-animate");
  const animationNode = document.getElementById("gen-animation");
  const durationNode = document.getElementById("gen-duration");
  const cacheNode = document.getElementById("gen-cache-seconds");
  const includeReportNode = document.getElementById("gen-include-report");

  if (ownerNode && parsed.owner) ownerNode.value = parsed.owner;
  if (repoNode && parsed.repo) repoNode.value = parsed.repo;
  if (kindNode && parsed.kind) kindNode.value = parsed.kind === "quality" ? "quality" : "repo";
  if (formatNode && parsed.format) formatNode.value = parsed.format === "json" ? "json" : "svg";

  syncGeneratorControlVisibility();
  syncGeneratorHideOptionsByKind();
  syncGeneratorFieldOptionsByKind();

  if (themeNode && parsed.theme) {
    const theme = String(parsed.theme || "").trim().toLowerCase();
    if (Array.from(themeNode.options).some((node) => node.value === theme)) {
      themeNode.value = theme;
    }
  }
  if (localeNode && parsed.locale) {
    const locale = String(parsed.locale || "").trim().toLowerCase();
    if (locale === "en" || locale === "ru") localeNode.value = locale;
  }
  if (titleNode) titleNode.value = parsed.title ?? "";
  if (widthNode && parsed.width != null) {
    widthNode.value = String(clampNumber(parsed.width, 640, 1400, 760));
  }
  if (langsNode && parsed.langs != null) {
    langsNode.value = String(clampNumber(parsed.langs, 1, 30, 4));
  }
  if (animateNode && parsed.animate != null) {
    animateNode.checked = parseBooleanValue(parsed.animate, true);
  }
  if (animationNode && parsed.animation) {
    const mode = String(parsed.animation || "").trim().toLowerCase();
    if (["all", "soft", "bars", "ring", "none"].includes(mode)) {
      animationNode.value = mode;
    }
  }
  if (durationNode && parsed.duration != null) {
    durationNode.value = String(clampNumber(parsed.duration, 350, 7000, 1400));
  }
  if (cacheNode && parsed.cacheSeconds != null) {
    cacheNode.value = String(clampNumber(parsed.cacheSeconds, 0, 86400, 21600));
  }
  if (includeReportNode) {
    includeReportNode.checked = parseBooleanValue(parsed.includeReport, false);
  }

  applyGeneratorHideFlags(parsed.hide ?? "");
  applyGeneratorFieldFlags(parsed.fields ?? "");

  if (parsed.colors && typeof parsed.colors === "object") {
    applyGeneratorPalette(parsed.colors);
  }

  syncGeneratorCustomThemeVisibility();
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
  const cacheSeconds = Number(document.getElementById("gen-cache-seconds")?.value || 21600);
  const includeReport = Boolean(document.getElementById("gen-include-report")?.checked);
  const fields = (document.getElementById("gen-fields")?.value || "").trim();

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
    params.set("cache_seconds", String(Math.max(0, Math.min(86400, cacheSeconds))));
    if (kind === "repo") params.set("langs_count", String(Math.max(1, Math.min(10, langs))));
    if (theme === "custom") {
      const custom = generatorCustomThemeParams();
      Object.entries(custom).forEach(([key, value]) => {
        params.set(key, value);
      });
    }
  } else if (kind === "repo") {
    params.set("langs_count", String(Math.max(1, Math.min(30, langs))));
    if (fields) params.set("fields", fields);
  } else {
    params.set("locale", locale);
    if (includeReport) params.set("include_report", "true");
    if (fields) params.set("fields", fields);
  }

  const qs = params.toString();
  if (qs) path += `?${qs}`;
  return path;
}

function setGeneratorOpenLinkState(node, disabled) {
  if (!node) return;
  node.classList.toggle("is-disabled", disabled);
  if (disabled) {
    node.setAttribute("aria-disabled", "true");
    node.setAttribute("tabindex", "-1");
    node.setAttribute("href", "#");
    return;
  }
  node.removeAttribute("aria-disabled");
  node.removeAttribute("tabindex");
}

function setGeneratorButtonState(node, disabled) {
  if (!node) return;
  node.disabled = disabled;
  node.classList.toggle("is-disabled", disabled);
}

async function copyToClipboard(text) {
  const value = String(text || "");
  if (!value) return false;
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(value);
      return true;
    }
  } catch {
    // Fallback below.
  }
  try {
    const area = document.createElement("textarea");
    area.value = value;
    area.setAttribute("readonly", "true");
    area.style.position = "fixed";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.focus();
    area.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(area);
    return ok;
  } catch {
    return false;
  }
}

async function refreshGeneratorPreview() {
  const lang = document.body.dataset.lang || "en";
  const urlNode = document.getElementById("gen-url");
  const mdNode = document.getElementById("gen-md");
  const image = document.getElementById("gen-preview-image");
  const jsonNode = document.getElementById("gen-preview-json");
  const svgWrap = document.getElementById("gen-svg-wrap");
  const openNode = document.getElementById("gen-open-url");
  const copyUrlNode = document.getElementById("gen-copy-url");
  const copyMdNode = document.getElementById("gen-copy-md");
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
    setGeneratorOpenLinkState(openNode, true);
    setGeneratorButtonState(copyUrlNode, true);
    setGeneratorButtonState(copyMdNode, true);
    return;
  }

  const absolute = `${window.location.origin}${path}`;
  urlNode.value = absolute;
  openNode.setAttribute("href", absolute);
  setGeneratorOpenLinkState(openNode, false);
  setGeneratorButtonState(copyUrlNode, false);

  if (format === "svg") {
    mdNode.value = `![Repo Inspector Card](${absolute})`;
    svgWrap.classList.remove("hidden");
    jsonNode.classList.add("hidden");
    image.src = absolute;
    setGeneratorButtonState(copyMdNode, false);
    return;
  }

  mdNode.value = "";
  setGeneratorButtonState(copyMdNode, true);
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
    "gen-url",
    "gen-md",
    "gen-preview-image",
    "gen-preview-json",
    "gen-svg-wrap",
    "gen-open-url",
  ];
  if (required.some((id) => !document.getElementById(id))) return;

  const controlIds = [
    "gen-owner",
    "gen-repo",
    "gen-kind",
    "gen-format",
    "gen-theme",
    "gen-locale",
    "gen-title",
    "gen-hide",
    "gen-fields",
    "gen-width",
    "gen-langs",
    "gen-animate",
    "gen-animation",
    "gen-duration",
    "gen-cache-seconds",
    "gen-include-report",
    "gen-theme-preset",
  ];
  const controls = controlIds
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
  document.querySelectorAll(".gen-field-option").forEach((node) => {
    node.addEventListener("change", () => {
      syncGeneratorFieldsField();
      delayedPreview();
    });
  });
  document.getElementById("gen-theme")?.addEventListener("change", () => {
    syncGeneratorControlVisibility();
    syncGeneratorHideOptionsByKind();
    syncGeneratorFieldOptionsByKind();
    syncGeneratorCustomThemeVisibility();
  });
  document.getElementById("gen-format")?.addEventListener("change", () => {
    syncGeneratorControlVisibility();
    syncGeneratorHideOptionsByKind();
    syncGeneratorFieldOptionsByKind();
    syncGeneratorCustomThemeVisibility();
  });
  document.getElementById("gen-kind")?.addEventListener("change", () => {
    syncGeneratorControlVisibility();
    syncGeneratorHideOptionsByKind();
    syncGeneratorFieldOptionsByKind();
  });

  document.getElementById("gen-theme-random")?.addEventListener("click", () => {
    pickRandomGeneratorTheme();
    syncGeneratorCustomThemeVisibility();
    delayedPreview();
  });
  document.getElementById("gen-apply-preset")?.addEventListener("click", () => {
    applyGeneratorPresetPalette();
    delayedPreview();
  });
  document.getElementById("gen-randomize-palette")?.addEventListener("click", () => {
    randomizeGeneratorPalette();
    delayedPreview();
  });
  document.getElementById("gen-reset-palette")?.addEventListener("click", () => {
    resetGeneratorPalette();
    delayedPreview();
  });
  ["gen-theme-random", "gen-apply-preset", "gen-randomize-palette", "gen-reset-palette"].forEach((id) => {
    document.getElementById(id)?.addEventListener("click", (event) => {
      event.preventDefault();
    });
  });
  document.getElementById("gen-hide-select-all")?.addEventListener("click", () => {
    setGeneratorHideSelection(true);
    delayedPreview();
  });
  document.getElementById("gen-hide-clear")?.addEventListener("click", () => {
    setGeneratorHideSelection(false);
    delayedPreview();
  });
  document.getElementById("gen-fields-select-all")?.addEventListener("click", () => {
    setGeneratorFieldSelection(true);
    delayedPreview();
  });
  document.getElementById("gen-fields-clear")?.addEventListener("click", () => {
    setGeneratorFieldSelection(false);
    delayedPreview();
  });

  const hidePanel = document.getElementById("gen-hide-panel");
  const fieldsPanel = document.getElementById("gen-fields-panel");
  document.addEventListener("click", (event) => {
    if (hidePanel && !hidePanel.contains(event.target)) hidePanel.removeAttribute("open");
    if (fieldsPanel && !fieldsPanel.contains(event.target)) fieldsPanel.removeAttribute("open");
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
    const parsed = parseGeneratorImport(importInput?.value || "");
    if (!parsed) {
      if (importError) importError.textContent = t(lang, "invalidGeneratorRepoUrl");
      return;
    }
    applyGeneratorImportToForm(parsed);
    if (ownerNode && !ownerNode.value && parsed.owner) ownerNode.value = parsed.owner;
    if (repoNode && !repoNode.value && parsed.repo) repoNode.value = parsed.repo;
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
    await copyToClipboard(text);
  });

  copyMd?.addEventListener("click", async () => {
    const text = mdNode?.value || "";
    if (!text) return;
    await copyToClipboard(text);
  });

  captureGeneratorDefaultPalette();
  syncGeneratorControlVisibility();
  syncGeneratorHideOptionsByKind();
  syncGeneratorFieldOptionsByKind();
  syncGeneratorCustomThemeVisibility();
  syncGeneratorHideField();
  syncGeneratorFieldsField();
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

