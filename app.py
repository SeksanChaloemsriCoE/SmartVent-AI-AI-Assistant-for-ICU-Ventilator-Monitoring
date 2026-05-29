import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(layout="wide")
st.title("🏥 Smart ICU AI Ventilator CDSS Monitor")
st.write("ระบบสนับสนุนการตัดสินใจทางคลินิก วิเคราะห์อัตราการหายใจและความเสี่ยงภาวะวิกฤตรายบุคคล")

# 1. ที่อยู่คลังข้อมูลหลักบน GitHub
BASE_RAW_URL = "https://raw.githubusercontent.com/anonymaew/bdi-hackathon-2026-sampled-dataset/e511fb1b73906b2be5292e4c2e66508c6018b157/ventilator/smart_icu_data/"
API_URL = "https://api.github.com/repos/anonymaew/bdi-hackathon-2026-sampled-dataset/contents/ventilator/smart_icu_data?ref=main"

PATIENT_NAME_MAP = {
    "2a7b9f1857ab1296725ab6fb1c0b5895.json": "🛏️ เตียง 01: นายสมชาย ดีใจ (HN-001)",
    "5ea4aaf18779681f4b0fbf093c233521.json": "🛏️ เตียง 02: นางสมศรี แก้วดี (HN-002)",
    "bd49632138fb4b75d505156379f25fb9.json": "🛏️ เตียง 03: นายอนันต์ รักชาติ (HN-003)"
}

@st.cache_data
def get_all_files():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

all_files_json = get_all_files()

