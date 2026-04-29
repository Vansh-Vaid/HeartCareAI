/* HeartCare AI – main.js */

// ── Flash auto-dismiss ─────────────────────────────────────────── //
document.querySelectorAll(".hc-alert").forEach((el) => {
  setTimeout(() => bootstrap.Alert.getOrCreateInstance(el)?.close(), 5500);
});

// ── Probability bar animation ──────────────────────────────────── //
function animateProbabilityBars() {
  document.querySelectorAll("[data-probability-width]").forEach((bar) => {
    const w = Math.max(0, Math.min(100, Number(bar.dataset.probabilityWidth || 0)));
    requestAnimationFrame(() => { bar.style.width = `${w}%`; });
  });
}
window.addEventListener("load", animateProbabilityBars);

// ── Mini-bar animation (model breakdown table) ─────────────────── //
window.addEventListener("load", () => {
  document.querySelectorAll(".mini-bar").forEach((bar) => {
    const target = bar.style.width;
    bar.style.width = "0%";
    setTimeout(() => { bar.style.width = target; }, 300);
  });
});

// ── Prediction form validation + submit spinner ────────────────── //
const predictionForm = document.getElementById("prediction-form");
if (predictionForm) {
  // ── Wizard flow (step-by-step form) ──────────────────────────── //
  const stepSections = Array.from(predictionForm.querySelectorAll(".hc-step"));
  const stepChips = Array.from(document.querySelectorAll("[data-step-jump]"));
  const stepCurrentEl = document.querySelector("[data-step-current]");
  const stepTotalEl = document.querySelector("[data-step-total]");
  const stepTitleEl = document.querySelector("[data-step-title]");
  const btnBack = document.querySelector("[data-step-back]");
  const btnNext = document.querySelector("[data-step-next]");
  const btnSubmit = document.querySelector("[data-step-submit]");

  let currentStep = 0;

  function setChipActive(stepIdx) {
    stepChips.forEach((c) => c.classList.toggle("is-active", Number(c.dataset.stepJump) === stepIdx));
  }

  function showStep(stepIdx) {
    currentStep = Math.max(0, Math.min(stepSections.length - 1, stepIdx));
    stepSections.forEach((s) => s.classList.toggle("is-active", Number(s.dataset.step) === currentStep));

    const active = stepSections.find((s) => Number(s.dataset.step) === currentStep);
    const title = active?.dataset.stepName || `Step ${currentStep + 1}`;

    if (stepCurrentEl) stepCurrentEl.textContent = String(currentStep + 1);
    if (stepTotalEl) stepTotalEl.textContent = String(stepSections.length);
    if (stepTitleEl) stepTitleEl.textContent = title;

    setChipActive(currentStep);

    const isFirst = currentStep === 0;
    const isLast = currentStep === stepSections.length - 1;
    if (btnBack) btnBack.disabled = isFirst;
    if (btnNext) btnNext.style.display = isLast ? "none" : "inline-flex";
    if (btnSubmit) btnSubmit.style.display = isLast ? "inline-flex" : "none";

    active?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function validateCurrentStep() {
    const section = stepSections.find((s) => Number(s.dataset.step) === currentStep);
    if (!section) return true;
    const fields = Array.from(section.querySelectorAll("input, select, textarea")).filter(
      (el) => !el.disabled
    );
    const invalid = fields.find((el) => !el.checkValidity());
    if (invalid) {
      predictionForm.classList.add("was-validated");
      invalid.scrollIntoView({ behavior: "smooth", block: "center" });
      invalid.focus?.();
      return false;
    }
    return true;
  }

  if (stepSections.length) {
    showStep(0);

    btnBack?.addEventListener("click", () => showStep(currentStep - 1));
    btnNext?.addEventListener("click", () => {
      if (!validateCurrentStep()) return;
      showStep(currentStep + 1);
    });

    stepChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        const target = Number(chip.dataset.stepJump);
        if (Number.isNaN(target)) return;
        // Require current step to be valid before moving forward.
        if (target > currentStep && !validateCurrentStep()) return;
        showStep(target);
      });
    });
  }

  predictionForm.addEventListener("submit", (e) => {
    if (!predictionForm.checkValidity()) {
      e.preventDefault();
      e.stopPropagation();
      predictionForm.classList.add("was-validated");
      // Scroll to first invalid field
      const first = predictionForm.querySelector(":invalid");
      if (first) first.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    const btn = predictionForm.querySelector("[type='submit']");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Running analysis…';
    }
  });
}

// ── Simple markdown → HTML renderer ───────────────────────────── //
function renderMarkdown(text) {
  return text
    // Bold **text**
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    // Code `inline`
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    // Bullet list: lines starting with • or -
    .replace(/^[•\-]\s+(.+)$/gm, "<li>$1</li>")
    // Wrap consecutive <li> in <ul>
    .replace(/((<li>.*<\/li>\n?)+)/g, "<ul class='mb-1 ps-3'>$1</ul>")
    // Numbered list
    .replace(/^\d+\.\s+(.+)$/gm, "<li>$1</li>")
    // Line breaks
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br>");
}

