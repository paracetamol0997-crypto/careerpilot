/* CareerPilot — Client Controller (Flask + SQLite edition) */
(function () {
  "use strict";

  const SAMPLE_RESUME = `RAHUL VERMA
Email: rahul.verma@college.edu | Phone: +91 98765 43210
B.Tech in Computer Science & Engineering (2023 - 2027) | CGPA: 7.8 / 10

SKILLS:
Languages: Python, JavaScript, Java, C++, SQL, HTML/CSS
Frameworks & Tools: Flask, React.js, Git, GitHub, SQLite

PROJECTS:
1. Campus Food Ordering Web Portal
- Built a web application using Flask and React for college cafeteria orders.
- Implemented user login system and shopping cart feature.
- Created SQLite database tables to store menu items and customer orders.

2. Library Management System
- Developed Python application for college library book issuance and tracking.
- Helped classmates search books by title and author.

EDUCATION & COURSEWORK:
Data Structures, Operating Systems, Database Management Systems, Object Oriented Programming.`;

  const ICONS = {
    check: '<svg class="cp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>',
    doc: '<svg class="cp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    refresh: '<svg class="cp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>',
    mic: '<svg class="cp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>',
    alert: '<svg class="cp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
    bookmark: '<svg class="cp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>',
    bookmarkFilled: '<svg class="cp-icon" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>',
    lock: '<svg class="cp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
  };

  const SPINNER_HTML = '<progress aria-label="Loading" class="loading-spinner"></progress>';

  let appState = window.__CAREERPILOT_INITIAL_STATE__ || {};
  let activeMagicToken = "";
  let activeMagicEmail = "";

  // ---------------------------------------------------------------------------
  // Theme Switcher
  // ---------------------------------------------------------------------------
  function syncThemeButtons() {
    const isDark = document.documentElement.classList.contains("dark");
    document.querySelectorAll("[data-theme-set]").forEach((btn) => {
      const target = btn.getAttribute("data-theme-set");
      btn.setAttribute("aria-pressed", String((target === "dark") === isDark));
    });
  }

  function setTheme(theme) {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    try {
      localStorage.setItem("careerpilot_theme", theme);
    } catch (_) {}
    syncThemeButtons();
  }

  document.querySelectorAll("[data-theme-set]").forEach((btn) => {
    btn.addEventListener("click", () => setTheme(btn.getAttribute("data-theme-set")));
  });
  syncThemeButtons();

  // ---------------------------------------------------------------------------
  // Native <dialog> Modals + closedby="any" fallback
  // ---------------------------------------------------------------------------
  if (!("closedBy" in HTMLDialogElement.prototype)) {
    const outside = (e, dialog) => {
      const r = dialog.getBoundingClientRect();
      return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
    };
    document.querySelectorAll('dialog[closedby="any"]').forEach((dialog) => {
      let pressedOutside = false;
      dialog.addEventListener("pointerdown", (e) => {
        pressedOutside = outside(e, dialog);
      });
      dialog.addEventListener("pointerup", (e) => {
        if (pressedOutside && outside(e, dialog)) dialog.close();
      });
    });
  }

  function openDialog(id) {
    const dlg = document.getElementById(id);
    if (dlg && typeof dlg.showModal === "function" && !dlg.open) {
      dlg.showModal();
    }
  }

  function closeDialog(id) {
    const dlg = document.getElementById(id);
    if (dlg && dlg.open) {
      dlg.close();
    }
  }

  document.querySelectorAll("[data-close-dialog]").forEach((btn) => {
    btn.addEventListener("click", () => closeDialog(btn.getAttribute("data-close-dialog")));
  });

  document.querySelectorAll("[data-open-reg]").forEach((btn) => {
    btn.addEventListener("click", () => openDialog("reg-dialog"));
  });

  // ---------------------------------------------------------------------------
  // Utility Helpers & Loading State Manager
  // ---------------------------------------------------------------------------
  function esc(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function setBusy(btn, isBusy, busyLabel) {
    if (!btn) return;
    if (isBusy) {
      if (!btn.dataset.origHtml) {
        btn.dataset.origHtml = btn.innerHTML;
      }
      btn.disabled = true;
      btn.setAttribute("aria-busy", "true");
      btn.innerHTML = `${SPINNER_HTML}<span>${esc(busyLabel || "Working...")}</span>`;
    } else {
      btn.disabled = false;
      btn.removeAttribute("aria-busy");
      if (btn.dataset.origHtml) {
        btn.innerHTML = btn.dataset.origHtml;
        delete btn.dataset.origHtml;
      }
    }
  }

  async function apiJson(url, options) {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...(options || {}),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "Request failed");
    }
    return data;
  }

  function updateNavRegistered(user) {
    const slot = document.getElementById("nav-auth-slot");
    if (!slot || !user) return;
    slot.innerHTML = `<a href="/dashboard" class="cp-btn cp-btn-outline cp-btn-sm"><span class="text-pass">${ICONS.check}</span><span>${esc(user.name || "Profile")}</span></a>`;
  }

  // ---------------------------------------------------------------------------
  // Chat Shell & Cards Renderer
  // ---------------------------------------------------------------------------
  class ChatWidgetController {
    constructor(rootEl, isEmbedded) {
      this.root = rootEl;
      this.isEmbedded = isEmbedded;
      this.isTyping = false;
      this.activeJobsFilter = "all";
      this.activeRoadmapPhase = "Foundation";
      this.activeResumeTab = "mistakes";
      this.lastRenderedCount = 0;
      this.renderShell();
      this.loadState();
    }

    renderShell() {
      this.root.innerHTML = `
        <div class="cp-chat-status">
          <div style="display:flex; align-items:center; gap:0.55rem;">
            <span style="width:8px; height:8px; border-radius:4px; background:var(--status-pass); display:inline-block;" aria-hidden="true"></span>
            <span class="text-muted" id="cp-status-text">Advisor ready</span>
          </div>
          <button type="button" id="cp-reset-chat-btn" class="cp-btn cp-btn-ghost cp-btn-sm" title="Reset conversation">
            ${ICONS.refresh}
            <span>Reset</span>
          </button>
        </div>
        <div class="cp-chat-feed" id="cp-chat-feed" aria-live="polite"></div>
        <form class="cp-chat-input-bar" id="cp-chat-form">
          <button type="button" id="cp-open-resume-btn" class="cp-btn cp-btn-outline cp-btn-sm" aria-label="Upload or paste resume" title="Analyze resume">
            ${ICONS.doc}
            <span>Resume</span>
          </button>
          <input type="text" id="cp-chat-input" class="cp-input" placeholder="Ask about resume fixes, 90-day roadmap, or mock interviews..." autocomplete="off" />
          <button type="submit" id="cp-chat-send" class="cp-btn cp-btn-primary cp-btn-sm">Send</button>
        </form>
      `;

      this.feedEl = this.root.querySelector("#cp-chat-feed");
      this.statusEl = this.root.querySelector("#cp-status-text");
      this.inputEl = this.root.querySelector("#cp-chat-input");
      this.formEl = this.root.querySelector("#cp-chat-form");
      this.sendBtn = this.root.querySelector("#cp-chat-send");

      this.root.querySelector("#cp-open-resume-btn").addEventListener("click", () => {
        openDialog("resume-dialog");
      });

      const resetBtn = this.root.querySelector("#cp-reset-chat-btn");
      resetBtn.addEventListener("click", async () => {
        setBusy(resetBtn, true, "Resetting");
        try {
          const res = await apiJson("/api/chat/reset", { method: "POST" });
          appState.messages = res.messages;
          this.lastRenderedCount = 0;
          this.renderMessages();
        } finally {
          setBusy(resetBtn, false);
        }
      });

      this.formEl.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = this.inputEl.value.trim();
        if (!text || this.isTyping) return;
        this.inputEl.value = "";
        this.sendUserMessage(text);
      });
    }

    async loadState() {
      try {
        appState = await apiJson("/api/state");
      } catch (_) {}
      this.updateStatusHeader();
      this.renderMessages();

      const intent = new URLSearchParams(window.location.search).get("intent");
      if (intent && !this.handledInitialIntent) {
        this.handledInitialIntent = true;
        this.executeIntent(intent);
      }
    }

    updateStatusHeader() {
      if (appState.profile) {
        this.statusEl.innerHTML = `<strong>${esc(appState.profile.branch)}</strong> (${esc(appState.profile.year)} yr) · <span class="text-brand" style="font-weight:600;">${esc(appState.profile.targetRole)}</span>`;
      } else {
        this.statusEl.textContent = "Advisor ready";
      }
    }

    scrollBottom() {
      if (this.feedEl) {
        this.feedEl.scrollTop = this.feedEl.scrollHeight;
      }
    }

    renderMessages() {
      const msgs = appState.messages || [];
      this.feedEl.innerHTML = "";
      msgs.forEach((msg, i) => {
        const row = document.createElement("div");
        const isNew = i >= this.lastRenderedCount;
        row.className = `cp-msg-row ${msg.sender === "user" ? "user" : "bot"}${isNew ? " is-new" : ""}`;

        const tag = document.createElement("div");
        tag.className = "text-subtle";
        tag.style.fontSize = "0.75rem";
        tag.style.fontWeight = "500";
        tag.textContent = msg.sender === "user" ? "You" : "CareerPilot";
        row.appendChild(tag);

        const bubble = document.createElement("div");
        bubble.className = "cp-msg-bubble";
        if (!msg.text && this.isTyping && i === msgs.length - 1) {
          bubble.innerHTML = `<span style="display:inline-flex; align-items:center; gap:0.5rem;">${SPINNER_HTML}<span>Thinking...</span></span>`;
        } else {
          bubble.textContent = msg.text || "";
        }
        row.appendChild(bubble);

        if (msg.cardPayload) {
          const cardWrap = document.createElement("div");
          cardWrap.style.width = "100%";
          cardWrap.style.maxWidth = "34rem";
          cardWrap.style.marginTop = "0.45rem";
          if (msg.cardPayload.type === "resume_preview") {
            cardWrap.innerHTML = this.renderResumeCard(msg.cardPayload.data);
          } else if (msg.cardPayload.type === "roadmap_preview") {
            cardWrap.innerHTML = this.renderRoadmapCard(msg.cardPayload.data);
          } else if (msg.cardPayload.type === "jobs_preview") {
            cardWrap.innerHTML = this.renderJobsCard(msg.cardPayload.data);
          } else if (msg.cardPayload.type === "interview_invite") {
            cardWrap.innerHTML = this.renderInterviewSummaryCard(msg.cardPayload.data);
          }
          row.appendChild(cardWrap);
        }

        if (Array.isArray(msg.chips) && msg.chips.length > 0) {
          const chipsRow = document.createElement("div");
          chipsRow.className = "cp-chips-row";
          msg.chips.forEach((chip) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "cp-chip";
            btn.textContent = chip.label;
            btn.addEventListener("click", () => this.handleChip(chip, btn));
            chipsRow.appendChild(btn);
          });
          row.appendChild(chipsRow);
        }

        this.feedEl.appendChild(row);
      });

      this.lastRenderedCount = msgs.length;
      this.bindCardEvents();
      this.scrollBottom();
    }

    renderResumeCard(res) {
      const scoreColor = res.score >= 80 ? "text-pass" : res.score >= 60 ? "text-brand" : "text-fix";
      const mistakesHtml = (res.mistakes || [])
        .map((m) => {
          if (m.isLocked) {
            return `
              <div class="cp-locked-box">
                <div class="cp-locked-blur">
                  <strong>Fix #${m.id}: ${esc(m.title)}</strong>
                  <p style="font-size:0.8rem;">${esc(m.whatIsWrong)}</p>
                </div>
                <div class="cp-locked-overlay">
                  <strong style="font-size:0.84rem; display:inline-flex; align-items:center; gap:0.35rem;">${ICONS.lock}<span>Fix #${m.id} locked</span></strong>
                  <p class="text-muted" style="font-size:0.78rem; margin:0.25rem 0 0.6rem;">Sign in free to view exact before and after bullet rewrites.</p>
                  <button type="button" class="cp-btn cp-btn-primary cp-btn-sm" data-open-reg-inline>Unlock fix #${m.id}</button>
                </div>
              </div>
            `;
          }
          return `
            <div class="cp-subcard" style="display:flex; flex-direction:column; gap:0.55rem;">
              <div style="font-weight:600; font-size:0.9rem;">
                <span class="text-brand tabular-nums">#${m.id}</span> · ${esc(m.title)}
              </div>
              <div class="text-muted" style="font-size:0.82rem; line-height:1.5;">
                <div><strong>Issue:</strong> ${esc(m.whatIsWrong)}</div>
                <div><strong>Impact:</strong> ${esc(m.whyItHurts)}</div>
                <div><strong class="text-brand">Fix:</strong> ${esc(m.howToFix)}</div>
              </div>
              <div class="cp-diff-box">
                <div style="background:var(--status-fix-bg); padding:0.55rem 0.7rem;">
                  <strong class="text-fix">- Before:</strong> ${esc(m.beforeExample)}
                </div>
                <div style="background:var(--status-pass-bg); padding:0.55rem 0.7rem;">
                  <strong class="text-pass">+ After:</strong> ${esc(m.afterExample)}
                </div>
              </div>
            </div>
          `;
        })
        .join("");

      const b = res.breakdown || {};
      const pillars = [
        ["Target keyword match", b.keywordMatch || 0, 30],
        ["Formatting and parseability", b.formatting || 0, 20],
        ["Quantified impact", b.quantifiedImpact || 0, 20],
        ["Section completeness", b.sectionCompleteness || 0, 15],
        ["Length and clarity", b.lengthAndClarity || 0, 15],
      ]
        .map(
          ([label, sc, mx]) => `
            <div>
              <div style="display:flex; justify-content:space-between; font-size:0.82rem; margin-bottom:0.3rem;">
                <span>${label}</span><span class="text-brand tabular-nums" style="font-weight:600;">${sc} / ${mx}</span>
              </div>
              <div class="cp-progress-track"><div class="cp-progress-fill" style="width:${Math.round((sc / mx) * 100)}%;"></div></div>
            </div>
          `
        )
        .join("");

      return `
        <div class="cp-card" style="padding:1.2rem; display:flex; flex-direction:column; gap:1rem;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem;">
            <div>
              <div class="text-subtle" style="font-size:0.78rem;">ATS audit report</div>
              <div style="font-weight:600; font-size:1rem; margin-top:0.15rem;">Target: <span class="text-brand">${esc(res.targetRole)}</span></div>
            </div>
            <div class="cp-subcard" style="text-align:center; padding:0.45rem 0.85rem;">
              <div class="tabular-nums ${scoreColor}" style="font-size:1.5rem; font-weight:700;">${res.score}</div>
              <div class="text-subtle" style="font-size:0.72rem;">out of 100</div>
            </div>
          </div>
          <div class="cp-subcard" style="padding:0.65rem 0.85rem; font-size:0.84rem;">
            ${esc(res.verdict)}
          </div>
          <div class="cp-tabs">
            <button type="button" class="cp-tab-btn ${this.activeResumeTab === "mistakes" ? "active" : ""}" data-card-resume-tab="mistakes">Fixable mistakes</button>
            <button type="button" class="cp-tab-btn ${this.activeResumeTab === "breakdown" ? "active" : ""}" data-card-resume-tab="breakdown">Score breakdown</button>
          </div>
          <div style="display:flex; flex-direction:column; gap:0.75rem;">
            ${this.activeResumeTab === "mistakes" ? mistakesHtml : pillars}
          </div>
        </div>
      `;
    }

    renderRoadmapCard(rm) {
      const weeks = rm.weeks || [];
      const phaseWeeks = weeks.filter((w) => w.phase === this.activeRoadmapPhase);
      const weeksHtml = phaseWeeks
        .map((wk) => {
          if (wk.isLocked) {
            return `
              <div class="cp-locked-box">
                <div class="cp-locked-blur"><strong>Week ${wk.weekNumber}: ${esc(wk.title)}</strong></div>
                <div class="cp-locked-overlay">
                  <strong style="font-size:0.84rem; display:inline-flex; align-items:center; gap:0.35rem;">${ICONS.lock}<span>Week ${wk.weekNumber} locked</span></strong>
                  <p class="text-muted" style="font-size:0.78rem; margin:0.25rem 0 0.6rem;">Sign in free to unlock weeks 3 to 12.</p>
                  <button type="button" class="cp-btn cp-btn-primary cp-btn-sm" data-open-reg-inline>Unlock 12 weeks free</button>
                </div>
              </div>
            `;
          }
          const tasksHtml = (wk.tasks || [])
            .map(
              (t) => `
                <label style="display:flex; align-items:center; gap:0.55rem; font-size:0.82rem; padding:0.4rem 0.6rem; border-radius:6px; background:var(--surface-card); cursor:pointer;">
                  <input type="checkbox" class="chat-rm-task" data-week="${wk.weekNumber}" data-task="${esc(t.id)}" ${t.completed ? "checked" : ""} />
                  <span style="${t.completed ? "text-decoration:line-through; opacity:0.6;" : ""}">${esc(t.title)}</span>
                </label>
              `
            )
            .join("");

          return `
            <div class="cp-subcard" style="display:flex; flex-direction:column; gap:0.55rem;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="text-brand tabular-nums" style="font-size:0.78rem; font-weight:600;">Week ${wk.weekNumber}</span>
                <span class="text-subtle" style="font-size:0.76rem;">${esc(wk.phase)}</span>
              </div>
              <strong style="font-size:0.92rem;">${esc(wk.title)}</strong>
              <p class="text-muted" style="margin:0; font-size:0.82rem;">${esc(wk.description)}</p>
              <div style="display:flex; flex-direction:column; gap:0.4rem;">${tasksHtml}</div>
              <a href="${esc(wk.resourceUrl)}" target="_blank" rel="noopener noreferrer" class="text-brand" style="font-size:0.8rem; font-weight:500;">
                ${esc(wk.resourceTitle)}
              </a>
            </div>
          `;
        })
        .join("");

      return `
        <div class="cp-card" style="padding:1.2rem; display:flex; flex-direction:column; gap:0.85rem;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div class="text-subtle" style="font-size:0.78rem;">90-day roadmap</div>
              <div style="font-weight:600; font-size:1rem; margin-top:0.15rem;">${esc(rm.role)} plan</div>
            </div>
            <span class="text-brand tabular-nums" style="font-size:0.86rem; font-weight:600;">${rm.progressPercent || 0}% complete</span>
          </div>
          <div class="cp-progress-track"><div class="cp-progress-fill" style="width:${rm.progressPercent || 0}%;"></div></div>
          <div class="cp-tabs">
            ${["Foundation", "Build", "Job Ready"]
              .map(
                (p) =>
                  `<button type="button" class="cp-tab-btn ${this.activeRoadmapPhase === p ? "active" : ""}" data-card-rm-phase="${p}">${p}</button>`
              )
              .join("")}
          </div>
          <div style="display:flex; flex-direction:column; gap:0.75rem; max-height:24rem; overflow-y:auto;">${weeksHtml}</div>
        </div>
      `;
    }

    renderJobsCard(jobs) {
      const visible = (jobs || []).filter((j) =>
        this.activeJobsFilter === "all" ? true : j.jobType === this.activeJobsFilter
      );
      const savedIds = new Set((appState.savedJobs || []).map((j) => j.id));

      const jobsHtml = visible
        .map((job) => {
          if (job.isScamSuspicious) {
            return `
              <div class="cp-subcard" style="background:var(--status-fix-bg); display:flex; flex-direction:column; gap:0.45rem;">
                <div class="text-fix" style="font-size:0.78rem; font-weight:600; display:inline-flex; align-items:center; gap:0.35rem;">
                  ${ICONS.alert}
                  <span>Suspicious posting flagged</span>
                </div>
                <strong style="text-decoration:line-through; opacity:0.8; font-size:0.88rem;">${esc(job.title)}</strong>
                <div class="text-muted" style="font-size:0.8rem;">${esc(job.company)}</div>
                <ul style="margin:0.25rem 0; padding-left:1.1rem; font-size:0.8rem;" class="text-fix">
                  ${(job.scamReasons || []).map((r) => `<li>${esc(r)}</li>`).join("")}
                </ul>
                <button type="button" class="cp-btn cp-btn-sm cp-btn-danger report-job-btn" data-job-id="${esc(job.id)}" style="align-self:flex-start;">
                  Report listing
                </button>
              </div>
            `;
          }

          const isSaved = savedIds.has(job.id);
          return `
            <div class="cp-subcard" style="display:flex; flex-direction:column; gap:0.55rem;">
              <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem;">
                <div>
                  <strong style="font-size:0.9rem;">${esc(job.title)}</strong>
                  <div class="text-muted" style="font-size:0.8rem;">${esc(job.company)} · ${esc(job.location)}</div>
                </div>
                <span class="cp-status-note cp-status-pass tabular-nums">${job.matchPercent}% match</span>
              </div>
              ${
                job.hasCgpaFilter
                  ? `<div class="cp-status-note cp-status-warn">Employer requests ${job.minCgpaRequired}+ CGPA</div>`
                  : ""
              }
              <p class="text-muted" style="margin:0; font-size:0.82rem;">${esc(job.whyItMatches)}</p>
              <div style="display:flex; justify-content:space-between; align-items:center; padding-top:0.35rem;">
                <span class="tabular-nums" style="font-size:0.82rem; font-weight:600;">${esc(job.salaryRange)}</span>
                <div style="display:flex; gap:0.45rem;">
                  <button type="button" class="cp-btn cp-btn-outline cp-btn-sm save-job-btn" data-job-json='${esc(JSON.stringify(job))}'>
                    ${isSaved ? ICONS.bookmarkFilled : ICONS.bookmark}
                    <span>${isSaved ? "Saved" : "Save"}</span>
                  </button>
                  <a href="${esc(job.applyUrl)}" target="_blank" rel="noopener noreferrer" class="cp-btn cp-btn-primary cp-btn-sm">Apply</a>
                </div>
              </div>
            </div>
          `;
        })
        .join("");

      return `
        <div class="cp-card" style="padding:1.2rem; display:flex; flex-direction:column; gap:0.85rem;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div class="text-subtle" style="font-size:0.78rem;">Verified roles</div>
              <div style="font-weight:600; font-size:1rem;">Matched fresher openings</div>
            </div>
            <span class="text-muted tabular-nums" style="font-size:0.82rem;">${(jobs || []).length} matches</span>
          </div>
          <div class="cp-tabs">
            ${["all", "Fresher", "Internship"]
              .map(
                (t) =>
                  `<button type="button" class="cp-tab-btn ${this.activeJobsFilter === t ? "active" : ""}" data-job-filter="${t}">${t === "all" ? "All" : t}</button>`
              )
              .join("")}
          </div>
          <div style="display:flex; flex-direction:column; gap:0.75rem; max-height:24rem; overflow-y:auto;">${jobsHtml}</div>
        </div>
      `;
    }

    renderInterviewSummaryCard(rep) {
      return `
        <div class="cp-card" style="padding:1.1rem; display:flex; flex-direction:column; gap:0.55rem;">
          <div class="text-subtle" style="font-size:0.8rem;">Mock interview complete</div>
          <div class="text-brand tabular-nums" style="font-size:1.5rem; font-weight:700;">${rep.overallScore} / 10</div>
          <div class="text-muted" style="font-size:0.84rem;">Recommended next step: ${esc(rep.nextRoadmapAction)}</div>
          <a href="/dashboard" class="cp-btn cp-btn-outline cp-btn-sm" style="align-self:flex-start;">View full report</a>
        </div>
      `;
    }

    bindCardEvents() {
      this.feedEl.querySelectorAll("[data-open-reg-inline]").forEach((b) => {
        b.addEventListener("click", () => openDialog("reg-dialog"));
      });
      this.feedEl.querySelectorAll("[data-card-resume-tab]").forEach((b) => {
        b.addEventListener("click", () => {
          this.activeResumeTab = b.getAttribute("data-card-resume-tab");
          this.renderMessages();
        });
      });
      this.feedEl.querySelectorAll("[data-card-rm-phase]").forEach((b) => {
        b.addEventListener("click", () => {
          this.activeRoadmapPhase = b.getAttribute("data-card-rm-phase");
          this.renderMessages();
        });
      });
      this.feedEl.querySelectorAll("[data-job-filter]").forEach((b) => {
        b.addEventListener("click", () => {
          this.activeJobsFilter = b.getAttribute("data-job-filter");
          this.renderMessages();
        });
      });
      this.feedEl.querySelectorAll(".chat-rm-task").forEach((cb) => {
        cb.addEventListener("change", async () => {
          cb.disabled = true;
          try {
            const wk = Number(cb.getAttribute("data-week"));
            const tid = cb.getAttribute("data-task");
            const updated = await apiJson("/api/roadmap/toggle-task", {
              method: "POST",
              body: JSON.stringify({ weekNumber: wk, taskId: tid }),
            });
            (appState.messages || []).forEach((m) => {
              if (m.cardPayload && m.cardPayload.type === "roadmap_preview") {
                m.cardPayload.data = updated;
              }
            });
            this.renderMessages();
          } finally {
            cb.disabled = false;
          }
        });
      });
      this.feedEl.querySelectorAll(".save-job-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          setBusy(btn, true, "Saving");
          try {
            const job = JSON.parse(btn.getAttribute("data-job-json"));
            const res = await apiJson("/api/jobs/save", {
              method: "POST",
              body: JSON.stringify({ job }),
            });
            appState.savedJobs = res.savedJobs;
            this.renderMessages();
          } catch (_) {
            setBusy(btn, false);
          }
        });
      });
      this.feedEl.querySelectorAll(".report-job-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          setBusy(btn, true, "Reporting");
          const jobId = btn.getAttribute("data-job-id");
          try {
            await apiJson("/api/jobs/report", {
              method: "POST",
              body: JSON.stringify({ jobId }),
            });
            btn.innerHTML = `${ICONS.check}<span>Reported</span>`;
            btn.removeAttribute("aria-busy");
            btn.disabled = true;
          } catch (_) {
            setBusy(btn, false);
          }
        });
      });
    }

    async handleChip(chip, triggerBtn) {
      if (chip.value === "feature_resume") return openDialog("resume-dialog");
      if (chip.value === "feature_roadmap") return this.triggerRoadmap(triggerBtn);
      if (chip.value === "feature_jobs") return this.triggerJobs(triggerBtn);
      if (chip.value === "feature_interview") {
        if (!appState.isRegistered) return openDialog("reg-dialog");
        return startMockInterview();
      }
      if (chip.value === "open_reg") return openDialog("reg-dialog");
      if (chip.value === "go_dashboard") {
        window.location.href = "/dashboard";
        return;
      }
      this.sendUserMessage(chip.label);
    }

    executeIntent(intent, triggerBtn) {
      if (intent === "resume_check") {
        openDialog("resume-dialog");
      } else if (intent === "roadmap") {
        this.triggerRoadmap(triggerBtn);
      } else if (intent === "jobs") {
        this.triggerJobs(triggerBtn);
      } else if (intent === "mock_interview") {
        if (!appState.isRegistered) openDialog("reg-dialog");
        else startMockInterview();
      }
    }

    async triggerRoadmap(triggerBtn) {
      setBusy(triggerBtn, true, "Building roadmap");
      try {
        await apiJson("/api/roadmap", { method: "POST", body: JSON.stringify({ appendChat: true }) });
        await this.loadState();
      } finally {
        setBusy(triggerBtn, false);
      }
    }

    async triggerJobs(triggerBtn) {
      setBusy(triggerBtn, true, "Finding matches");
      try {
        await apiJson("/api/jobs", { method: "POST", body: JSON.stringify({ appendChat: true }) });
        await this.loadState();
      } finally {
        setBusy(triggerBtn, false);
      }
    }

    async sendUserMessage(text) {
      this.isTyping = true;
      setBusy(this.sendBtn, true, "Sending");
      const userMsg = { id: "u_" + Date.now(), sender: "user", text };
      const botMsg = { id: "b_" + Date.now(), sender: "bot", text: "" };
      appState.messages = [...(appState.messages || []), userMsg, botMsg];
      this.renderMessages();

      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text, profile: appState.profile }),
        });
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let fullText = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          fullText += decoder.decode(value, { stream: true });
          botMsg.text = fullText;
          this.renderMessages();
        }
      } catch (err) {
        botMsg.text = "Ready to help. Choose Resume Audit, 90-Day Roadmap, Verified Roles, or Mock Interview.";
        this.renderMessages();
      } finally {
        this.isTyping = false;
        setBusy(this.sendBtn, false);
        await this.loadState();
      }
    }
  }

  // Instantiate visible product on either /chat or home hero workspace
  let activeChatCtrl = null;
  const fullChatRoot = document.getElementById("full-chat-root");
  const heroChatRoot = document.getElementById("hero-chat-root");
  if (fullChatRoot) {
    activeChatCtrl = new ChatWidgetController(fullChatRoot, false);
  } else if (heroChatRoot) {
    activeChatCtrl = new ChatWidgetController(heroChatRoot, true);
  }

  document.querySelectorAll("[data-launch-intent]").forEach((el) => {
    el.addEventListener("click", () => {
      const intent = el.getAttribute("data-launch-intent");
      if (activeChatCtrl) {
        if (heroChatRoot) {
          heroChatRoot.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
        activeChatCtrl.executeIntent(intent, el);
      } else {
        window.location.href = `/chat?intent=${encodeURIComponent(intent)}`;
      }
    });
  });

  // ---------------------------------------------------------------------------
  // Resume Upload & Audit Modal
  // ---------------------------------------------------------------------------
  const resumePastePane = document.getElementById("resume-paste-pane");
  const resumeUploadPane = document.getElementById("resume-upload-pane");
  const resumeTextInput = document.getElementById("resume-text-input");
  const resumeFileInput = document.getElementById("resume-file-input");
  const resumeFileLabel = document.getElementById("resume-file-label");
  const resumeModalErr = document.getElementById("resume-modal-error");
  const resumeSubmitBtn = document.getElementById("resume-submit-btn");
  let uploadedFileName = "";

  document.querySelectorAll("[data-resume-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const t = btn.getAttribute("data-resume-tab");
      document.querySelectorAll("[data-resume-tab]").forEach((b) => b.classList.toggle("active", b === btn));
      resumePastePane.classList.toggle("hidden", t !== "paste");
      resumeUploadPane.classList.toggle("hidden", t !== "upload");
    });
  });

  const sampleBtn = document.getElementById("insert-sample-resume-btn");
  if (sampleBtn) {
    sampleBtn.addEventListener("click", () => {
      resumeTextInput.value = SAMPLE_RESUME;
      uploadedFileName = "Rahul_Verma_Sample_Resume.txt";
      resumeModalErr.classList.add("hidden");
    });
  }

  if (resumeFileInput) {
    resumeFileInput.addEventListener("change", async () => {
      const file = resumeFileInput.files && resumeFileInput.files[0];
      if (!file) return;
      resumeModalErr.classList.add("hidden");
      resumeFileLabel.innerHTML = `<span style="display:inline-flex; align-items:center; gap:0.5rem;">${SPINNER_HTML}<span>Scanning ${esc(file.name)}...</span></span>`;

      const formData = new FormData();
      formData.append("file", file);
      try {
        const res = await fetch("/api/upload", { method: "POST", body: formData });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Upload failed");
        uploadedFileName = data.securityCheck.sanitizedFilename;
        resumeTextInput.value = data.extractedText && data.extractedText.length > 20 ? data.extractedText : SAMPLE_RESUME;
        resumeFileLabel.innerHTML = `<span class="text-pass" style="display:inline-flex; align-items:center; gap:0.4rem;">${ICONS.check}<span>Ready: ${esc(uploadedFileName)}</span></span>`;
      } catch (err) {
        resumeModalErr.innerHTML = `${ICONS.alert}<span>${esc(err.message)}</span>`;
        resumeModalErr.classList.remove("hidden");
        resumeFileLabel.textContent = "Choose a PDF, DOCX, or TXT file";
      }
    });
  }

  const resumeForm = document.getElementById("resume-audit-form");
  if (resumeForm) {
    resumeForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = resumeTextInput.value.trim();
      if (text.length < 10) {
        resumeModalErr.innerHTML = `${ICONS.alert}<span>Paste your resume text or insert the sample resume first.</span>`;
        resumeModalErr.classList.remove("hidden");
        return;
      }
      resumeModalErr.classList.add("hidden");
      setBusy(resumeSubmitBtn, true, "Scoring resume");
      try {
        await apiJson("/api/resume", {
          method: "POST",
          body: JSON.stringify({
            resumeText: text,
            fileName: uploadedFileName || "Pasted_Resume.txt",
            appendChat: true,
          }),
        });
        closeDialog("resume-dialog");
        if (activeChatCtrl) await activeChatCtrl.loadState();
        else window.location.href = "/chat";
      } catch (err) {
        resumeModalErr.innerHTML = `${ICONS.alert}<span>${esc(err.message)}</span>`;
        resumeModalErr.classList.remove("hidden");
      } finally {
        setBusy(resumeSubmitBtn, false);
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 5-Minute Mock Interview Modal
  // ---------------------------------------------------------------------------
  let interviewTimer = null;
  async function startMockInterview() {
    const bodyEl = document.getElementById("interview-dialog-body");
    const timerEl = document.getElementById("interview-timer");
    const roleId = (appState.profile && appState.profile.targetRole) || "software-developer";

    bodyEl.innerHTML = `<div style="display:flex; align-items:center; justify-content:center; gap:0.65rem; padding:2.5rem 0;">${SPINNER_HTML}<span>Loading interview questions...</span></div>`;
    openDialog("interview-dialog");

    const data = await apiJson(`/api/interview/questions?roleId=${encodeURIComponent(roleId)}`);
    const questions = data.questions || [];
    let idx = 0;
    let secondsLeft = 300;
    const answers = [];

    if (interviewTimer) clearInterval(interviewTimer);
    interviewTimer = setInterval(() => {
      secondsLeft--;
      const m = String(Math.floor(Math.max(0, secondsLeft) / 60)).padStart(2, "0");
      const s = String(Math.max(0, secondsLeft) % 60).padStart(2, "0");
      timerEl.textContent = `${m}:${s}`;
      if (secondsLeft <= 0) {
        clearInterval(interviewTimer);
        finish();
      }
    }, 1000);

    async function finish(btn) {
      clearInterval(interviewTimer);
      setBusy(btn, true, "Evaluating answers");
      const report = await apiJson("/api/interview", {
        method: "POST",
        body: JSON.stringify({ sessionId: appState.sessionId || "mock", roleId, answers, appendChat: true }),
      });
      bodyEl.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:1rem;">
          <div class="cp-subcard" style="padding:1.25rem; background:var(--accent-tint);">
            <div class="text-brand" style="font-size:0.8rem; font-weight:600;">Overall interview score</div>
            <div class="tabular-nums text-brand" style="font-size:2.2rem; font-weight:700; margin-top:0.2rem;">${report.overallScore} / 10</div>
          </div>
          <div class="cp-grid-4">
            <div class="cp-subcard" style="padding:0.7rem; text-align:center;"><div class="text-subtle" style="font-size:0.75rem;">Accuracy</div><strong class="tabular-nums">${report.contentAccuracyScore}/10</strong></div>
            <div class="cp-subcard" style="padding:0.7rem; text-align:center;"><div class="text-subtle" style="font-size:0.75rem;">Clarity</div><strong class="tabular-nums">${report.clarityScore}/10</strong></div>
            <div class="cp-subcard" style="padding:0.7rem; text-align:center;"><div class="text-subtle" style="font-size:0.75rem;">Confidence</div><strong class="tabular-nums">${report.confidenceScore}/10</strong></div>
            <div class="cp-subcard" style="padding:0.7rem; text-align:center;"><div class="text-subtle" style="font-size:0.75rem;">Communication</div><strong class="tabular-nums">${report.communicationScore}/10</strong></div>
          </div>
          <div class="cp-subcard" style="padding:0.9rem;">
            <div class="text-subtle" style="font-size:0.78rem; font-weight:500;">Example answer</div>
            <p style="margin:0.35rem 0 0; font-size:0.88rem; line-height:1.5;">${esc(report.idealAnswerForWeakest)}</p>
          </div>
          <button type="button" id="interview-done-btn" class="cp-btn cp-btn-primary">Save and close</button>
        </div>
      `;
      bodyEl.querySelector("#interview-done-btn").addEventListener("click", async () => {
        closeDialog("interview-dialog");
        if (activeChatCtrl) await activeChatCtrl.loadState();
      });
    }

    function renderQuestion() {
      const q = questions[idx];
      if (!q) return finish();
      bodyEl.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:1rem;">
          <div style="display:flex; justify-content:space-between; font-size:0.82rem;" class="text-muted tabular-nums">
            <span>Question ${idx + 1} of ${questions.length}</span>
            <span class="text-brand" style="font-weight:600;">${esc(q.category)}</span>
          </div>
          <div class="cp-progress-track"><div class="cp-progress-fill" style="width:${Math.round(((idx + 1) / questions.length) * 100)}%;"></div></div>
          <div class="cp-subcard" style="padding:1rem;">
            <p style="margin:0; font-size:1.05rem; font-weight:500; line-height:1.45;">${esc(q.question)}</p>
          </div>
          <textarea id="interview-answer-input" class="cp-textarea" rows="5" placeholder="Type your answer or use voice input..." autofocus></textarea>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <button type="button" id="interview-voice-btn" class="cp-btn cp-btn-outline cp-btn-sm">
              ${ICONS.mic}
              <span>Speak answer</span>
            </button>
            <button type="button" id="interview-skip-btn" class="cp-btn cp-btn-ghost cp-btn-sm">Skip question</button>
          </div>
          <button type="button" id="interview-next-btn" class="cp-btn cp-btn-primary">
            ${idx + 1 === questions.length ? "Finish and score" : "Submit and next"}
          </button>
        </div>
      `;

      const ansInput = bodyEl.querySelector("#interview-answer-input");
      const voiceBtn = bodyEl.querySelector("#interview-voice-btn");

      voiceBtn.addEventListener("click", () => {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRec) {
          const rec = new SpeechRec();
          rec.lang = "en-IN";
          voiceBtn.innerHTML = `${SPINNER_HTML}<span>Listening...</span>`;
          rec.onresult = (ev) => {
            const transcript = ev.results[0] && ev.results[0][0] ? ev.results[0][0].transcript : "";
            ansInput.value = (ansInput.value ? ansInput.value + " " : "") + transcript;
            voiceBtn.innerHTML = `${ICONS.mic}<span>Speak answer</span>`;
          };
          rec.onerror = () => { voiceBtn.innerHTML = `${ICONS.mic}<span>Speak answer</span>`; };
          rec.start();
        } else {
          voiceBtn.innerHTML = `${SPINNER_HTML}<span>Transcribing sample...</span>`;
          setTimeout(() => {
            ansInput.value = (ansInput.value ? ansInput.value + " " : "") +
              "In my project, I built modular Python Flask APIs with indexed SQLite queries and tested edge cases.";
            voiceBtn.innerHTML = `${ICONS.mic}<span>Speak answer</span>`;
          }, 900);
        }
      });

      bodyEl.querySelector("#interview-skip-btn").addEventListener("click", () => {
        answers.push({ questionId: q.id, userAnswer: "Skipped", timeSpentSeconds: 300 - secondsLeft });
        idx++;
        if (idx >= questions.length) finish();
        else renderQuestion();
      });

      const nextBtn = bodyEl.querySelector("#interview-next-btn");
      nextBtn.addEventListener("click", () => {
        if (!ansInput.value.trim()) {
          ansInput.focus();
          return;
        }
        answers.push({ questionId: q.id, userAnswer: ansInput.value.trim(), timeSpentSeconds: 300 - secondsLeft });
        idx++;
        if (idx >= questions.length) finish(nextBtn);
        else renderQuestion();
      });
    }

    renderQuestion();
  }

  // ---------------------------------------------------------------------------
  // Registration Modal (Phone OTP 7890, Google OAuth, Magic Link, 1-Click Demo)
  // ---------------------------------------------------------------------------
  const regErr = document.getElementById("reg-error");
  const authPanes = {
    phone: document.getElementById("auth-pane-phone"),
    google: document.getElementById("auth-pane-google"),
    magic_link: document.getElementById("auth-pane-magic"),
  };

  document.querySelectorAll("[data-auth-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const method = btn.getAttribute("data-auth-tab");
      document.querySelectorAll("[data-auth-tab]").forEach((b) => b.classList.toggle("active", b === btn));
      Object.entries(authPanes).forEach(([k, el]) => {
        if (el) el.classList.toggle("hidden", k !== method);
      });
    });
  });

  async function onRegistered(res) {
    appState.isRegistered = true;
    appState.user = res.user;
    updateNavRegistered(res.user);
    closeDialog("reg-dialog");
    if (activeChatCtrl) await activeChatCtrl.loadState();
    else if (document.body.dataset.page === "dashboard") window.location.reload();
  }

  const otpSendForm = document.getElementById("phone-otp-send-form");
  const otpVerifyForm = document.getElementById("phone-otp-verify-form");
  if (otpSendForm) {
    otpSendForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      regErr.classList.add("hidden");
      const btn = otpSendForm.querySelector('button[type="submit"]');
      setBusy(btn, true, "Sending OTP");
      try {
        const phone = document.getElementById("reg-phone-input").value.trim();
        await apiJson("/api/auth/phone/initiate", { method: "POST", body: JSON.stringify({ phone }) });
        otpSendForm.classList.add("hidden");
        otpVerifyForm.classList.remove("hidden");
      } catch (err) {
        regErr.innerHTML = `${ICONS.alert}<span>${esc(err.message)}</span>`;
        regErr.classList.remove("hidden");
      } finally {
        setBusy(btn, false);
      }
    });
  }
  if (otpVerifyForm) {
    otpVerifyForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = otpVerifyForm.querySelector('button[type="submit"]');
      setBusy(btn, true, "Verifying");
      try {
        const phone = document.getElementById("reg-phone-input").value.trim();
        const otp = document.getElementById("reg-otp-input").value.trim();
        const res = await apiJson("/api/auth/phone/verify", { method: "POST", body: JSON.stringify({ phone, otp }) });
        await onRegistered(res);
      } catch (err) {
        regErr.innerHTML = `${ICONS.alert}<span>${esc(err.message)}</span>`;
        regErr.classList.remove("hidden");
      } finally {
        setBusy(btn, false);
      }
    });
  }

  const googleBtn = document.getElementById("google-oauth-btn");
  if (googleBtn) {
    googleBtn.addEventListener("click", async () => {
      setBusy(googleBtn, true, "Signing in");
      try {
        const res = await apiJson("/api/auth/google", { method: "POST", body: JSON.stringify({}) });
        await onRegistered(res);
      } finally {
        setBusy(googleBtn, false);
      }
    });
  }

  const magicSendForm = document.getElementById("magic-link-send-form");
  const magicVerifyBox = document.getElementById("magic-link-verify-box");
  if (magicSendForm) {
    magicSendForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = magicSendForm.querySelector('button[type="submit"]');
      setBusy(btn, true, "Sending link");
      try {
        activeMagicEmail = document.getElementById("reg-email-input").value.trim();
        const res = await apiJson("/api/auth/magic-link/initiate", {
          method: "POST",
          body: JSON.stringify({ email: activeMagicEmail }),
        });
        activeMagicToken = res.mockTokenOrCode;
        document.getElementById("magic-link-msg").textContent = res.message;
        magicSendForm.classList.add("hidden");
        magicVerifyBox.classList.remove("hidden");
      } finally {
        setBusy(btn, false);
      }
    });
  }
  const magicVerifyBtn = document.getElementById("magic-link-verify-btn");
  if (magicVerifyBtn) {
    magicVerifyBtn.addEventListener("click", async () => {
      setBusy(magicVerifyBtn, true, "Signing in");
      try {
        const res = await apiJson("/api/auth/magic-link/verify", {
          method: "POST",
          body: JSON.stringify({ token: activeMagicToken, email: activeMagicEmail }),
        });
        await onRegistered(res);
      } finally {
        setBusy(magicVerifyBtn, false);
      }
    });
  }

  const instantDemoBtn = document.getElementById("instant-demo-verify-btn");
  if (instantDemoBtn) {
    instantDemoBtn.addEventListener("click", async () => {
      setBusy(instantDemoBtn, true, "Activating demo");
      try {
        const res = await apiJson("/api/auth/phone/verify", {
          method: "POST",
          body: JSON.stringify({ phone: "+91 98765 43210", otp: "7890", name: "Demo Student Pilot" }),
        });
        await onRegistered(res);
      } finally {
        setBusy(instantDemoBtn, false);
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Home Page: Copy Training Email
  // ---------------------------------------------------------------------------
  const copyEmailBtn = document.getElementById("copy-training-email");
  if (copyEmailBtn) {
    copyEmailBtn.addEventListener("click", () => {
      if (navigator.clipboard) {
        navigator.clipboard.writeText("training@careerpilot.ai");
        copyEmailBtn.innerHTML = `${ICONS.check}<span>Copied</span>`;
        setTimeout(() => { copyEmailBtn.textContent = "Copy"; }, 2000);
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Student Dashboard Tabs, Roadmap Task Toggles & DPDP Controls
  // ---------------------------------------------------------------------------
  document.querySelectorAll("[data-dash-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-dash-tab");
      document.querySelectorAll("[data-dash-tab]").forEach((b) => b.classList.toggle("active", b === btn));
      ["overview", "resume", "roadmap", "jobs", "interviews", "privacy"].forEach((name) => {
        const pane = document.getElementById(`dash-pane-${name}`);
        if (pane) pane.classList.toggle("hidden", name !== target);
      });
    });
  });

  document.querySelectorAll(".dash-task-checkbox").forEach((cb) => {
    cb.addEventListener("change", async () => {
      cb.disabled = true;
      try {
        await apiJson("/api/roadmap/toggle-task", {
          method: "POST",
          body: JSON.stringify({
            weekNumber: Number(cb.getAttribute("data-week")),
            taskId: cb.getAttribute("data-task"),
          }),
        });
        const labelSpan = cb.nextElementSibling;
        if (labelSpan) {
          labelSpan.style.textDecoration = cb.checked ? "line-through" : "none";
          labelSpan.style.opacity = cb.checked ? "0.6" : "1";
        }
      } finally {
        cb.disabled = false;
      }
    });
  });

  const cData = document.getElementById("consent-data-processing");
  const cWa = document.getElementById("consent-whatsapp");
  const cModel = document.getElementById("consent-model-training");
  [cData, cWa, cModel].forEach((el) => {
    if (!el) return;
    el.addEventListener("change", async () => {
      await apiJson("/api/dashboard/consent", {
        method: "POST",
        body: JSON.stringify({
          dataProcessing: cData.checked,
          whatsappUpdates: cWa.checked,
          modelTraining: cModel.checked,
        }),
      });
    });
  });

  const deleteBtn = document.getElementById("dpdp-delete-btn");
  if (deleteBtn) {
    deleteBtn.addEventListener("click", async () => {
      setBusy(deleteBtn, true, "Submitting");
      try {
        const res = await apiJson("/api/dashboard/delete", { method: "POST" });
        document.getElementById("dpdp-status-msg").textContent = res.message;
      } finally {
        setBusy(deleteBtn, false);
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Admin Dashboard Tabs & Feature Flag Persistence
  // ---------------------------------------------------------------------------
  document.querySelectorAll("[data-admin-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-admin-tab");
      document.querySelectorAll("[data-admin-tab]").forEach((b) => b.classList.toggle("active", b === btn));
      ["funnel", "flags", "resources", "audit"].forEach((name) => {
        const pane = document.getElementById(`admin-pane-${name}`);
        if (pane) pane.classList.toggle("hidden", name !== target);
      });
    });
  });

  document.querySelectorAll(".admin-flag-toggle").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const key = btn.getAttribute("data-flag");
      const curr = btn.getAttribute("data-val") === "true";
      const next = !curr;
      setBusy(btn, true, "Saving");
      try {
        await apiJson("/api/admin/flags", {
          method: "POST",
          body: JSON.stringify({ key, value: next }),
        });
        btn.setAttribute("data-val", String(next));
        btn.classList.toggle("cp-btn-primary", next);
        btn.classList.toggle("cp-btn-outline", !next);
        delete btn.dataset.origHtml;
        btn.disabled = false;
        btn.removeAttribute("aria-busy");
        btn.textContent = next ? "Enabled" : "Disabled";
      } catch (_) {
        setBusy(btn, false);
      }
    });
  });
})();
