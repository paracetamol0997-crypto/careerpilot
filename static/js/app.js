/* CareerPilot AI — Client Controller (Flask + SQLite edition) */
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
  // Native <dialog> Modals + closedby="any" fallback (Modern Web Guidance)
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
  // Utility Helpers
  // ---------------------------------------------------------------------------
  function esc(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
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
    slot.innerHTML = `<a href="/dashboard" class="cp-verified-pill">✓ ${esc(user.name || "Profile")}</a>`;
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
      this.renderShell();
      this.loadState();
    }

    renderShell() {
      this.root.innerHTML = `
        <div class="cp-chat-status">
          <div style="display:flex; align-items:center; gap:0.5rem;">
            <span style="width:0.5rem; height:0.5rem; border-radius:999px; background:var(--status-pass); display:inline-block;"></span>
            <span class="text-muted" id="cp-status-text">CareerPilot Advisor Ready</span>
          </div>
          <button type="button" id="cp-reset-chat-btn" class="cp-badge" style="cursor:pointer;">↺ Reset</button>
        </div>
        <div class="cp-chat-feed" id="cp-chat-feed"></div>
        <form class="cp-chat-input-bar" id="cp-chat-form">
          <button type="button" id="cp-open-resume-btn" class="cp-btn cp-btn-outline cp-btn-sm" title="Upload or Paste Resume">📄</button>
          <input type="text" id="cp-chat-input" class="cp-input" placeholder="Ask about resume fixes, roadmaps, or interview prep..." autocomplete="off" />
          <button type="submit" id="cp-chat-send" class="cp-btn cp-btn-primary cp-btn-sm">Send →</button>
        </form>
      `;

      this.feedEl = this.root.querySelector("#cp-chat-feed");
      this.statusEl = this.root.querySelector("#cp-status-text");
      this.inputEl = this.root.querySelector("#cp-chat-input");
      this.formEl = this.root.querySelector("#cp-chat-form");

      this.root.querySelector("#cp-open-resume-btn").addEventListener("click", () => {
        openDialog("resume-dialog");
      });

      this.root.querySelector("#cp-reset-chat-btn").addEventListener("click", async () => {
        const res = await apiJson("/api/chat/reset", { method: "POST" });
        appState.messages = res.messages;
        this.renderMessages();
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
        this.statusEl.innerHTML = `<strong>${esc(appState.profile.branch)}</strong> (${esc(appState.profile.year)} Yr) · Target: <strong class="text-brand">${esc(appState.profile.targetRole)}</strong>`;
      } else {
        this.statusEl.textContent = "CareerPilot Advisor Ready";
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
      msgs.forEach((msg) => {
        const row = document.createElement("div");
        row.className = `cp-msg-row ${msg.sender === "user" ? "user" : "bot"}`;

        const tag = document.createElement("div");
        tag.className = "font-mono text-subtle";
        tag.style.fontSize = "0.68rem";
        tag.textContent = msg.sender === "user" ? "You" : "CP/ CareerPilot Guide";
        row.appendChild(tag);

        const bubble = document.createElement("div");
        bubble.className = "cp-msg-bubble";
        bubble.textContent = msg.text || "Formulating guidance...";
        row.appendChild(bubble);

        if (msg.cardPayload) {
          const cardWrap = document.createElement("div");
          cardWrap.style.width = "100%";
          cardWrap.style.maxWidth = "34rem";
          cardWrap.style.marginTop = "0.4rem";
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
            btn.addEventListener("click", () => this.handleChip(chip));
            chipsRow.appendChild(btn);
          });
          row.appendChild(chipsRow);
        }

        this.feedEl.appendChild(row);
      });

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
                  <strong>Mistake #${m.id}: ${esc(m.title)}</strong>
                  <p style="font-size:0.75rem;">${esc(m.whatIsWrong)}</p>
                </div>
                <div class="cp-locked-overlay">
                  <strong style="font-size:0.8rem;">🔒 Mistake #${m.id} Locked (Guest Preview)</strong>
                  <p class="text-muted" style="font-size:0.72rem; margin:0.25rem 0 0.5rem;">Free sign-up unlocks exact before/after bullet rewrites.</p>
                  <button type="button" class="cp-btn cp-btn-primary cp-btn-sm" data-open-reg-inline>Unlock Mistake #${m.id}</button>
                </div>
              </div>
            `;
          }
          return `
            <div style="border:1px solid var(--border-subtle); border-radius:0.6rem; padding:0.85rem; background:var(--surface-base); display:flex; flex-direction:column; gap:0.5rem;">
              <div style="display:flex; align-items:center; gap:0.5rem; font-weight:600; font-size:0.85rem;">
                <span class="cp-badge" style="background:var(--accent-brand); color:#fff;">#${m.id}</span>
                <span>${esc(m.title)}</span>
              </div>
              <div class="text-muted" style="font-size:0.78rem; line-height:1.45;">
                <div><strong>Issue:</strong> ${esc(m.whatIsWrong)}</div>
                <div><strong>Impact:</strong> ${esc(m.whyItHurts)}</div>
                <div><strong class="text-brand">Fix:</strong> ${esc(m.howToFix)}</div>
              </div>
              <div style="border:1px solid var(--border-subtle); border-radius:0.45rem; overflow:hidden; font-family:var(--font-mono); font-size:0.72rem;">
                <div style="background:var(--status-fix-bg); padding:0.55rem; border-bottom:1px solid var(--border-subtle);">
                  <strong class="text-fix">- Before:</strong> ${esc(m.beforeExample)}
                </div>
                <div style="background:var(--status-pass-bg); padding:0.55rem;">
                  <strong class="text-pass">+ After:</strong> ${esc(m.afterExample)}
                </div>
              </div>
            </div>
          `;
        })
        .join("");

      const b = res.breakdown || {};
      const pillars = [
        ["Target Keyword Match", b.keywordMatch || 0, 30],
        ["Formatting & Parseability", b.formatting || 0, 20],
        ["Quantified Impact", b.quantifiedImpact || 0, 20],
        ["Section Completeness", b.sectionCompleteness || 0, 15],
        ["Length & Clarity", b.lengthAndClarity || 0, 15],
      ]
        .map(
          ([label, sc, mx]) => `
            <div>
              <div style="display:flex; justify-content:space-between; font-size:0.75rem; margin-bottom:0.25rem;">
                <span>${label}</span><span class="font-mono text-brand">${sc} / ${mx}</span>
              </div>
              <div class="cp-progress-track"><div class="cp-progress-fill" style="width:${Math.round((sc / mx) * 100)}%;"></div></div>
            </div>
          `
        )
        .join("");

      return `
        <div class="cp-card" style="padding:1.15rem; display:flex; flex-direction:column; gap:1rem;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem;">
            <div>
              <div class="cp-section-label">ATS Audit Report</div>
              <div style="font-weight:600; font-size:1rem; margin-top:0.2rem;">Target: <span class="text-brand">${esc(res.targetRole)}</span></div>
            </div>
            <div style="text-align:center; border:1px solid var(--border-subtle); border-radius:0.55rem; padding:0.45rem 0.85rem; background:var(--surface-base);">
              <div class="font-mono tabular-nums ${scoreColor}" style="font-size:1.5rem; font-weight:700;">${res.score}</div>
              <div class="font-mono text-subtle" style="font-size:0.62rem;">/ 100 ATS</div>
            </div>
          </div>
          <div style="border-left:3px solid var(--accent-brand); padding:0.5rem 0.75rem; background:var(--surface-base); font-size:0.8rem;">
            ${esc(res.verdict)}
          </div>
          <div class="cp-tabs">
            <button type="button" class="cp-tab-btn ${this.activeResumeTab === "mistakes" ? "active" : ""}" data-card-resume-tab="mistakes">3 Fixable Mistakes</button>
            <button type="button" class="cp-tab-btn ${this.activeResumeTab === "breakdown" ? "active" : ""}" data-card-resume-tab="breakdown">Score Rubric</button>
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
                  <strong style="font-size:0.8rem;">🔒 Week ${wk.weekNumber} Locked (Guest Preview)</strong>
                  <p class="text-muted" style="font-size:0.72rem; margin:0.25rem 0 0.5rem;">Sign up free to unlock Weeks 3–12.</p>
                  <button type="button" class="cp-btn cp-btn-primary cp-btn-sm" data-open-reg-inline>Unlock 12 Weeks Free</button>
                </div>
              </div>
            `;
          }
          const tasksHtml = (wk.tasks || [])
            .map(
              (t) => `
                <label style="display:flex; align-items:center; gap:0.5rem; font-size:0.76rem; padding:0.35rem 0.5rem; border:1px solid var(--border-subtle); border-radius:0.4rem; background:var(--surface-card); cursor:pointer;">
                  <input type="checkbox" class="chat-rm-task" data-week="${wk.weekNumber}" data-task="${esc(t.id)}" ${t.completed ? "checked" : ""} />
                  <span style="${t.completed ? "text-decoration:line-through; opacity:0.6;" : ""}">${esc(t.title)}</span>
                </label>
              `
            )
            .join("");

          return `
            <div style="border:1px solid var(--border-subtle); border-radius:0.6rem; padding:0.85rem; background:var(--surface-base); display:flex; flex-direction:column; gap:0.5rem;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="font-mono text-brand" style="font-size:0.7rem; font-weight:600;">WEEK ${wk.weekNumber}</span>
                <span class="cp-badge">${esc(wk.phase)}</span>
              </div>
              <strong style="font-size:0.88rem;">${esc(wk.title)}</strong>
              <p class="text-muted" style="margin:0; font-size:0.76rem;">${esc(wk.description)}</p>
              <div style="display:flex; flex-direction:column; gap:0.35rem;">${tasksHtml}</div>
              <a href="${esc(wk.resourceUrl)}" target="_blank" rel="noopener noreferrer" class="font-mono text-brand" style="font-size:0.72rem;">
                ↗ Vetted Guide: ${esc(wk.resourceTitle)}
              </a>
            </div>
          `;
        })
        .join("");

      return `
        <div class="cp-card" style="padding:1.15rem; display:flex; flex-direction:column; gap:0.85rem;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div class="cp-section-label">90-Day Roadmap</div>
              <div style="font-weight:600; font-size:1rem; margin-top:0.2rem;"><span class="text-brand">${esc(rm.role)}</span> Syllabus</div>
            </div>
            <span class="cp-badge tabular-nums">${rm.progressPercent || 0}% Done</span>
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
          <div style="display:flex; flex-direction:column; gap:0.7rem; max-height:24rem; overflow-y:auto;">${weeksHtml}</div>
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
              <div style="border:1px solid var(--status-fix-border); background:var(--status-fix-bg); border-radius:0.6rem; padding:0.85rem; display:flex; flex-direction:column; gap:0.4rem;">
                <div class="font-mono text-fix" style="font-size:0.7rem; font-weight:700;">⚠ SUSPICIOUS POSTING FLAGGED</div>
                <strong style="text-decoration:line-through; opacity:0.8; font-size:0.85rem;">${esc(job.title)}</strong>
                <div class="text-muted" style="font-size:0.75rem;">${esc(job.company)}</div>
                <ul style="margin:0.25rem 0; padding-left:1.1rem; font-size:0.74rem;" class="text-fix">
                  ${(job.scamReasons || []).map((r) => `<li>${esc(r)}</li>`).join("")}
                </ul>
                <button type="button" class="cp-btn cp-btn-sm cp-btn-danger report-job-btn" data-job-id="${esc(job.id)}" style="align-self:flex-start;">
                  Report Listing
                </button>
              </div>
            `;
          }

          const isSaved = savedIds.has(job.id);
          return `
            <div style="border:1px solid var(--border-subtle); background:var(--surface-base); border-radius:0.6rem; padding:0.85rem; display:flex; flex-direction:column; gap:0.5rem;">
              <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:0.5rem;">
                <div>
                  <strong style="font-size:0.86rem;">${esc(job.title)}</strong>
                  <div class="text-muted" style="font-size:0.75rem;">${esc(job.company)} · ${esc(job.location)}</div>
                </div>
                <span class="cp-badge cp-badge-pass tabular-nums">${job.matchPercent}% Match</span>
              </div>
              ${
                job.hasCgpaFilter
                  ? `<div class="cp-badge cp-badge-warn" style="font-size:0.7rem;">Note: Employer requests ${job.minCgpaRequired}+ CGPA.</div>`
                  : ""
              }
              <p class="text-muted" style="margin:0; font-size:0.76rem;">${esc(job.whyItMatches)}</p>
              <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid var(--border-subtle); padding-top:0.5rem;">
                <span class="font-mono" style="font-size:0.76rem; font-weight:600;">${esc(job.salaryRange)}</span>
                <div style="display:flex; gap:0.4rem;">
                  <button type="button" class="cp-btn cp-btn-outline cp-btn-sm save-job-btn" data-job-json='${esc(JSON.stringify(job))}'>
                    ${isSaved ? "★ Saved" : "☆ Save"}
                  </button>
                  <a href="${esc(job.applyUrl)}" target="_blank" rel="noopener noreferrer" class="cp-btn cp-btn-primary cp-btn-sm">Apply ↗</a>
                </div>
              </div>
            </div>
          `;
        })
        .join("");

      return `
        <div class="cp-card" style="padding:1.15rem; display:flex; flex-direction:column; gap:0.85rem;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <div class="cp-section-label">Verified Roles</div>
              <div style="font-weight:600; font-size:1rem;">Curated Fresher Openings</div>
            </div>
            <span class="cp-badge">${(jobs || []).length} Matches</span>
          </div>
          <div style="display:flex; gap:0.4rem;">
            ${["all", "Fresher", "Internship"]
              .map(
                (t) =>
                  `<button type="button" class="cp-chip ${this.activeJobsFilter === t ? "cp-btn-primary" : ""}" data-job-filter="${t}">${t === "all" ? "All" : t}</button>`
              )
              .join("")}
          </div>
          <div style="display:flex; flex-direction:column; gap:0.7rem; max-height:24rem; overflow-y:auto;">${jobsHtml}</div>
        </div>
      `;
    }

    renderInterviewSummaryCard(rep) {
      return `
        <div class="cp-card" style="padding:1rem; display:flex; flex-direction:column; gap:0.5rem;">
          <div class="cp-section-label">Mock Interview Complete</div>
          <div class="font-mono text-brand" style="font-size:1.5rem; font-weight:700;">${rep.overallScore} / 10</div>
          <div class="text-muted" style="font-size:0.78rem;">Model improvement tip: ${esc(rep.nextRoadmapAction)}</div>
          <a href="/dashboard" class="cp-btn cp-btn-outline cp-btn-sm" style="align-self:flex-start;">View Full Report in My Space →</a>
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
        });
      });
      this.feedEl.querySelectorAll(".save-job-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const job = JSON.parse(btn.getAttribute("data-job-json"));
          const res = await apiJson("/api/jobs/save", {
            method: "POST",
            body: JSON.stringify({ job }),
          });
          appState.savedJobs = res.savedJobs;
          this.renderMessages();
        });
      });
      this.feedEl.querySelectorAll(".report-job-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const jobId = btn.getAttribute("data-job-id");
          await apiJson("/api/jobs/report", {
            method: "POST",
            body: JSON.stringify({ jobId }),
          });
          btn.textContent = "Reported ✓";
          btn.disabled = true;
        });
      });
    }

    async handleChip(chip) {
      if (chip.value === "feature_resume") return openDialog("resume-dialog");
      if (chip.value === "feature_roadmap") return this.triggerRoadmap();
      if (chip.value === "feature_jobs") return this.triggerJobs();
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

    executeIntent(intent) {
      if (intent === "resume_check") {
        openDialog("resume-dialog");
      } else if (intent === "roadmap") {
        this.triggerRoadmap();
      } else if (intent === "jobs") {
        this.triggerJobs();
      } else if (intent === "mock_interview") {
        if (!appState.isRegistered) openDialog("reg-dialog");
        else startMockInterview();
      }
    }

    async triggerRoadmap() {
      await apiJson("/api/roadmap", { method: "POST", body: JSON.stringify({ appendChat: true }) });
      await this.loadState();
    }

    async triggerJobs() {
      await apiJson("/api/jobs", { method: "POST", body: JSON.stringify({ appendChat: true }) });
      await this.loadState();
    }

    async sendUserMessage(text) {
      this.isTyping = true;
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
        botMsg.text = "I'm ready to guide you! Choose ATS Resume Review, 90-Day Roadmap, Matched Jobs, or Mock Interview.";
        this.renderMessages();
      } finally {
        this.isTyping = false;
        await this.loadState();
      }
    }
  }

  let activeChatCtrl = null;
  const fullChatRoot = document.getElementById("full-chat-root");
  if (fullChatRoot) {
    activeChatCtrl = new ChatWidgetController(fullChatRoot, false);
  }

  // Floating Chat Widget on Home Page
  const floatingOpenBtn = document.getElementById("floating-open-btn");
  const floatingCloseBtn = document.getElementById("floating-close-btn");
  const floatingPanel = document.getElementById("floating-panel");
  const embeddedRoot = document.getElementById("embedded-chat-root");

  function openFloatingWidget(intent) {
    if (!floatingPanel || !embeddedRoot) {
      window.location.href = intent ? `/chat?intent=${encodeURIComponent(intent)}` : "/chat";
      return;
    }
    floatingOpenBtn.classList.add("hidden");
    floatingPanel.classList.remove("hidden");
    if (!activeChatCtrl) {
      activeChatCtrl = new ChatWidgetController(embeddedRoot, true);
    }
    if (intent) {
      setTimeout(() => activeChatCtrl.executeIntent(intent), 250);
    }
  }

  if (floatingOpenBtn) {
    floatingOpenBtn.addEventListener("click", () => openFloatingWidget(null));
  }
  if (floatingCloseBtn) {
    floatingCloseBtn.addEventListener("click", () => {
      floatingPanel.classList.add("hidden");
      floatingOpenBtn.classList.remove("hidden");
    });
  }

  document.querySelectorAll("[data-launch-intent]").forEach((el) => {
    el.addEventListener("click", () => {
      const intent = el.getAttribute("data-launch-intent");
      if (window.innerWidth < 640) {
        window.location.href = `/chat?intent=${encodeURIComponent(intent)}`;
      } else {
        openFloatingWidget(intent);
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
      resumeFileLabel.textContent = `Uploading & scanning ${file.name}...`;

      const formData = new FormData();
      formData.append("file", file);
      try {
        const res = await fetch("/api/upload", { method: "POST", body: formData });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Upload failed");
        uploadedFileName = data.securityCheck.sanitizedFilename;
        resumeTextInput.value = data.extractedText && data.extractedText.length > 20 ? data.extractedText : SAMPLE_RESUME;
        resumeFileLabel.textContent = `✓ Verified & Extracted: ${uploadedFileName}`;
      } catch (err) {
        resumeModalErr.textContent = err.message;
        resumeModalErr.classList.remove("hidden");
        resumeFileLabel.textContent = "Click to choose a PDF, DOCX, or TXT file";
      }
    });
  }

  const resumeForm = document.getElementById("resume-audit-form");
  if (resumeForm) {
    resumeForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = resumeTextInput.value.trim();
      if (text.length < 10) {
        resumeModalErr.textContent = "Please paste resume content (or insert sample resume).";
        resumeModalErr.classList.remove("hidden");
        return;
      }
      resumeModalErr.classList.add("hidden");
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
    });
  }

  // ---------------------------------------------------------------------------
  // 5-Minute Mock Interview Modal (with Web Speech STT + Fallback)
  // ---------------------------------------------------------------------------
  let interviewTimer = null;
  async function startMockInterview() {
    const bodyEl = document.getElementById("interview-dialog-body");
    const timerEl = document.getElementById("interview-timer");
    const roleId = (appState.profile && appState.profile.targetRole) || "software-developer";
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
      timerEl.textContent = `⏱ ${m}:${s}`;
      if (secondsLeft <= 0) {
        clearInterval(interviewTimer);
        finish();
      }
    }, 1000);

    async function finish() {
      clearInterval(interviewTimer);
      const report = await apiJson("/api/interview", {
        method: "POST",
        body: JSON.stringify({ sessionId: appState.sessionId || "mock", roleId, answers, appendChat: true }),
      });
      bodyEl.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:1rem;">
          <div class="cp-manifesto" style="padding:1.25rem;">
            <div class="font-mono" style="font-size:0.7rem; opacity:0.8;">OVERALL INTERVIEW SCORE</div>
            <div class="font-mono tabular-nums" style="font-size:2.2rem; font-weight:700;">${report.overallScore} / 10</div>
          </div>
          <div class="cp-grid-4">
            <div class="cp-card" style="padding:0.65rem; text-align:center;"><div class="font-mono text-subtle" style="font-size:0.65rem;">Accuracy</div><strong>${report.contentAccuracyScore}/10</strong></div>
            <div class="cp-card" style="padding:0.65rem; text-align:center;"><div class="font-mono text-subtle" style="font-size:0.65rem;">Clarity</div><strong>${report.clarityScore}/10</strong></div>
            <div class="cp-card" style="padding:0.65rem; text-align:center;"><div class="font-mono text-subtle" style="font-size:0.65rem;">Confidence</div><strong>${report.confidenceScore}/10</strong></div>
            <div class="cp-card" style="padding:0.65rem; text-align:center;"><div class="font-mono text-subtle" style="font-size:0.65rem;">Comm.</div><strong>${report.communicationScore}/10</strong></div>
          </div>
          <div class="cp-card" style="background:var(--surface-base); padding:0.85rem;">
            <div class="font-mono text-subtle" style="font-size:0.68rem;">MODEL ANSWER EXAMPLE</div>
            <p class="font-display" style="font-style:italic; margin:0.35rem 0 0; font-size:0.85rem;">"${esc(report.idealAnswerForWeakest)}"</p>
          </div>
          <button type="button" id="interview-done-btn" class="cp-btn cp-btn-primary">Done &amp; Save to My Space</button>
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
          <div style="display:flex; justify-content:space-between; font-size:0.75rem;" class="font-mono text-muted">
            <span>Question ${idx + 1} of ${questions.length}</span>
            <span class="text-brand">${esc(q.category)}</span>
          </div>
          <div class="cp-progress-track"><div class="cp-progress-fill" style="width:${Math.round(((idx + 1) / questions.length) * 100)}%;"></div></div>
          <div class="cp-card" style="background:var(--surface-base); padding:1rem;">
            <p class="font-display" style="margin:0; font-size:1.1rem; line-height:1.4;">${esc(q.question)}</p>
          </div>
          <textarea id="interview-answer-input" class="cp-textarea" rows="5" placeholder="Type your answer or click Speak Answer..." autofocus></textarea>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <button type="button" id="interview-voice-btn" class="cp-chip">🎙 Speak Answer (Voice)</button>
            <button type="button" id="interview-skip-btn" style="border:none; background:none; color:var(--text-muted); cursor:pointer; font-size:0.78rem;">Skip Question →</button>
          </div>
          <button type="button" id="interview-next-btn" class="cp-btn cp-btn-cta">
            ${idx + 1 === questions.length ? "Finish & Generate Report" : "Submit & Next Question"} →
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
          voiceBtn.textContent = "🔴 Listening...";
          rec.onresult = (ev) => {
            const transcript = ev.results[0] && ev.results[0][0] ? ev.results[0][0].transcript : "";
            ansInput.value = (ansInput.value ? ansInput.value + " " : "") + transcript;
            voiceBtn.textContent = "🎙 Speak Answer (Voice)";
          };
          rec.onerror = () => { voiceBtn.textContent = "🎙 Speak Answer (Voice)"; };
          rec.start();
        } else {
          voiceBtn.textContent = "🎙 Simulating Voice...";
          setTimeout(() => {
            ansInput.value = (ansInput.value ? ansInput.value + " " : "") +
              "In my project, I built modular Python Flask APIs with indexed SQLite queries and tested edge cases.";
            voiceBtn.textContent = "🎙 Speak Answer (Voice)";
          }, 900);
        }
      });

      bodyEl.querySelector("#interview-skip-btn").addEventListener("click", () => {
        answers.push({ questionId: q.id, userAnswer: "Skipped", timeSpentSeconds: 300 - secondsLeft });
        idx++;
        renderQuestion();
      });

      bodyEl.querySelector("#interview-next-btn").addEventListener("click", () => {
        if (!ansInput.value.trim()) return;
        answers.push({ questionId: q.id, userAnswer: ansInput.value.trim(), timeSpentSeconds: 300 - secondsLeft });
        idx++;
        renderQuestion();
      });
    }

    renderQuestion();
    openDialog("interview-dialog");
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
      const phone = document.getElementById("reg-phone-input").value.trim();
      await apiJson("/api/auth/phone/initiate", { method: "POST", body: JSON.stringify({ phone }) });
      otpSendForm.classList.add("hidden");
      otpVerifyForm.classList.remove("hidden");
    });
  }
  if (otpVerifyForm) {
    otpVerifyForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const phone = document.getElementById("reg-phone-input").value.trim();
        const otp = document.getElementById("reg-otp-input").value.trim();
        const res = await apiJson("/api/auth/phone/verify", { method: "POST", body: JSON.stringify({ phone, otp }) });
        await onRegistered(res);
      } catch (err) {
        regErr.textContent = err.message;
        regErr.classList.remove("hidden");
      }
    });
  }

  const googleBtn = document.getElementById("google-oauth-btn");
  if (googleBtn) {
    googleBtn.addEventListener("click", async () => {
      const res = await apiJson("/api/auth/google", { method: "POST", body: JSON.stringify({}) });
      await onRegistered(res);
    });
  }

  const magicSendForm = document.getElementById("magic-link-send-form");
  const magicVerifyBox = document.getElementById("magic-link-verify-box");
  if (magicSendForm) {
    magicSendForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      activeMagicEmail = document.getElementById("reg-email-input").value.trim();
      const res = await apiJson("/api/auth/magic-link/initiate", {
        method: "POST",
        body: JSON.stringify({ email: activeMagicEmail }),
      });
      activeMagicToken = res.mockTokenOrCode;
      document.getElementById("magic-link-msg").textContent = res.message;
      magicSendForm.classList.add("hidden");
      magicVerifyBox.classList.remove("hidden");
    });
  }
  const magicVerifyBtn = document.getElementById("magic-link-verify-btn");
  if (magicVerifyBtn) {
    magicVerifyBtn.addEventListener("click", async () => {
      const res = await apiJson("/api/auth/magic-link/verify", {
        method: "POST",
        body: JSON.stringify({ token: activeMagicToken, email: activeMagicEmail }),
      });
      await onRegistered(res);
    });
  }

  const instantDemoBtn = document.getElementById("instant-demo-verify-btn");
  if (instantDemoBtn) {
    instantDemoBtn.addEventListener("click", async () => {
      const res = await apiJson("/api/auth/phone/verify", {
        method: "POST",
        body: JSON.stringify({ phone: "+91 98765 43210", otp: "7890", name: "Demo Student Pilot" }),
      });
      await onRegistered(res);
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
        copyEmailBtn.textContent = "Copied ✓";
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
      const res = await apiJson("/api/dashboard/delete", { method: "POST" });
      document.getElementById("dpdp-status-msg").textContent = res.message;
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
      await apiJson("/api/admin/flags", {
        method: "POST",
        body: JSON.stringify({ key, value: next }),
      });
      btn.setAttribute("data-val", String(next));
      btn.classList.toggle("cp-btn-primary", next);
      btn.classList.toggle("cp-btn-outline", !next);
      btn.textContent = key === "lockAtsMistakes2and3" ? (next ? "🔒 Enabled" : "🔓 Disabled") : (next ? "Enabled" : "Disabled");
    });
  });
})();
