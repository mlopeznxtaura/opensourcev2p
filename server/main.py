"""FastAPI cloud platform.

Endpoints accept already-encrypted blobs OR plaintext+key-header (dev only).
Identity resolution NEVER happens here — see sidecar/.
"""
from __future__ import annotations

import base64
import json
import time

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, Response
from fpdf import FPDF
from pydantic import BaseModel, Field

from . import auth, crypto, planner, storage

app = FastAPI(title="Zero Trust Pastoral Platform", version="2.0p")


class StoreIn(BaseModel):
    care_id: str = Field(min_length=8, max_length=128)
    ciphertext_b64: str | None = None
    plaintext: str | None = None  # dev only


class StoreOut(BaseModel):
    stored: bool
    record_id: int
    content_hash: str


class PlanIn(BaseModel):
    transcript: str = Field(min_length=3, max_length=120000)
    mode: str = Field(default="pastoral_confession")


def _bearer(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer")
    try:
        return auth.verify_token(authorization.split(" ", 1)[1])
    except Exception:
        raise HTTPException(401, "bad token")


@app.get("/health")
def health():
    return {"status": "online", "version": "2.0p"}


@app.get("/", response_class=HTMLResponse)
def root():
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Voice to Plan</title>
    <style>
      :root {
        --carbon-ink: #101112;
        --dust-paper: #E8E0D3;
        --paper-2: #F4EEE3;
        --archive-green: #6F8767;
        --oxide-red: #9D4A42;
        --midnight-navy: #1F2945;
        --soft-gold: #C8B47D;
        --electric-cyan: #5BE0FF;
        --line: rgba(16,17,18,0.12);
        --line-strong: rgba(16,17,18,0.22);
        --panel: rgba(255,255,255,0.78);
        --panel-soft: rgba(255,255,255,0.56);
      }
      * { box-sizing: border-box; }
      html, body { height: 100%; }
      body {
        margin: 0;
        font-family: "Inter", "SF Pro Display", "Segoe UI", Arial, sans-serif;
        color: var(--carbon-ink);
        background:
          radial-gradient(980px 440px at 84% 0%, rgba(31,41,69,0.22), transparent 66%),
          radial-gradient(1200px 520px at 100% -20%, rgba(91,224,255,0.20), transparent 62%),
          radial-gradient(940px 440px at -10% 110%, rgba(157,74,66,0.14), transparent 58%),
          linear-gradient(165deg, #F6F1E8 0%, #EDE4D6 48%, #E4D8C7 100%);
      }
      .shell {
        max-width: 1180px;
        margin: 32px auto;
        padding: 24px;
      }
      .brandbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        padding: 14px 18px;
        border: 1px solid rgba(16,17,18,0.08);
        border-bottom: 0;
        border-radius: 14px 14px 0 0;
        background: linear-gradient(180deg, rgba(236,233,236,0.95), rgba(230,224,222,0.90));
      }
      .brand-left {
        display: flex;
        align-items: center;
        gap: 12px;
        min-width: 0;
      }
      .brand-diamond {
        width: 12px;
        height: 12px;
        border-radius: 2px;
        background: #5BE0FF;
        transform: rotate(45deg);
        flex: 0 0 auto;
      }
      .brand-title {
        margin: 0;
        font-size: 33px;
        line-height: 1;
        font-weight: 760;
        letter-spacing: -0.03em;
        color: #1B1C1F;
      }
      .brand-right {
        margin: 0;
        font-size: 12px;
        font-weight: 540;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: rgba(16,17,18,0.42);
        white-space: nowrap;
      }
      .app {
        border: 1px solid var(--line);
        border-radius: 0 0 26px 26px;
        padding: 28px;
        background: linear-gradient(180deg, rgba(251,250,255,0.86), rgba(246,241,236,0.78));
        box-shadow:
          inset 0 1px 0 rgba(255,255,255,0.62),
          0 30px 70px rgba(31, 24, 16, 0.16);
        backdrop-filter: blur(10px) saturate(108%);
      }
      .header {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 18px;
        margin-bottom: 20px;
      }
      .title {
        margin: 0;
        font-size: clamp(30px, 5vw, 42px);
        font-weight: 720;
        letter-spacing: -0.03em;
        color: #18213A;
      }
      .subtitle {
        margin: 6px 0 0;
        color: rgba(31,41,69,0.72);
        font-size: 13px;
        max-width: 660px;
        line-height: 1.55;
      }
      .pill {
        display: inline-flex;
        gap: 7px;
        align-items: center;
        border: 1px solid rgba(91,224,255,0.74);
        color: #0D3F49;
        background: rgba(91,224,255,0.22);
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 560;
      }
      h2 {
        margin: 0 0 10px;
        font-size: 14px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #27324F;
        font-weight: 610;
      }
      h3 {
        margin: 0 0 10px;
        font-size: 14px;
        color: #27324F;
        font-weight: 610;
      }
      .input-wrap, .result-wrap {
        border: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(246,246,252,0.66), rgba(255,255,255,0.52));
        border-radius: 16px;
        padding: 16px;
        margin-top: 14px;
        position: relative;
      }
      .input-wrap:before, .result-wrap:before {
        content: "";
        position: absolute;
        left: 12px;
        right: 12px;
        top: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(91,224,255,0.62), transparent);
      }
      select, textarea, .dropzone {
        width: 100%;
        color: var(--carbon-ink);
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.85);
        border-radius: 12px;
        transition: border-color 120ms ease, box-shadow 120ms ease, background 160ms ease;
      }
      select:focus, textarea:focus {
        outline: none;
        border-color: rgba(31,41,69,0.42);
        box-shadow: 0 0 0 3px rgba(31,41,69,0.16), 0 0 0 6px rgba(91,224,255,0.16);
      }
      select {
        padding: 12px;
        max-width: 390px;
      }
      textarea {
        min-height: 220px;
        resize: vertical;
        padding: 14px;
        line-height: 1.55;
      }
      .dropzone {
        margin-top: 10px;
        border-style: dashed;
        text-align: center;
        color: rgba(16,17,18,0.58);
        padding: 16px;
      }
      .dropzone.active {
        border-color: rgba(91,224,255,0.98);
        color: var(--carbon-ink);
        background: rgba(91,224,255,0.20);
      }
      .row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 14px 0 8px;
      }
      button {
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 10px 14px;
        font-weight: 610;
        letter-spacing: 0.01em;
        cursor: pointer;
        color: #08232A;
        background: linear-gradient(180deg, #7CE9FF, #5BE0FF);
        box-shadow: 0 9px 20px rgba(91,224,255,0.28);
      }
      button:hover { filter: brightness(1.05); }
      button:active { transform: translateY(1px); }
      button.secondary {
        color: #2B2A27;
        border-color: rgba(31,41,69,0.22);
        background: linear-gradient(180deg, #E7EBF6, #DBDFEC);
        box-shadow: none;
      }
      button.warn {
        color: #3B1611;
        border-color: rgba(157,74,66,0.44);
        background: linear-gradient(180deg, #BE6D65, #9D4A42);
        box-shadow: 0 8px 18px rgba(157,74,66,0.20);
      }
      .muted {
        color: rgba(16,17,18,0.65);
        font-size: 13px;
      }
      #status.ok { color: #0D6A78; }
      .grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 14px;
      }
      .box {
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 14px;
        background: linear-gradient(180deg, rgba(249,250,255,0.86), rgba(255,255,255,0.72));
        box-shadow: inset 0 1px 0 rgba(31,41,69,0.05);
      }
      .box p { margin: 0 0 8px; }
      ul { margin: 6px 0 0 18px; line-height: 1.5; }
      .json-block {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: rgba(255,255,255,0.74);
        padding: 10px;
      }
      pre {
        margin: 0;
        max-height: 260px;
        overflow: auto;
        color: #1F2328;
        font-size: 12px;
        line-height: 1.5;
      }
      code { color: #145865; }
      .footer-note {
        margin-top: 10px;
        color: rgba(31,41,69,0.66);
        font-size: 12px;
      }
      @media (max-width: 940px) {
        .header { align-items: flex-start; flex-direction: column; }
        .grid { grid-template-columns: 1fr; }
        .brandbar { flex-direction: column; align-items: flex-start; }
        .brand-right { white-space: normal; }
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <div class="brandbar">
        <div class="brand-left">
          <span class="brand-diamond"></span>
          <h1 class="brand-title">VOICE TO PLAN v1</h1>
        </div>
        <p class="brand-right">Private intake · Action planning · Open-source</p>
      </div>
      <div class="app">
        <div class="header">
          <div>
            <p class="subtitle">Capture voice or text input and transform it into concise action plans for pastoral care, project execution, or safety reporting.</p>
          </div>
        </div>
        <div class="input-wrap">
          <h2>Use Case Mode</h2>
          <select id="mode">
            <option value="pastoral_confession">Private Pastoral Confessions -> Action Plans</option>
            <option value="project_management">Project Management -> Execution Plans</option>
            <option value="manufacturing_safety">Manufacturing Safety Reporting -> Corrective Plans</option>
          </select>
          <h2 style="margin-top:14px">Input</h2>
          <textarea id="transcript" placeholder="Speak with mic or paste transcript..."></textarea>
          <div id="dropzone" class="dropzone">Drag and drop files here (or click to pick). Text is appended to transcript.</div>
          <input id="fileInput" type="file" multiple style="display:none">
          <div class="row">
            <button onclick="startMic()">Start Mic</button>
            <button class="secondary" onclick="stopMic()">Stop Mic</button>
            <button onclick="generatePlan()">Generate Plan</button>
            <button class="warn" onclick="exportPdf()">Export PDF</button>
            <button class="secondary" onclick="exportJsonl()">Export JSONL</button>
          </div>
          <p id="status" class="muted">Ready.</p>
        </div>
        <div class="result-wrap">
          <h2>Plan Summary (Non-Technical)</h2>
          <div class="box">
            <h3>Problem Statement</h3>
            <p id="problem">No plan generated yet.</p>
            <p><strong>Risk:</strong> <span id="risk">-</span></p>
            <p><strong>Summary:</strong> <span id="summary">-</span></p>
          </div>
          <div class="grid" style="margin-top:14px;">
            <div class="box">
              <h3>Action Plan (Immediate)</h3>
              <p><strong>Tally:</strong> <span id="tally_immediate">0</span></p>
              <ul id="list_immediate"></ul>
            </div>
            <div class="box">
              <h3>Action Plan (This Week)</h3>
              <p><strong>Tally:</strong> <span id="tally_week">0</span></p>
              <ul id="list_week"></ul>
            </div>
          </div>
          <div class="box" style="margin-top:14px;">
            <h3>Follow-Ups</h3>
            <p><strong>Tally:</strong> <span id="tally_followup">0</span></p>
            <ul id="list_followup"></ul>
          </div>
          <h3 style="margin-top:14px;">JSON (technical view)</h3>
          <div class="json-block">
            <pre id="raw_json">No plan yet.</pre>
          </div>
          <p class="footer-note">API: <code>POST /v1/plan</code> | Exports: <code>/v1/export/pdf</code>, <code>/v1/export/jsonl</code></p>
        </div>
      </div>
    </div>
    <script>
      let recognition = null;
      let latestPlan = null;
      const modeSelect = document.getElementById("mode");
      const dropzone = document.getElementById("dropzone");
      const fileInput = document.getElementById("fileInput");
      const transcriptEl = document.getElementById("transcript");
      function triggerDownload(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1500);
      }
      function status(msg, good) {
        const el = document.getElementById("status");
        el.textContent = msg;
        el.className = good ? "ok" : "muted";
      }
      async function ingestFiles(fileList) {
        const files = Array.from(fileList || []);
        if (!files.length) return;
        const chunks = [];
        for (const f of files) {
          try {
            const text = await f.text();
            chunks.push("\\n\\n--- FILE: " + f.name + " ---\\n" + text);
          } catch (_) {
            chunks.push("\\n\\n--- FILE: " + f.name + " ---\\n[Unable to read as text]");
          }
        }
        transcriptEl.value = (transcriptEl.value + chunks.join("")).trim();
        status("File ingest complete (" + files.length + ").", true);
      }
      dropzone.addEventListener("click", () => fileInput.click());
      fileInput.addEventListener("change", (e) => ingestFiles(e.target.files));
      dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("active"); });
      dropzone.addEventListener("dragleave", () => dropzone.classList.remove("active"));
      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("active");
        ingestFiles(e.dataTransfer.files);
      });
      transcriptEl.addEventListener("paste", (e) => {
        const text = (e.clipboardData || window.clipboardData).getData("text");
        if (!text) return;
        e.preventDefault();
        const start = transcriptEl.selectionStart ?? transcriptEl.value.length;
        const end = transcriptEl.selectionEnd ?? transcriptEl.value.length;
        transcriptEl.value = transcriptEl.value.slice(0, start) + text + transcriptEl.value.slice(end);
        transcriptEl.selectionStart = transcriptEl.selectionEnd = start + text.length;
        status("Pasted input captured.", true);
      });
      function setList(id, items) {
        const list = document.getElementById(id);
        list.innerHTML = "";
        (items || []).forEach((x) => {
          const li = document.createElement("li");
          li.textContent = x;
          list.appendChild(li);
        });
      }
      function renderPlan(plan) {
        latestPlan = plan;
        document.getElementById("problem").textContent = plan.problem_statement || "-";
        document.getElementById("risk").textContent = plan.risk_level || "-";
        document.getElementById("summary").textContent = plan.summary || "-";
        document.getElementById("tally_immediate").textContent = plan.tally?.immediate ?? 0;
        document.getElementById("tally_week").textContent = plan.tally?.this_week ?? 0;
        document.getElementById("tally_followup").textContent = plan.tally?.follow_up ?? 0;
        setList("list_immediate", plan.plan?.immediate || []);
        setList("list_week", plan.plan?.this_week || []);
        setList("list_followup", plan.plan?.follow_up || []);
        document.getElementById("raw_json").textContent = JSON.stringify(plan, null, 2);
      }
      function startMic() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {
          status("Speech recognition unavailable in this browser. Type transcript manually.", false);
          return;
        }
        recognition = new SR();
        recognition.lang = "en-US";
        recognition.continuous = true;
        recognition.interimResults = true;
        const area = document.getElementById("transcript");
        recognition.onresult = (e) => {
          let text = "";
          for (let i = 0; i < e.results.length; i++) text += e.results[i][0].transcript + " ";
          area.value = text.trim();
        };
        recognition.onerror = () => status("Mic error. Check browser permissions.", false);
        recognition.onstart = () => status("Listening...", true);
        recognition.start();
      }
      function stopMic() {
        if (recognition) recognition.stop();
        status("Mic stopped.", false);
      }
      const MODE_UI = {
        pastoral_confession: {
          placeholder: "Speak with mic or paste a pastoral confession summary...",
          emptyMsg: "Please capture or type confession text first.",
        },
        project_management: {
          placeholder: "Describe project status, blockers, deadlines, and stakeholders...",
          emptyMsg: "Please capture or type project update text first.",
        },
        manufacturing_safety: {
          placeholder: "Describe the incident, hazard, location, equipment, and who was involved...",
          emptyMsg: "Please capture or type a safety report first.",
        },
      };
      function applyModeUi() {
        const cfg = MODE_UI[modeSelect.value] || MODE_UI.pastoral_confession;
        transcriptEl.placeholder = cfg.placeholder;
      }
      modeSelect.addEventListener("change", applyModeUi);
      applyModeUi();
      async function generatePlan() {
        const transcript = document.getElementById("transcript").value.trim();
        const cfg = MODE_UI[modeSelect.value] || MODE_UI.pastoral_confession;
        if (!transcript) {
          status(cfg.emptyMsg, false);
          return;
        }
        status("Generating plan...", true);
        const r = await fetch("/v1/plan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ transcript, mode: modeSelect.value })
        });
        const j = await r.json();
        if (!r.ok) {
          const err = j?.detail ? JSON.stringify(j.detail) : "Plan request failed.";
          status(err, false);
          return;
        }
        renderPlan(j);
        status("Plan generated.", true);
      }
      async function exportPdf() {
        const transcript = document.getElementById("transcript").value.trim();
        if (!transcript) return status("Add transcript first.", false);
        const r = await fetch("/v1/export/pdf", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ transcript, mode: modeSelect.value })
        });
        if (!r.ok) {
          let msg = "PDF export failed.";
          try { const j = await r.json(); if (j?.detail) msg = JSON.stringify(j.detail); } catch (_) {}
          status(msg, false);
          return;
        }
        const blob = await r.blob();
        triggerDownload(blob, modeSelect.value + "-plan.pdf");
        status("PDF exported.", true);
      }
      async function exportJsonl() {
        const transcript = document.getElementById("transcript").value.trim();
        if (!transcript) return status("Add transcript first.", false);
        const r = await fetch("/v1/export/jsonl", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ transcript, mode: modeSelect.value })
        });
        if (!r.ok) {
          let msg = "JSONL export failed.";
          try { const j = await r.json(); if (j?.detail) msg = JSON.stringify(j.detail); } catch (_) {}
          status(msg, false);
          return;
        }
        const blob = await r.blob();
        triggerDownload(blob, modeSelect.value + "-plan.jsonl");
        status("JSONL exported.", true);
      }
    </script>
  </body>
