import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import json
from datetime import datetime
from io import StringIO

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Smart ICU CDSS (Gemini)",
    page_icon="🏥",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS.
# ─────────────────────────────────────────────
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0a0f1a !important;
    color: #c8d8ea;
    font-family: 'Segoe UI', sans-serif;
}
[data-testid="stSidebar"] { background-color: #0d1420 !important; border-right: 1px solid #1e2d45; }
[data-testid="stSidebar"] * { color: #c8d8ea !important; }
.icu-header {
    background: #0d1420; border: 1px solid #1e2d45; border-radius: 10px;
    padding: 12px 20px; display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 16px;
}
.logo-badge {
    background: #1a3a5c; color: #60a5d4; font-size: 11px; font-weight: 600;
    padding: 4px 12px; border-radius: 4px; letter-spacing: 1px;
    display: inline-block; margin-right: 12px;
}
.header-title { color: #e2eaf4; font-size: 16px; font-weight: 600; display: inline-block; }
.live-indicator {
    background: #0f2a1a; color: #34d399; border: 1px solid #14532d;
    padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;
}
.vital-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px; }
.vital-card { background: #0d1a2e; border: 1px solid #1a2d45; border-radius: 10px; padding: 12px 16px; }
.vital-card.danger { background: #1a0d0d; border-color: #7f1d1d; }
.vital-card.warning { background: #1c1400; border-color: #78450a; }
.vital-label { font-size: 10px; color: #4a6480; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px; }
.vital-value { font-size: 26px; font-weight: 700; color: #e2eaf4; line-height: 1; }
.vital-value.danger { color: #f87171; }
.vital-value.warning { color: #fbbf24; }
.vital-unit { font-size: 11px; color: #4a6480; margin-top: 2px; }
.vital-trend { font-size: 11px; margin-top: 6px; }
.trend-up { color: #f87171; }
.trend-dn { color: #34d399; }
.trend-eq { color: #6b8099; }
.ai-panel {
    background: #0d1420; border: 1px solid #1e2d45; border-radius: 10px;
    padding: 16px; margin-top: 0;
}
.ai-panel-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.ai-badge {
    background: #0f5132; color: #fff; border: 1px solid #0f5132;
    border-radius: 6px; padding: 3px 10px; font-size: 11px; font-weight: 600;
}
.ai-title { color: #e2eaf4; font-size: 14px; font-weight: 600; }
.risk-bar-wrap { margin: 10px 0; }
.risk-bar-label { display: flex; justify-content: space-between; margin-bottom: 4px; }
.risk-pct-big { font-size: 22px; font-weight: 700; }
.risk-pct-crit { color: #f87171; }
.risk-pct-warn { color: #fbbf24; }
.risk-pct-safe { color: #34d399; }
.risk-bar-bg { background: #1a2d45; border-radius: 4px; height: 8px; overflow: hidden; }
.risk-bar-fill { height: 8px; border-radius: 4px; }
.risk-fill-crit { background: linear-gradient(90deg, #22c55e, #fbbf24, #f87171); }
.risk-fill-warn { background: linear-gradient(90deg, #22c55e, #fbbf24); }
.risk-fill-safe { background: #22c55e; }
.ai-bubble {
    background: #0a1624; border-left: 3px solid #2563eb; border-radius: 0 8px 8px 0;
    padding: 10px 14px; margin-bottom: 8px; font-size: 13px; color: #9ab8d4; line-height: 1.7;
}
.ai-bubble.danger-bubble { border-left-color: #f87171; }
.ai-bubble.warn-bubble   { border-left-color: #fbbf24; }
.ai-bubble.safe-bubble   { border-left-color: #34d399; }
.ai-bubble strong { color: #f87171; }
.ai-bubble em     { color: #34d399; font-style: normal; }
.alert-crit {
    background: #2a0a0a; border: 1px solid #f87171; border-radius: 8px;
    padding: 12px 16px; color: #fca5a5; font-size: 13px; margin-bottom: 12px;
    animation: pulse-red 1.5s infinite;
}
@keyframes pulse-red { 0%,100%{border-color:#f87171;} 50%{border-color:#fecaca;} }
.alert-safe {
    background: #0a1f12; border: 1px solid #34d399; border-radius: 8px;
    padding: 12px 16px; color: #6ee7b7; font-size: 13px; margin-bottom: 12px;
}
.alert-warn {
    background: #1c1400; border: 1px solid #fbbf24; border-radius: 8px;
    padding: 12px 16px; color: #fde68a; font-size: 13px; margin-bottom: 12px;
}
hr.icu-divider { border-color: #1e2d45; margin: 16px 0; }
.risk-pill { display: inline-block; font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 3px; margin-top: 5px; }
.rp-crit { background: #3d1515; color: #f87171; }
.rp-warn { background: #2d2010; color: #fbbf24; }
.rp-safe { background: #0f2a1a; color: #34d399; }
[data-testid="stMetric"] { background: #0d1a2e; border: 1px solid #1a2d45; border-radius: 10px; padding: 10px 14px; }
[data-testid="stMetricLabel"] p { color: #4a6480 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.7px; }
[data-testid="stMetricValue"] { color: #e2eaf4 !important; }
div[data-testid="stSelectbox"] > div > div { background: #121d2e !important; border-color: #1e2d45 !important; color: #c8d8ea !important; }
button[kind="primary"] { background: #1a3a6e !important; border-color: #2563eb !important; color: #93c5fd !important; }
[data-testid="stTextInput"] input { background: #121d2e !important; border-color: #1e2d45 !important; color: #c8d8ea !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Config  ← แก้ URL ให้ถูกต้อง (ไม่มี markdown bracket)
# ─────────────────────────────────────────────
BASE_RAW_URL = (
    "https://raw.githubusercontent.com/anonymaew/"
    "bdi-hackathon-2026-sampled-dataset/"
    "e511fb1b73906b2be5292e4c2e66508c6018b157/ventilator/smart_icu_data/"
)

# ← Hardcode list ไว้เลย ไม่พึ่ง GitHub API (rate-limit 403)
PATIENT_FILES = [
    "2a7b9f1857ab1296725ab6fb1c0b5895.json",
    "5ea4aaf18779681f4b0fbf093c233521.json",
    "bd49632138fb4b75d505156379f25fb9.json",
]

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
@st.cache_data(ttl=600)
def load_patient_json(fname: str) -> list[dict]:
    """คืนค่า list ของ visit records (JSON จริงเป็น array)"""
    url = BASE_RAW_URL + fname
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else [data]

@st.cache_data(ttl=600)
def load_waveform_csv(csv_filename: str) -> pd.DataFrame:
    url = BASE_RAW_URL + csv_filename
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    # BOM-safe read
    df = pd.read_csv(StringIO(r.content.decode("utf-8-sig")))
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def find_col(cols: list[str], *keywords) -> str | None:
    for k in keywords:
        found = next((c for c in cols if k in c), None)
        if found:
            return found
    return cols[0] if cols else None

def classify_risk(p_val: float):
    """(label, pct, css_cls)"""
    if p_val > 23:
        return "วิกฤต",   min(99, int(70 + (p_val - 23) * 5)), "crit"
    elif p_val > 20:
        return "เฝ้าระวัง", int(40 + (p_val - 20) * 10),         "warn"
    else:
        return "ปลอดภัย",  max(5, int(20 - max(p_val, 0))),       "safe"

def call_gemini(p_val, f_val, v_val, diagnosis, age, t_step, api_key, history_p) -> dict:
    """เรียก Gemini API พร้อม fallback"""
    p_trend = ""
    if len(history_p) >= 3:
        delta = history_p[-1] - history_p[-3]
        p_trend = f"เพิ่มขึ้น {delta:.1f}" if delta > 0 else f"ลดลง {abs(delta):.1f}"

    prompt = f"""คุณคือระบบ AI สนับสนุนการตัดสินใจทางคลินิก (CDSS) ใน ICU
ข้อมูลผู้ป่วย:
- วินิจฉัย: {diagnosis}
- อายุ: {age} ปี
- Airway Pressure (Paw): {p_val:.1f} cmH₂O (trend: {p_trend or 'ไม่มีข้อมูล'})
- Respiratory Flow: {f_val:.1f} L/min
- Tidal Volume: {v_val:.1f} mL
- รอบที่: {t_step}/100
- ประวัติ Paw 5 ค่าล่าสุด: {[round(x,1) for x in history_p[-5:]]}

เกณฑ์: Paw ปกติ 8–20, เฝ้าระวัง 20–23, วิกฤต >23 หรือ <8 cmH₂O

ตอบเป็น JSON เท่านั้น ห้ามมี markdown fence:
{{"risk_pct":<0-100>,"status":"<วิกฤต|เฝ้าระวัง|ปลอดภัย>","summary":"<1 ประโยค>","reason":"<1-2 ประโยค>","recommendation":"<1-2 ประโยค>"}}"""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="ตอบเป็น JSON เท่านั้น ห้ามมีข้อความอื่น",
                response_mime_type="application/json",
                response_schema=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "risk_pct":       types.Schema(type=types.Type.INTEGER),
                        "status":         types.Schema(type=types.Type.STRING),
                        "summary":        types.Schema(type=types.Type.STRING),
                        "reason":         types.Schema(type=types.Type.STRING),
                        "recommendation": types.Schema(type=types.Type.STRING),
                    },
                    required=["risk_pct","status","summary","reason","recommendation"],
                ),
            ),
        )
        text = resp.text.strip().lstrip("```json").rstrip("```").strip()
        return json.loads(text)
    except Exception as e:
        risk, pct, _ = classify_risk(p_val)
        return {
            "risk_pct": pct, "status": risk,
            "summary": f"Gemini API error: {str(e)[:80]}",
            "reason": f"Paw = {p_val:.1f} cmH₂O",
            "recommendation": "ตรวจสอบ API Key และการเชื่อมต่อ",
        }

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 SMART ICU CDSS")
    st.markdown("### ⚙️ ตั้งค่าระบบ")

    # ── ใส่ API Key ตรงนี้ ──
    GEMINI_API_KEY = "-----"
    api_key = GEMINI_API_KEY
    st.success("✅ Gemini API Key พร้อมใช้งาน")

    st.markdown("---")
    st.markdown("### 👤 เลือกผู้ป่วย")

    # โหลด JSON ทั้ง 3 ผู้ป่วยแบบ safe
    patient_options = []
    for fname in PATIENT_FILES:
        try:
            visits = load_patient_json(fname)
            # เอา visit แรกที่มี captures
            first = next((v for v in visits if v.get("captures")), visits[0])
            label = f"{first.get('patient','?')} — {first.get('diagnosis','ไม่ระบุ')[:30]}"
            patient_options.append({"fname": fname, "visits": visits, "label": label})
        except Exception as e:
            patient_options.append({"fname": fname, "visits": [], "label": f"⚠️ โหลดไม่ได้ ({fname[:8]})"})

    selected_idx = st.selectbox(
        "รายชื่อผู้ป่วย:",
        range(len(patient_options)),
        format_func=lambda i: patient_options[i]["label"],
    )
    sel = patient_options[selected_idx]
    visits = sel["visits"]

    # เลือก visit (วันที่)
    visit_labels = [
        f"วันที่ {v.get('bed','?').split(',')[-1].strip()} เวลา {v['captures'][0]['time'] if v.get('captures') else 'ไม่มีข้อมูล'}"
        for v in visits
    ]
    # กรอง visit ที่มี captures เท่านั้น
    valid_visits = [(i, v) for i, v in enumerate(visits) if v.get("captures")]
    if not valid_visits:
        st.error("ผู้ป่วยรายนี้ไม่มีข้อมูล waveform")
        st.stop()

    visit_choice = st.selectbox(
        "เลือก Session:",
        range(len(valid_visits)),
        format_func=lambda i: f"วันที่ {valid_visits[i][1].get('bed','?').split(',')[-1].strip()} | {valid_visits[i][1]['captures'][0]['time']}",
    )
    _, chosen_visit = valid_visits[visit_choice]

    st.markdown("---")
    st.markdown("**สัญลักษณ์ความเสี่ยง**")
    st.markdown("""
- 🔴 **วิกฤต** — Paw > 23 cmH₂O  
- 🟡 **เฝ้าระวัง** — Paw 20–23 cmH₂O  
- 🟢 **ปลอดภัย** — Paw < 20 cmH₂O
""")

    stream_btn = st.button("▶️ เริ่ม Stream สัญญาณชีพ", type="primary", use_container_width=True)

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
diag  = chosen_visit.get("diagnosis", "ไม่ระบุ")
demo  = chosen_visit.get("demographic", "ไม่ระบุ")
pat   = chosen_visit.get("patient", "ไม่ระบุ")
# parse อายุจาก "ช 47 ปี" หรือ "ญ 55 ปี"
try:
    age = int("".join(filter(str.isdigit, pat.split("ปี")[0])))
except Exception:
    age = 0

st.markdown(f"""
<div class="icu-header">
  <div>
    <span class="logo-badge">SMART ICU CDSS</span>
    <span class="header-title">หอวิกฤต ICU · ผู้ป่วย {pat} · {diag[:50]}</span>
  </div>
  <span class="live-indicator">● LIVE</span>
</div>""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("👤 ผู้ป่วย", pat)
c2.metric("📋 ข้อมูลกายภาพ", demo[:35] if demo else "ไม่ระบุ")
c3.metric("🩺 วินิจฉัย", diag[:45] + "..." if len(diag) > 45 else diag)

st.markdown('<hr class="icu-divider">', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# โหลด Waveform CSV
# ─────────────────────────────────────────────
csv_filename = chosen_visit["captures"][0]["raw_data"]
try:
    df_wave = load_waveform_csv(csv_filename)
    cols    = df_wave.columns.tolist()
except Exception as e:
    st.error(f"❌ โหลดไฟล์ waveform ไม่ได้: {e}")
    st.stop()

# CSV จริง: "flow (l/min)", "pressure (cmh2o)", "volume (ml)"
p_col = find_col(cols, "pressure", "paw", "p_")
f_col = find_col(cols, "flow", "f_")
v_col = find_col(cols, "volume", "v_")
features = [c for c in [p_col, f_col, v_col] if c]

if not features:
    st.error(f"ไม่พบ columns ที่ต้องการ — columns ที่มี: {cols}")
    st.stop()

# ─────────────────────────────────────────────
# Layout
# ─────────────────────────────────────────────
left_col, right_col = st.columns([2, 1], gap="medium")
with left_col:
    vitals_ph = st.empty()
    chart_ph  = st.empty()
with right_col:
    alert_ph = st.empty()
    ai_ph    = st.empty()

# ─────────────────────────────────────────────
# Render functions
# ─────────────────────────────────────────────
def render_vitals(p_val, f_val, v_val, p_prev=None):
    p_class   = "danger" if p_val > 23 else ("warning" if p_val > 20 else "")
    p_v_class = p_class
    p_trend   = ""
    if p_prev is not None:
        d = p_val - p_prev
        if d > 0.2:
            p_trend = f'<div class="vital-trend trend-up">▲ +{d:.1f} cmH₂O</div>'
        elif d < -0.2:
            p_trend = f'<div class="vital-trend trend-dn">▼ {d:.1f} cmH₂O</div>'
        else:
            p_trend = '<div class="vital-trend trend-eq">— คงที่</div>'

    vitals_ph.markdown(f"""
<div class="vital-grid">
  <div class="vital-card {p_class}">
    <div class="vital-label">Airway Pressure (Paw)</div>
    <div class="vital-value {p_v_class}">{p_val:.1f}</div>
    <div class="vital-unit">cmH₂O</div>
    {p_trend}
  </div>
  <div class="vital-card">
    <div class="vital-label">Respiratory Flow</div>
    <div class="vital-value">{f_val:.1f}</div>
    <div class="vital-unit">L/min</div>
  </div>
  <div class="vital-card">
    <div class="vital-label">Tidal Volume</div>
    <div class="vital-value">{v_val:.1f}</div>
    <div class="vital-unit">mL</div>
  </div>
</div>""", unsafe_allow_html=True)

def render_ai_panel(result: dict):
    status  = result.get("status", "ไม่ทราบ")
    pct     = int(result.get("risk_pct", 0))
    summary = result.get("summary", "")
    reason  = result.get("reason", "")
    rec     = result.get("recommendation", "")

    if status == "วิกฤต":
        css_bar, css_pct, bubble_cls, icon = "risk-fill-crit","risk-pct-crit","danger-bubble","🚨"
    elif status == "เฝ้าระวัง":
        css_bar, css_pct, bubble_cls, icon = "risk-fill-warn","risk-pct-warn","warn-bubble","⚠️"
    else:
        css_bar, css_pct, bubble_cls, icon = "risk-fill-safe","risk-pct-safe","safe-bubble","✅"

    bar_w = max(4, min(100, pct))
    ai_ph.markdown(f"""
<div class="ai-panel">
  <div class="ai-panel-header">
    <span class="ai-badge">Gemini AI</span>
    <span class="ai-title">การวิเคราะห์ทางคลินิก</span>
  </div>
  <div class="risk-bar-wrap">
    <div class="risk-bar-label">
      <span style="font-size:13px;color:#6b8099;">ความเสี่ยงภาวะวิกฤต</span>
      <span class="risk-pct-big {css_pct}">{pct}%</span>
    </div>
    <div class="risk-bar-bg">
      <div class="risk-bar-fill {css_bar}" style="width:{bar_w}%"></div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:3px;">
      <span style="font-size:9px;color:#4a6480;">ต่ำ</span>
      <span style="font-size:9px;color:#4a6480;">สูง</span>
    </div>
  </div>
  <div style="font-size:13px;font-weight:600;color:#e2eaf4;margin:10px 0 6px;">
    {icon} สถานะ: {status}
  </div>
  <div class="ai-bubble {bubble_cls}">
    <strong>สรุป:</strong> {summary}
  </div>
  <div class="ai-bubble">
    <strong style="color:#60a5fa;">เหตุผล:</strong> {reason}
  </div>
  <div class="ai-bubble safe-bubble">
    <em>แนะนำ: {rec}</em>
  </div>
  <div style="font-size:10px;color:#2d4a66;margin-top:8px;text-align:right;">
    วิเคราะห์โดย Gemini 2.5 Flash · {datetime.now().strftime('%H:%M:%S')}
  </div>
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Initial display
# ─────────────────────────────────────────────
first = df_wave.iloc[0]
p0 = float(first[p_col]) if p_col else 15.0
f0 = float(first[f_col]) if f_col else 30.0
v0 = float(first[v_col]) if v_col and v_col in df_wave.columns else 450.0

render_vitals(p0, f0, v0)
chart_ph.line_chart(df_wave[features].head(50))
alert_ph.info("💡 กด **▶️ เริ่ม Stream** เพื่อดูการวิเคราะห์เรียลไทม์")
ai_ph.markdown(f"""
<div class="ai-panel">
  <div class="ai-panel-header">
    <span class="ai-badge">Gemini AI</span>
    <span class="ai-title">พร้อมวิเคราะห์</span>
  </div>
  <div class="ai-bubble">
    กดปุ่ม <strong>▶️ เริ่ม Stream</strong> ด้านซ้าย<br>
    เพื่อให้ Gemini วิเคราะห์สัญญาณชีพแบบเรียลไทม์
  </div>
  {'<div class="ai-bubble danger-bubble">⚠️ ตรวจพบ Paw สูงในค่าเริ่มต้น — แนะนำให้ตรวจสอบ</div>' if p0 > 20 else ""}
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Streaming loop
# ─────────────────────────────────────────────
if stream_btn:
    if not api_key:
        st.error("⚠️ กรุณาใส่ Gemini API Key ก่อน")
        st.stop()

    stream_df       = pd.DataFrame(columns=features)
    history_p: list[float] = []
    last_ai: dict   = {}
    last_ai_time    = 0.0
    AI_EVERY        = 15   # เรียก Gemini ทุก 15 รอบ
    AI_MIN_INTERVAL = 8.0  # ห่างกันอย่างน้อย 8 วินาที
    ai_call_count   = 0

    for t in range(100):
        idx   = (t * 2) % len(df_wave)
        chunk = df_wave.iloc[idx : idx + 2].copy()

        chunk[p_col] = chunk[p_col] + np.sin(t * 0.4) * 4
        chunk[f_col] = chunk[f_col] + np.cos(t * 0.4) * 15

        if 40 <= t <= 55:
            chunk[p_col] = chunk[p_col] + 10.0

        p_val = float(chunk[p_col].values[-1])
        f_val = float(chunk[f_col].values[-1])
        v_val = float(chunk[v_col].values[-1]) if v_col and v_col in chunk.columns else 450.0

        history_p.append(p_val)
        p_prev = history_p[-2] if len(history_p) >= 2 else None

        render_vitals(p_val, f_val, v_val, p_prev)

        stream_df = pd.concat([stream_df, chunk[features]], ignore_index=True)
        chart_ph.line_chart(stream_df.tail(60))

        # Alert banner
        _, _, risk_cls = classify_risk(p_val)
        if risk_cls == "crit":
            alert_ph.markdown(f"""<div class="alert-crit">
🚨 <strong>[CDSS แจ้งเตือนด่วน]</strong> Airway Pressure สูง <strong>{p_val:.1f} cmH₂O</strong>
เกินพิกัด 23 cmH₂O — เสี่ยง Barotrauma / Patient-Ventilator Dyssynchrony โปรดเข้าช่วยเหลือทันที!</div>""",
                unsafe_allow_html=True)
        elif risk_cls == "warn":
            alert_ph.markdown(f"""<div class="alert-warn">
⚠️ <strong>[เฝ้าระวัง]</strong> Paw {p_val:.1f} cmH₂O — อยู่ในโซนเฝ้าระวัง (20–23 cmH₂O)</div>""",
                unsafe_allow_html=True)
        else:
            alert_ph.markdown(f"""<div class="alert-safe">
✅ <strong>[สถานะปกติ]</strong> Paw {p_val:.1f} cmH₂O — สัญญาณชีพอยู่ในเกณฑ์ปกติ</div>""",
                unsafe_allow_html=True)

        # เรียก Gemini — throttle ให้ห่างกันอย่างน้อย AI_MIN_INTERVAL วินาที
        now = time.time()
        is_critical_spike = (p_val > 23 and (last_ai == {} or last_ai.get("status") != "วิกฤต"))
        should_call = (t % AI_EVERY == 0 or is_critical_spike) and (now - last_ai_time >= AI_MIN_INTERVAL)

        if should_call:
            last_ai = call_gemini(p_val, f_val, v_val, diag, age, t, api_key, history_p)
            last_ai_time = time.time()
            ai_call_count += 1

        if last_ai:
            render_ai_panel(last_ai)

        time.sleep(0.3)

    st.success(f"🏁 Stream เสร็จสิ้น — เรียก Gemini ทั้งหมด {ai_call_count} ครั้ง")
    st.balloons()
