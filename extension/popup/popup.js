
"use strict";

const $ = id => document.getElementById(id);

const API = "http://127.0.0.1:8000/api";
const MAX_PAGE_TEXT = 10000;

const STORAGE_KEY = "qwenApiKey";
const THEME_STORAGE_KEY = "qwenTheme";
const DEFAULT_THEME = "cyber-neon";

const VALID_THEMES = new Set([
  "cyber-neon",
  "midnight-purple",
  "emerald-matrix",
  "light"
]);

let saveTimer = null;
let saveInProgress = Promise.resolve();

// --------------------------------------
// STATUS
// --------------------------------------

function setStatus(message, state = "info") {
  const status = $("status");
  if (!status) return;

  const statusMessage = status.querySelector(".status-message");
  const statusSymbol = status.querySelector(".status-symbol");

  if (statusMessage) {
    statusMessage.textContent = message;
  } else {
    status.textContent = message;
  }

  if (statusSymbol) {
    statusSymbol.textContent =
      state === "success" ? "✓" :
      state === "error" ? "!" :
      state === "loading" ? "◌" : "◈";
  }

  status.dataset.state = state;
}

// --------------------------------------
// LIVE DATE AND TIME
// --------------------------------------

function updateClock() {
  const now = new Date();

  const timeElement = $("clockTime");
  const dayElement = $("clockDay");
  const dateElement = $("clockDate");

  if (!timeElement || !dayElement || !dateElement) return;

  const locale = "en-IN";

  timeElement.textContent = new Intl.DateTimeFormat(locale, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  }).format(now);

  dayElement.textContent = new Intl.DateTimeFormat(locale, {
    weekday: "long"
  }).format(now);

  dateElement.textContent = new Intl.DateTimeFormat(locale, {
    day: "2-digit",
    month: "long",
    year: "numeric"
  }).format(now);
}

updateClock();
setInterval(updateClock, 1000);

// --------------------------------------
// API KEY STORAGE
// --------------------------------------

async function loadSavedApiKey() {
  try {
    if (!chrome.storage?.local) {
      throw new Error(
        'Chrome storage is unavailable. Check that manifest.json includes "storage" permission and reload the extension.'
      );
    }

    const result = await chrome.storage.local.get(STORAGE_KEY);
    $("apiKey").value = result[STORAGE_KEY] || "";
    return true;
  } catch (error) {
    console.error("API key load error:", error);
    setStatus("Storage load error: " + error.message, "error");
    return false;
  }
}

function saveApiKey() {
  clearTimeout(saveTimer);

  saveTimer = setTimeout(() => {
    saveInProgress = saveInProgress
      .catch(() => {})
      .then(async () => {
        if (!chrome.storage?.local) {
          throw new Error(
            'Chrome storage is unavailable. Check the "storage" permission.'
          );
        }

        const key = $("apiKey").value.trim();

        if (key) {
          await chrome.storage.local.set({ [STORAGE_KEY]: key });
        } else {
          await chrome.storage.local.remove(STORAGE_KEY);
        }
      })
      .catch(error => {
        console.error("API key save error:", error);
        setStatus("Storage save error: " + error.message, "error");
      });
  }, 300);
}

$("apiKey").addEventListener("input", saveApiKey);

// --------------------------------------
// THEME STORAGE
// --------------------------------------

async function loadSavedTheme() {
  try {
    const result = await chrome.storage.local.get(THEME_STORAGE_KEY);
    const savedTheme = result[THEME_STORAGE_KEY];

    applyTheme(
      VALID_THEMES.has(savedTheme) ? savedTheme : DEFAULT_THEME
    );
  } catch (error) {
    console.error("Theme load error:", error);
    applyTheme(DEFAULT_THEME);
  }
}

function applyTheme(theme) {
  const safeTheme = VALID_THEMES.has(theme) ? theme : DEFAULT_THEME;

  document.body.dataset.theme = safeTheme;
  $("themeSelect").value = safeTheme;
}