</html>"""


@app.post("/v1/plan")
def voice_to_plan(body: PlanIn):
    plan = planner.build_plan(body.transcript, body.mode)
    plan["mode"] = body.mode
    return plan


@app.post("/v1/export/jsonl")
def export_jsonl(body: PlanIn):
    plan = planner.build_plan(body.transcript, body.mode)
    payload = {
        "type": "structured_action_plan",
        "mode": body.mode,
        "transcript": body.transcript,
        "plan": plan,
    }
    line = json.dumps(payload, ensure_ascii=True) + "\n"
    headers = {"Content-Disposition": f"attachment; filename={body.mode}-plan.jsonl"}
    return Response(content=line, media_type="application/x-ndjson", headers=headers)


@app.post("/v1/export/pdf")
def export_pdf(body: PlanIn):
    plan = planner.build_plan(body.transcript, body.mode)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    content_w = pdf.w - pdf.l_margin - pdf.r_margin

    def write_line(text: str, height: int = 7) -> None:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(content_w, height, text)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, planner.mode_title(body.mode), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    write_line(f"Mode: {body.mode}")
    write_line(f"Problem Statement: {plan['problem_statement']}")
    pdf.ln(2)
    write_line(f"Risk Level: {plan['risk_level']}")
    write_line(f"Summary: {plan['summary']}")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Action Tally", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    tally = plan["tally"]
    write_line(
        f"Immediate: {tally['immediate']} | This Week: {tally['this_week']} | "
        f"Follow-Up: {tally['follow_up']} | Total: {tally['total_actions']}",
    )

    def add_section(title: str, items: list[str]) -> None:
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for idx, item in enumerate(items, start=1):
            write_line(f"{idx}. {item}")

    add_section("Immediate Actions", plan["plan"]["immediate"])
    add_section("This Week", plan["plan"]["this_week"])
    add_section("Follow-Ups", plan["plan"]["follow_up"])

    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 10)
    for note in plan["notes"]:
        write_line(f"- {note}", height=6)

    headers = {"Content-Disposition": f"attachment; filename={body.mode}-plan.pdf"}
    return Response(content=bytes(pdf.output()), media_type="application/pdf", headers=headers)

@app.post("/store", response_model=StoreOut)
def store(
    body: StoreIn,
    authorization: str | None = Header(default=None),
    x_content_key: str | None = Header(default=None),
):
    claims = _bearer(authorization)
    if claims["sub"] != body.care_id:
        raise HTTPException(403, "care_id mismatch")

    if body.ciphertext_b64:
        ct = base64.b64decode(body.ciphertext_b64)
    elif body.plaintext is not None:
        key = crypto.load_key(x_content_key)
        ct = crypto.encrypt(body.plaintext.encode(), key)
    else:
        raise HTTPException(400, "no payload")

    conn = storage.connect()
    rid = storage.store_ciphertext(conn, body.care_id, ct, int(time.time()))
    from hashlib import sha256
    return StoreOut(stored=True, record_id=rid, content_hash=sha256(ct).hexdigest())

@app.get("/audit")
def audit_log(authorization: str | None = Header(default=None)):
    _bearer(authorization)
    conn = storage.connect()
    return {"chain": storage.audit_chain(conn)}