// ── Chatbot state ─────────────────────────────────────────────── //
const chatbotDrawer   = document.querySelector("[data-chatbot-drawer]");
const chatbotMessages = document.querySelector("[data-chatbot-messages]");
const chatbotForm     = document.querySelector("[data-chatbot-form]");
const chatbotInput    = document.querySelector("[data-chatbot-input]");
const chatbotPage     = document.body.dataset.chatbotPage || "general";
let chatbotWelcomed = false;

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function getWelcomeMessage(page) {
  if (page === "predict") {
    return "I can help you fill out this form. Ask me about any field, what a test means, or what counts as a normal range.";
  }
  if (page === "result") {
    return "I can explain this result in simple language, including the risk percentage, confidence wording, and what to discuss with a doctor.";
  }
  return "I can explain heart screening terms and guide you through the app in simple language.";
}

function appendMessage(role, html, { citations = [], isEmergency = false } = {}) {
  if (!chatbotMessages) return;

  const wrap = document.createElement("div");
  wrap.className = `chatbot-message ${role}${isEmergency ? " emergency" : ""}`;

  const body = document.createElement("div");
  body.innerHTML = `<p>${renderMarkdown(escapeHtml(html))}</p>`;
  wrap.appendChild(body);

  if (citations.length) {
    const meta = document.createElement("div");
    meta.className = "chatbot-citations";
    citations.forEach(({ title, source }) => {
      const pill = document.createElement("span");
      pill.className = "chatbot-citation";
      pill.textContent = title || source;
      meta.appendChild(pill);
    });
    wrap.appendChild(meta);
  }

  chatbotMessages.appendChild(wrap);
  chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
}

function ensureChatbotWelcome() {
  if (!chatbotMessages || chatbotWelcomed || chatbotMessages.children.length) return;
  appendMessage("assistant", getWelcomeMessage(chatbotPage));
  chatbotWelcomed = true;
}

function showTypingIndicator() {
  const el = document.createElement("div");
  el.className = "chatbot-message assistant";
  el.id = "chatbot-typing";
  el.innerHTML = `
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>`;
  el.style.cssText = "display:flex;gap:4px;align-items:center;padding:.65rem .9rem;";
  chatbotMessages?.appendChild(el);
  chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
}

function removeTypingIndicator() {
  document.getElementById("chatbot-typing")?.remove();
}

async function askChatbot(question) {
  appendMessage("user", question);
  showTypingIndicator();

  try {
    const res  = await fetch("/chatbot/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, page: chatbotPage }),
    });
    const data = await res.json();
    removeTypingIndicator();

    if (!res.ok) {
      appendMessage("assistant", data.error || "The help service could not answer right now.");
      return;
    }

    appendMessage("assistant", data.answer, {
      citations: data.citations || [],
      isEmergency: data.is_emergency || false,
    });

    if (data.safety_notice && !data.is_emergency) {
      const note = document.createElement("div");
      note.className = "chatbot-message-meta mt-1";
      note.style.cssText = "font-size:.75rem;color:var(--ink-3);padding:0 .5rem;";
      note.textContent = data.safety_notice;
      chatbotMessages.appendChild(note);
      chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }
  } catch {
    removeTypingIndicator();
    appendMessage("assistant", "The help service is temporarily unavailable. Please try again.");
  }
}

// Open / close
document.querySelectorAll("[data-chatbot-open]").forEach((btn) =>
  btn.addEventListener("click", () => {
    chatbotDrawer?.classList.add("is-open");
    ensureChatbotWelcome();
  })
);
document.querySelectorAll("[data-chatbot-close]").forEach((btn) =>
  btn.addEventListener("click", () => chatbotDrawer?.classList.remove("is-open"))
);

// Quick-start chips
document.querySelectorAll("[data-chatbot-prompt]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const prompt = btn.dataset.chatbotPrompt || "";
    chatbotDrawer?.classList.add("is-open");
    ensureChatbotWelcome();
    if (prompt) askChatbot(prompt);
  });
});

// Form submit
if (chatbotForm && chatbotInput) {
  ensureChatbotWelcome();
  chatbotForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const q = chatbotInput.value.trim();
    if (!q) return;
    chatbotInput.value = "";
    await askChatbot(q);
  });

  // Ctrl+Enter to submit
  chatbotInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      chatbotForm.dispatchEvent(new Event("submit"));
    }
  });
}

// ── Active nav link highlight ──────────────────────────────────── //
document.querySelectorAll(".hc-navbar .nav-link").forEach((link) => {
  if (link.href === window.location.href) link.classList.add("active");
});