async function saveTheme(theme) {
  if (!VALID_THEMES.has(theme)) return;

  applyTheme(theme);

  try {
    await chrome.storage.local.set({
      [THEME_STORAGE_KEY]: theme
    });
  } catch (error) {
    console.error("Theme save error:", error);
    setStatus("Could not save theme preference: " + error.message, "error");
  }
}

$("themeSelect").addEventListener("change", event => {
  saveTheme(event.target.value);
});

// --------------------------------------
// PAGE EXTRACTION
// --------------------------------------

async function currentPage() {
  const [tab] = await chrome.tabs.query({
    active: true,
    currentWindow: true
  });

  if (!tab?.id || !/^https?:/.test(tab.url || "")) {
    throw new Error(
      "This is a restricted Chrome page. Open a regular website first."
    );
  }

  try {
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: "QWEN_EXTRACT_PAGE"
    });

    if (!response?.ok || !response.page) {
      throw new Error(
        response?.error || "The content script returned no page data."
      );
    }

    return response.page;
  } catch (error) {
    throw new Error(
      "Could not extract page. Reload the website after reloading the extension, then try again. " +
      error.message
    );
  }
}

// --------------------------------------
// FORMAT PAGE TEXT
// --------------------------------------

function formatPage(page) {
  return (
    `Title: ${page.title || "Untitled"}\n` +
    `URL: ${page.url || ""}\n` +
    `Headings: ${(page.headings || []).join(" | ")}\n\n` +
    (page.text || "")
  ).slice(0, MAX_PAGE_TEXT);
}

// --------------------------------------
// SAFE MARKDOWN DISPLAY
// --------------------------------------

