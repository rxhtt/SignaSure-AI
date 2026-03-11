from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from app.model import get_model

app = FastAPI(title="Signature Verification System")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Signature Verification | Enterprise</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Neue+Montreal:wght@400;500;700&family=Space+Grotesk:wght@400;600&display=swap" rel="stylesheet">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
        <style>
          :root {
            --bg: #0b0f14;
            --bg-2: #0f1720;
            --panel: rgba(255,255,255,0.06);
            --panel-2: rgba(255,255,255,0.12);
            --line: rgba(255,255,255,0.08);
            --text: #eef3f8;
            --muted: #9fb0c3;
            --accent: #5ee2ff;
            --accent-2: #9be15d;
            --glow: rgba(94,226,255,0.35);
          }
          * { box-sizing: border-box; }
          body {
            margin: 0;
            color: var(--text);
            background: radial-gradient(1200px 800px at 80% -10%, rgba(94,226,255,0.2), transparent 60%),
                        radial-gradient(900px 600px at 10% 10%, rgba(155,225,93,0.18), transparent 55%),
                        linear-gradient(180deg, #0a0f14 0%, #0b1118 100%);
            font-family: "Neue Montreal", "Space Grotesk", sans-serif;
          }
          .grid {
            position: fixed;
            inset: 0;
            background-image:
              linear-gradient(transparent 31px, rgba(255,255,255,0.03) 32px),
              linear-gradient(90deg, transparent 31px, rgba(255,255,255,0.03) 32px);
            background-size: 32px 32px;
            pointer-events: none;
            opacity: 0.25;
          }
          .wrap {
            max-width: 1200px;
            margin: 0 auto;
            padding: 48px 28px 80px;
          }
          .nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 24px;
            margin-bottom: 40px;
          }
          .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 600;
            letter-spacing: 0.2px;
          }
          .brand-dot {
            width: 12px;
            height: 12px;
            border-radius: 999px;
            background: var(--accent);
            box-shadow: 0 0 24px var(--glow);
          }
          .nav-actions {
            display: flex;
            gap: 12px;
          }
          .chip {
            padding: 8px 14px;
            border: 1px solid var(--line);
            border-radius: 999px;
            color: var(--muted);
            font-size: 13px;
            backdrop-filter: blur(8px);
          }
          .hero {
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 36px;
            align-items: stretch;
          }
          .hero h1 {
            font-size: 48px;
            line-height: 1.05;
            margin: 0 0 16px;
            letter-spacing: -0.5px;
          }
          .hero p {
            color: var(--muted);
            font-size: 17px;
            line-height: 1.6;
            margin: 0 0 20px;
          }
          .card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 22px;
            backdrop-filter: blur(10px);
          }
          .upload {
            display: grid;
            gap: 16px;
          }
          .drop {
            border: 1px dashed rgba(255,255,255,0.22);
            border-radius: 16px;
            padding: 20px;
            background: rgba(255,255,255,0.03);
            display: grid;
            gap: 12px;
          }
          .drop strong { font-size: 16px; }
          .drop small { color: var(--muted); }
          .actions {
            display: flex;
            gap: 12px;
          }
          button {
            appearance: none;
            border: none;
            background: linear-gradient(135deg, var(--accent), #6a9cff);
            color: #0b0f14;
            font-weight: 600;
            padding: 12px 16px;
            border-radius: 12px;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            box-shadow: 0 10px 30px rgba(94,226,255,0.25);
          }
          button.secondary {
            background: transparent;
            border: 1px solid var(--line);
            color: var(--text);
            box-shadow: none;
          }
          button:hover { transform: translateY(-1px); }
          .result {
            padding: 14px;
            border-radius: 12px;
            background: rgba(255,255,255,0.04);
            border: 1px solid var(--line);
            font-family: "Space Grotesk", monospace;
            font-size: 13px;
            color: #cfe2f5;
            white-space: pre-wrap;
            min-height: 64px;
          }
          .panel {
            display: grid;
            gap: 12px;
          }
          .metric {
            display: grid;
            grid-template-columns: 1fr auto;
            align-items: center;
            padding: 12px 14px;
            background: var(--panel-2);
            border-radius: 12px;
            border: 1px solid var(--line);
          }
          .metric b { font-size: 14px; }
          .metric span { color: var(--muted); font-size: 13px; }
          .how {
            margin-top: 40px;
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
          }
          .step h3 { margin: 0 0 6px; font-size: 18px; }
          .step p { margin: 0; color: var(--muted); font-size: 14px; line-height: 1.6; }
          .signals { margin: 0; padding-left: 18px; color: var(--muted); font-size: 14px; line-height: 1.6; }
          .signals li { margin: 4px 0; }
          .footer {
            margin-top: 60px;
            color: var(--muted);
            font-size: 12px;
            display: flex;
            justify-content: space-between;
          }
          .preview {
            width: 100%;
            border-radius: 14px;
            border: 1px solid var(--line);
            background: rgba(255,255,255,0.03);
            aspect-ratio: 4 / 3;
            object-fit: contain;
          }
          .badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 10px;
            border-radius: 999px;
            border: 1px solid rgba(94,226,255,0.3);
            color: var(--accent);
            font-size: 12px;
          }
          @media (max-width: 980px) {
            .hero { grid-template-columns: 1fr; }
            .how { grid-template-columns: 1fr; }
          }
        </style>
      </head>
      <body>
        <div class="grid"></div>
        <div class="wrap">
          <div class="nav">
            <div class="brand">
              <div class="brand-dot"></div>
              <div>Signature Verification System</div>
            </div>
            <div class="nav-actions">
              <div class="chip">Enterprise-ready</div>
              <div class="chip">CNN + Thresholding</div>
            </div>
          </div>

          <section class="hero">
            <div class="card panel">
              <div class="badge">Intelligent Verification</div>
              <h1>Automated Signature Verification for high-stakes workflows.</h1>
              <p>
                Upload a signature image and receive a confidence-scored authenticity decision.
                The system uses a CNN to learn stroke dynamics, texture, and shape cues, and a
                calibrated threshold to separate genuine and forged signatures.
              </p>
              <div class="upload">
                <div class="drop">
                  <strong>Upload a signature image</strong>
                  <small>PNG, JPG, JPEG. Recommended 300 DPI or higher.</small>
                  <input type="file" id="file" accept="image/*" />
                </div>
                <div class="actions">
                  <button onclick="submit()">Verify Signature</button>
                  <button class="secondary" onclick="resetForm()">Reset</button>
                </div>
                <div class="result" id="result">Awaiting upload...</div>
              </div>
            </div>

            <div class="card panel">
              <img id="preview" class="preview" alt="Signature preview" />
              <div class="metric">
                <b>Decision</b>
                <span id="decision">—</span>
              </div>
              <div class="metric">
                <b>Confidence</b>
                <span id="confidence">—</span>
              </div>
              <div class="metric">
                <b>Threshold</b>
                <span id="threshold">—</span>
              </div>
              <div class="metric">
                <b>Ink Ratio</b>
                <span id="ink_ratio">—</span>
              </div>
              <div class="metric">
                <b>Edge Strength</b>
                <span id="edge_strength">—</span>
              </div>
              <div class="metric">
                <b>Stroke Consistency</b>
                <span id="stroke_consistency">—</span>
              </div>
              <div class="metric">
                <b>Model</b>
                <span>CNN (128x128 grayscale)</span>
              </div>
            </div>
          </section>

          <section class="how">
            <div class="card step">
              <h3>1. Capture</h3>
              <p>Signatures are normalized into clean, uniform grayscale tiles for consistent analysis.</p>
            </div>
            <div class="card step">
              <h3>2. Learn</h3>
              <p>The CNN learns hierarchical features such as stroke edges, pressure patterns, and flow.</p>
            </div>
            <div class="card step">
              <h3>3. Decide</h3>
              <p>A calibrated threshold converts probabilities into a reliable genuine/forged verdict.</p>
            </div>
          </section>

          <section class="how">
            <div class="card step">
              <h3>Why This Result?</h3>
              <p id="detail">Model rationale will appear here after verification.</p>
              <p style="margin-top:10px;color:var(--muted);font-size:12px;">
                This is a machine learning assessment, not a legal or forensic determination.
              </p>
            </div>
            <div class="card step">
              <h3>Signals Observed</h3>
              <ul id="signals" class="signals"></ul>
            </div>
            <div class="card step">
              <h3>Enterprise Add-ons</h3>
              <p>
                Usage-based API access, SLA-backed support, bulk batch verification, audit trails,
                and per-client threshold tuning for compliance-grade deployments.
              </p>
            </div>
          </section>

          <section class="how">
            <div class="card step">
              <h3>Project Credits</h3>
              <p>
                Name: iliyasmahamd H jalaladar<br>
                UUCMS No: U02AJ23S0415<br>
                Email: jalaldarilyas@gmail.com
              </p>
            </div>
            <div class="card step">
              <h3>Guide</h3>
              <p>smt kubra shirur</p>
            </div>
            <div class="card step">
              <h3>Institution</h3>
              <p>
                Final Year Project (BCA)<br>
                Government First College, Dharwad - 580001
              </p>
            </div>
          </section>

          <div class="footer">
            <div>Security-first architecture. Human review optional.</div>
            <div>API: /predict · /health</div>
          </div>
        </div>

        <script>
          const fileInput = document.getElementById('file');
          const preview = document.getElementById('preview');
          const result = document.getElementById('result');
          const decision = document.getElementById('decision');
          const confidence = document.getElementById('confidence');
          const threshold = document.getElementById('threshold');
          const inkRatio = document.getElementById('ink_ratio');
          const edgeStrength = document.getElementById('edge_strength');
          const strokeConsistency = document.getElementById('stroke_consistency');
          const detail = document.getElementById('detail');
          const signals = document.getElementById('signals');

          fileInput.addEventListener('change', () => {
            const file = fileInput.files[0];
            if (!file) return;
            const url = URL.createObjectURL(file);
            preview.src = url;
          });

          function renderResult(data) {
            result.textContent = JSON.stringify(data, null, 2);
            decision.textContent = data.label;
            confidence.textContent = (data.score * 100).toFixed(2) + '%';
            threshold.textContent = data.threshold;
            if (data.signals) {
              inkRatio.textContent = data.signals.ink_ratio;
              edgeStrength.textContent = data.signals.edge_strength;
              strokeConsistency.textContent = data.signals.stroke_consistency;
              signals.innerHTML = '';
              const items = [
                'Ink ratio: ' + data.signals.ink_ratio,
                'Edge strength: ' + data.signals.edge_strength,
                'Stroke consistency: ' + data.signals.stroke_consistency,
                'BBox coverage: ' + data.signals.bbox_coverage,
                'Aspect ratio: ' + data.signals.aspect_ratio
              ];
              items.forEach(text => {
                const li = document.createElement('li');
                li.textContent = text;
                signals.appendChild(li);
              });
            }
            if (data.detail) {
              detail.textContent = data.detail + ' ' + (data.rationale || []).join(' ');
            }
            gsap.fromTo('.metric', { y: 10, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4, stagger: 0.08 });
          }

          async function submit() {
            const file = fileInput.files[0];
            if (!file) return;
            result.textContent = 'Verifying...';
            const form = new FormData();
            form.append('file', file);
            const res = await fetch('/predict', { method: 'POST', body: form });
            const data = await res.json();
            renderResult(data);
          }

          function resetForm() {
            fileInput.value = '';
            preview.src = '';
            result.textContent = 'Awaiting upload...';
            decision.textContent = '—';
            confidence.textContent = '—';
            threshold.textContent = '—';
            inkRatio.textContent = '—';
            edgeStrength.textContent = '—';
            strokeConsistency.textContent = '—';
            detail.textContent = 'Model rationale will appear here after verification.';
            signals.innerHTML = '';
          }

          gsap.from('.card', { y: 20, opacity: 0, duration: 0.8, stagger: 0.12, ease: 'power2.out' });
          gsap.from('.brand', { x: -10, opacity: 0, duration: 0.6, delay: 0.2 });
        </script>
      </body>
    </html>
    """


@app.post("/predict")
async def predict(file: UploadFile = File(...)) -> JSONResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    image_bytes = await file.read()

    try:
        model = get_model()
        label, score, signals, detail, rationale = model.predict(image_bytes)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return JSONResponse(
        {
            "label": label,
            "score": score,
            "threshold": model.threshold,
            "signals": signals,
            "detail": detail,
            "rationale": rationale,
        }
    )