if all_files_json:
    json_files = [f['name'] for f in all_files_json if f['name'].endswith('.json')]
    st.sidebar.header("👤 เลือกผู้ป่วยในหอวิกฤต")
    display_names = [PATIENT_NAME_MAP.get(fname, f"👤 ผู้ป่วยรหัส {fname[:8]}...") for fname in json_files]
    selected_display_name = st.sidebar.selectbox("รายชื่อผู้ป่วยครองเตียง:", display_names)
    
    reverse_map = {v: k for k, v in PATIENT_NAME_MAP.items()}
    selected_json = reverse_map.get(selected_display_name, json_files[0])
    
    json_url = BASE_RAW_URL + selected_json
    patient_meta = requests.get(json_url).json()
    
    if isinstance(patient_meta, list):
        patient_meta = patient_meta[0]
        
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("📋 ข้อมูลปัจจุบัน", selected_display_name.replace("🛏️ ", ""))
    with c2:
        st.metric("📊 ข้อมูลกายภาพ (BMI)", patient_meta.get('demographic', 'ไม่ระบุ'))
    with c3:
        st.warning(f"🩺 **ผลวินิจฉัยหลัก:** {patient_meta.get('diagnosis', 'ไม่ระบุ')}")
        
    try:
        csv_file_name = patient_meta['captures'][0]['raw_data']
        csv_url = BASE_RAW_URL + csv_file_name
    except:
        csv_file_name = None
        st.error("ไม่พบลิงก์ไฟล์ Waveform ในโปรไฟล์ผู้ป่วยรายนี้")

    if csv_file_name:
        st.sidebar.success(f"🔗 สแกนพบไฟล์คลื่นสัญญาณเรียบร้อย")
        start_btn = st.sidebar.button("▶️ เริ่มสตรีมสัญญาณชีพเรียลไทม์")
        
        st.markdown("---")
        
        with st.spinner("กำลังดึงข้อมูลสัญญาณชีพจากระบบคลังกลาง..."):
            try:
                df_wave = pd.read_csv(csv_url)
                df_wave.columns = [str(c).strip().lower() for c in df_wave.columns]
                available_cols = df_wave.columns.tolist()
            except Exception as e:
                st.error(f"ไม่สามารถอ่านไฟล์ CSV ได้: {e}")
                df_wave = None

        if df_wave is not None:
            p_col = next((c for c in available_cols if 'pressure' in c or 'p_' in c or 'paw' in c), None)
            f_col = next((c for c in available_cols if 'flow' in c or 'f_' in c), None)
            v_col = next((c for c in available_cols if 'volume' in c or 'v_' in c), None)
            
            if not p_col and len(available_cols) > 0: p_col = available_cols[0]
            if not f_col and len(available_cols) > 1: f_col = available_cols[1]
            if not v_col and len(available_cols) > 2: v_col = available_cols[2]

            features = [c for c in [p_col, f_col, v_col] if c is not None and c in available_cols]
            
            metric_columns = st.columns(len(features) + 1)
            metrics_placeholders = {}
            for i, feat in enumerate(features):
                metrics_placeholders[feat] = metric_columns[i].empty()
            metric_ai = metric_columns[-1].empty()
            
            chart_spot = st.empty()
            alert_spot = st.empty()
            
            # เตรียม AI โมเดล
            ai_model = None
            if len(features) > 0:
                df_wave['risk_label'] = np.where((df_wave[p_col] > 20) | (df_wave[p_col] < 8), 1, 0)
                X = df_wave[features].fillna(0)
                y = df_wave['risk_label']
                
                # เช็คว่ามีข้อมูลทั้งฝั่งวิกฤต(1) และปลอดภัย(0) ครบหรือไม่
                if len(np.unique(y)) > 1:
                    ai_model = RandomForestClassifier(n_estimators=5, random_state=42)
                    ai_model.fit(X, y)
            
            if start_btn:
                stream_df = pd.DataFrame(columns=features)
                
                for t in range(100):
                    idx = (t * 2) % len(df_wave)
                    chunk = df_wave.iloc[idx:idx+2].copy()
                    
                    # ปรับสัญญาณจำลองคลื่นปอดให้สมจริงเคลื่อนไหวได้
                    simulated_noise_p = np.sin(t * 0.4) * 4  
                    simulated_noise_f = np.cos(t * 0.4) * 15 
                    
                    chunk[p_col] = chunk[p_col] + simulated_noise_p
                    chunk[f_col] = chunk[f_col] + simulated_noise_f
                    
                    # ช่วงทดสอบสถานะวิกฤต (รอบที่ 40-55) เพื่อพรีเซนต์การดีดไซเรนเตือนภัย
                    if 40 <= t <= 55:
                        chunk[p_col] = chunk[p_col] + 12.0 
                    
                    p_val = chunk[p_col].values[-1]
                    f_val = chunk[f_col].values[-1]
                    v_val = chunk[v_col].values[-1] if v_col in chunk.columns else 333.3
                    
                    metrics_placeholders[p_col].metric(label="Airway Pressure (Paw)", value=f"{p_val:.1f} cmH2O")
                    metrics_placeholders[f_col].metric(label="Respiratory Flow", value=f"{f_val:.1f} L/min")
                    if v_col in metrics_placeholders:
                        metrics_placeholders[v_col].metric(label="Tidal Volume", value=f"{v_val:.1f} mL")
                    
                    # 🌟 คำนวณความเสี่ยงอย่างปลอดภัย ดักจับกรณีมีคลาสเดียวเพื่อไม่ให้ IndexError บรรทัด 138 เกิดขึ้นอีก
                    if ai_model is not None:
                        ai_input = chunk[features].fillna(0)
                        pred = ai_model.predict(ai_input)[-1]
                        prob = ai_model.predict_proba(ai_input)[-1][1] * 100
                    else:
                        # กรณีที่โมเดลไม่มีคลาสเสี่ยงให้เรียนรู้ล่วงหน้า จะใช้ Threshold คำนวณแบบตรงไปตรงมา
                        pred = 1 if p_val > 23.0 else 0
                        prob = 90.0 if p_val > 23.0 else 10.0
                    
                    if p_val > 23.0 or pred == 1:
                        metric_ai.metric("AI Risk Status", "🚨 วิกฤต", f"ความเสี่ยง {max(prob, 85):.0f}%", delta_color="inverse")
                        alert_spot.error(f"⚠️ **[CDSS แจ้งเตือนด่วน]:** ตรวจพบแรงดันในทางเดินหายใจสูงเกินพิกัด ({p_val:.1f} cmH2O) ผู้ป่วยอาจเกิดภาวะต้านเครื่องช่วยหายใจหรือปอดบาดเจ็บ (Barotrauma) โปรดเข้าช่วยเหลือทันที!")
                    else:
                        metric_ai.metric("AI Risk Status", "✅ ปลอดภัย", f"เสี่ยง {min(prob, 15):.0f}%")
                        alert_spot.success("🏥 **[สถานะทางการแพทย์]:** คลื่นสัญญาณชีพของผู้ป่วยสัมพันธ์กับเครื่องช่วยหายใจปกติดี")
                    
                    stream_df = pd.concat([stream_df, chunk[features]])
                    chart_spot.line_chart(stream_df.tail(40))
                    
                    time.sleep(0.15) 
                    
                st.success("🏁 จำลองการสตรีมสัญญาณชีพเสร็จสิ้นอย่างสมบูรณ์")
            else:
                st.info("💡 พร้อมใช้งานแล้ว! เลือกชื่อผู้ป่วยด้านซ้าย แล้วกดปุ่ม **'เริ่มสตรีมสัญญาณชีพเรียลไทม์'** ได้เลยครับ")
else:
    st.error("ไม่สามารถเชื่อมต่อคลังข้อมูลหลักได้")