function normalizeMarkdown(text) {
  return String(text)
    .replace(/\\([\\`*_{}[\]()#+.!>~-])/g, "$1")
    .replace(/\r\n?/g, "\n")
    .trim();
}

function appendInlineMarkdown(parent, rawText) {
  const text = normalizeMarkdown(rawText);
  const tokenPattern = /(\*\*[^*]+\*\*|__[^_]+__|`[^`]+`|\*[^*\n]+\*|_[^_\n]+_)/g;

  let cursor = 0;
  let match;

  while ((match = tokenPattern.exec(text)) !== null) {
    if (match.index > cursor) {
      parent.appendChild(
        document.createTextNode(text.slice(cursor, match.index))
      );
    }

    const token = match[0];
    let element;

    if (token.startsWith("**") || token.startsWith("__")) {
      element = document.createElement("strong");
      element.textContent = token.slice(2, -2);
    } else if (token.startsWith("`")) {
      element = document.createElement("code");
      element.textContent = token.slice(1, -1);
    } else {
      element = document.createElement("em");
      element.textContent = token.slice(1, -1);
    }

    parent.appendChild(element);
    cursor = match.index + token.length;
  }

  if (cursor < text.length) {
    parent.appendChild(document.createTextNode(text.slice(cursor)));
  }
}

function renderAnswer(rawText) {
  const answer = $("answer");
  const text = normalizeMarkdown(rawText);

  answer.replaceChildren();

  if (!text) {
    answer.textContent = "Qwen returned an empty result.";
    return;
  }

  const lines = text.split("\n");
  let paragraphLines = [];
  let listElement = null;
  let listType = null;

  function flushParagraph() {
    if (!paragraphLines.length) return;

    const paragraph = document.createElement("p");
    appendInlineMarkdown(paragraph, paragraphLines.join(" "));
    answer.appendChild(paragraph);
    paragraphLines = [];
  }

  function closeList() {
    listElement = null;
    listType = null;
  }

  for (const line of lines) {
    const trimmed = line.trim();

    if (!trimmed) {
      flushParagraph();
      closeList();
      continue;
    }

    const headingMatch = trimmed.match(/^#{1,6}\s+(.+)$/);

    if (headingMatch) {
      flushParagraph();
      closeList();

      const heading = document.createElement("h3");
      heading.className = "answer-heading";
      appendInlineMarkdown(heading, headingMatch[1]);
      answer.appendChild(heading);
      continue;
    }

    const bulletMatch = trimmed.match(/^[-*+]\s+(.+)$/);
    const numberMatch = trimmed.match(/^\d+[.)]\s+(.+)$/);

    if (bulletMatch || numberMatch) {
      flushParagraph();

      const nextType = bulletMatch ? "ul" : "ol";

      if (!listElement || listType !== nextType) {
        closeList();
        listType = nextType;
        listElement = document.createElement(nextType);
        answer.appendChild(listElement);
      }

      const item = document.createElement("li");

      appendInlineMarkdown(
        item,
        bulletMatch ? bulletMatch[1] : numberMatch[1]
      );

      listElement.appendChild(item);
      continue;
    }

    closeList();
    paragraphLines.push(trimmed);
  }

  flushParagraph();
}

// --------------------------------------
// API REQUEST
// --------------------------------------

async function post(path, body) {
  const apiKey = $("apiKey").value.trim();

  if (!apiKey) {
    throw new Error("Enter your local API key first.");
  }

  clearTimeout(saveTimer);

  saveInProgress = saveInProgress
    .catch(() => {})
    .then(() => chrome.storage.local.set({
      [STORAGE_KEY]: apiKey
    }));

  try {
    await saveInProgress;
  } catch (error) {
    console.error("API key save error:", error);
    throw new Error(
      "Could not save the API key in Chrome storage: " + error.message
    );
  }

  let response;

  try {
    response = await fetch(API + path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey
      },
      body: JSON.stringify(body)
    });
  } catch (error) {
    throw new Error(
      "Cannot connect to the local backend at " +
      API +
      ". Check that your backend is running."
    );
  }

  const data = await response.json().catch(() => ({
    detail: "The backend returned an invalid response."
  }));

  if (!response.ok) {
    const detail = data.detail;

    const message =
      typeof detail === "string"
        ? detail
        : detail
          ? JSON.stringify(detail)
          : `Backend returned HTTP ${response.status}.`;

    throw new Error(message);
  }

  return data;
}

// --------------------------------------
// RUN QWEN
// --------------------------------------

async function run(kind) {
  const answer = $("answer");

  answer.dataset.state = "loading";
  answer.textContent = "Processing your request...";
  $("trace").textContent = "";

  setStatus("Connecting to local Qwen backend...", "loading");

  $("summarize").disabled = true;
  $("ask").disabled = true;

  try {
    let resultText = "";

    if (kind === "summarize") {
      const page = await currentPage();

      const data = await post("/summarize", {
        text: formatPage(page)
      });

      resultText = data.summary || "";
    } else {
      const question = $("question").value.trim();

      if (!question) {
        throw new Error("Enter a question first.");
      }

      let pageText = "";

      if (/\b(page|article|website|this)\b/i.test(question)) {
        const page = await currentPage();
        pageText = formatPage(page);
      }

      const data = await post("/agent", {
        goal: question,
        page_text: pageText
      });

      resultText = data.answer || "";

      if (data.trace !== undefined) {
        $("trace").textContent = JSON.stringify(
          data.trace,
          null,
          2
        );
      }
    }

    if (typeof resultText !== "string" || !resultText.trim()) {
      throw new Error("Qwen returned an empty result.");
    }

    renderAnswer(resultText);
    answer.dataset.state = "success";

    setStatus(
      "Success — result displayed successfully!",
      "success"
    );
  } catch (error) {
    answer.dataset.state = "error";
    answer.textContent = "Error: " + error.message;

    setStatus(
      "Request failed: " + error.message,
      "error"
    );
  } finally {
    $("summarize").disabled = false;
    $("ask").disabled = false;
  }
}

// --------------------------------------
// BUTTON EVENTS
// --------------------------------------

$("summarize").addEventListener("click", () => {
  run("summarize");
});

$("ask").addEventListener("click", () => {
  run("ask");
});

// --------------------------------------
// INITIALIZE
// --------------------------------------

async function initialize() {
  applyTheme(DEFAULT_THEME);

  await Promise.all([
    loadSavedApiKey(),
    loadSavedTheme()
  ]);
}

initialize();
