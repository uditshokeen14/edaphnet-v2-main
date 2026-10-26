"""EdaphNet v2: Agritech & Soil Intelligence Dashboard (Streamlit Cloud & Docker Ready).

Features 4 integrated AI/expert modules:
  1. Leaf Disease Scanner (MobileNetV3-Large, 38 classes, calibrated temperature confidence)
  2. Soil Photo Carbon & Nitrogen Estimator (CIELAB colour witness -> KSSL trained Brain)
  3. Crop Suitability Advisor (FAO EcoCrop rule engine with multi-soil uncertainty)
  4. Lab Report Audit & Swap Detector (EdaphNet joint batch Bayesian error discovery)
"""
import base64
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

# ------------------------------------------------------------------ Page Setup
st.set_page_config(
    page_title="EdaphNet: Agritech & Soil Intelligence",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e4620;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4b5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8faf7;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 10px;
    }
    .status-badge-ok {
        background: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-badge-warn {
        background: #fef9c3;
        color: #854d0e;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .status-badge-bad {
        background: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ Model & Engine Cache
@st.cache_resource(show_spinner="Loading Leaf Disease Backbone (MobileNetV3)...")
def get_leaf_model():
    from app.leaf.model import MODEL_PATH, LeafModel
    if not MODEL_PATH.exists():
        st.error("models/leaf_head.joblib missing. Please ensure the model file exists.")
        return None
    try:
        return LeafModel()
    except (RuntimeError, OSError, ValueError) as e:
        st.error(f"Leaf disease model could not be loaded: {e}")
        return None


@st.cache_resource(show_spinner="Loading Soil Spectroscopy Brain...")
def get_soil_engine():
    try:
        from serve_demo import Engine
        return Engine()
    except (RuntimeError, OSError, ValueError, SystemExit) as e:
        st.error(f"Soil Spectroscopy Brain could not be loaded: {e}")
        return None


@st.cache_data
def get_crops_data():
    try:
        from app.crop.suitability import load_crops
        return load_crops()
    except (OSError, ValueError, KeyError) as e:
        st.error(f"FAO crop knowledge could not be loaded: {e}")
        return []


@st.cache_data
def get_disease_knowledge():
    k_path = ROOT / "app" / "knowledge" / "diseases.json"
    if k_path.exists():
        return json.loads(k_path.read_text(encoding="utf-8"))
    return {"diseases": {}, "sources": {}}


# ------------------------------------------------------------------ Sidebar
with st.sidebar:
    st.image("https://raw.githubusercontent.com/google/material-design-icons/master/png/image/eco/materialicons/48dp/2x/baseline_eco_black_48dp.png", width=50)
    st.markdown("### 🌱 EdaphNet v2")
    st.markdown("**Dual-Witness Soil & Agritech Intelligence**")
    st.markdown("---")

    st.markdown("#### System Status")
    leaf_m = get_leaf_model()
    soil_e = get_soil_engine()
    crops_d = get_crops_data()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Leaf Classes", len(leaf_m.classes) if leaf_m and hasattr(leaf_m, "classes") else "N/A")
    with col2:
        st.metric("FAO Crops", len(crops_d) if crops_d else "N/A")

    st.caption("✅ MobileNetV3 + Logistic Calibration")
    st.caption("✅ KSSL Vis-NIR Colour Brain")
    st.caption("✅ FAO EcoCrop Suitability Engine")

    st.markdown("---")
    st.markdown("#### About")
    st.info(
        "EdaphNet v2 combines smartphone proximal colour witnesses with soil spectroscopy and deep learning "
        "to verify soil testing reports, diagnose crop leaf pathologies, and recommend optimal crops."
    )


# ------------------------------------------------------------------ Header
st.markdown('<div class="main-header">EdaphNet Agricultural Intelligence System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Field-ready crop disease diagnostics, soil carbon estimation, FAO EcoCrop planning, and laboratory report audit.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ Tabs
tab_leaf, tab_soil, tab_crops, tab_report = st.tabs([
    "🌿 Leaf Disease Diagnosis",
    "🧪 Soil Carbon & Properties",
    "🌾 Crop Suitability Advisor",
    "🔍 Lab Report Audit & Consistency"
])


# ================================================================== TAB 1: Leaf Disease
with tab_leaf:
    st.markdown("### 🌿 Leaf Disease Scanner")
    st.markdown("Upload or capture a leaf photo. Uses a calibrated **MobileNetV3-Large** backbone with temperature scaling and an abstention threshold.")

    col_input, col_result = st.columns([1, 1])

    with col_input:
        input_method = st.radio("Input method:", ["Upload Image", "Use Camera"], horizontal=True, key="leaf_in_method")
        leaf_file = None
        if input_method == "Upload Image":
            leaf_file = st.file_uploader("Upload leaf photo (JPG/PNG)", type=["jpg", "jpeg", "png"], key="leaf_file")
        else:
            leaf_file = st.camera_input("Capture leaf photo", key="leaf_cam")

        if leaf_file:
            try:
                pil_leaf = Image.open(leaf_file)
                pil_leaf = ImageOps.exif_transpose(pil_leaf).convert("RGB")
                st.image(pil_leaf, caption="Input Leaf Photo", use_container_width=True)
            except (OSError, ValueError) as e:
                st.error(f"Could not read image: {e}")
                pil_leaf = None
        else:
            pil_leaf = None

    with col_result:
        if leaf_file and pil_leaf and leaf_m:
            with st.spinner("Analyzing leaf pathology..."):
                try:
                    pred = leaf_m.predict_pil(pil_leaf)
                except (RuntimeError, ValueError) as e:
                    st.error(f"Inference error: {e}")
                    pred = None

                if isinstance(pred, dict) and isinstance(pred.get("top"), list) and len(pred["top"]) > 0:
                    diseases_kb = get_disease_knowledge()
                    top_list = [t for t in pred["top"] if isinstance(t, dict)]
                    if top_list:
                        top1 = top_list[0]
                        is_confident = bool(pred.get("confident"))
                        crop_name = str(top1.get("crop", "")).title()
                        condition_name = str(top1.get("condition", "")).title()
                        prob = float(top1.get("probability", 0.0))
                        cls_name = str(top1.get("class", ""))

                        st.markdown("#### Diagnostic Verdict")
                        if is_confident:
                            if cls_name.endswith("healthy"):
                                st.markdown(f'<span class="status-badge-ok">HEALTHY</span> **{crop_name}** ({prob*100:.1f}% confidence)', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<span class="status-badge-warn">PATHOLOGY DETECTED</span> **{crop_name} — {condition_name}** ({prob*100:.1f}% confidence)', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<span class="status-badge-bad">UNCERTAIN PREDICTION</span> Best match: **{crop_name} — {condition_name}** ({prob*100:.1f}%)', unsafe_allow_html=True)
                            st.warning("⚠️ Prediction confidence is below the reliability threshold (0.50). Confirm with a local Krishi Vigyan Kendra / Extension Officer before taking chemical action.")

                        st.markdown("##### Top Predictions")
                        for item in top_list:
                            c_prob = float(item.get("probability", 0.0))
                            c_crop = str(item.get("crop", "")).title()
                            c_cond = str(item.get("condition", "")).title()
                            c_label = f"{c_crop} — {c_cond}"
                            st.write(f"**{c_label}** ({c_prob*100:.1f}%)")
                            st.progress(min(1.0, max(0.0, c_prob)))

                        # Sourced disease management information
                        d_info = diseases_kb.get("diseases", {}).get(cls_name) if isinstance(diseases_kb, dict) else None
                        if isinstance(d_info, dict):
                            st.markdown("---")
                            st.markdown("##### 📋 Recommended Management (Extension Guidelines)")
                            st.markdown(f"**Causal Agent:** {d_info.get('cause', 'Unknown')}")
                            manage_steps = d_info.get("manage", [])
                            if isinstance(manage_steps, list):
                                for step in manage_steps:
                                    st.markdown(f"- {step}")
                            source_key = d_info.get("source")
                            sources_dict = diseases_kb.get("sources", {}) if isinstance(diseases_kb, dict) else {}
                            source_url = sources_dict.get(source_key) if isinstance(sources_dict, dict) else None
                            if source_url:
                                st.markdown(f"[🔗 View Sourced Extension Reference]({source_url})")
        elif leaf_file and not leaf_m:
            st.error("Leaf disease model is not available. Please ensure models/leaf_head.joblib is present.")
        elif not leaf_file:
            st.info("👈 Upload or capture a leaf image to run automated pathology identification.")


# ================================================================== TAB 2: Soil Photo Carbon
with tab_soil:
    st.markdown("### 🧪 Soil Photo Carbon & Properties Estimator")
    st.markdown("Estimates Organic Carbon (OC), Total Nitrogen (N), and Total Carbon (Ctot) from soil photo colour using our calibrated KSSL model.")

    col_s_in, col_s_out = st.columns([1, 1])

    with col_s_in:
        soil_input_method = st.radio("Soil image input:", ["Upload Photo", "Camera Capture"], horizontal=True, key="soil_in_method")
        soil_file = None
        if soil_input_method == "Upload Photo":
            soil_file = st.file_uploader("Upload soil photo (dry, crushed soil)", type=["jpg", "jpeg", "png"], key="soil_file")
        else:
            soil_file = st.camera_input("Capture soil sample", key="soil_cam")

        use_colour_card = st.checkbox("Photo includes a ColorChecker 24 card", value=False, help="Allows accurate colour correction")
        moist_hint = st.checkbox("Soil sample is air-dried", value=True, help="Moist soils look artificially darker")

        if soil_file:
            try:
                pil_soil = Image.open(soil_file)
                pil_soil = ImageOps.exif_transpose(pil_soil).convert("RGB")
                st.image(pil_soil, caption="Soil Photo", use_container_width=True)
            except (OSError, ValueError) as e:
                st.error(f"Could not read soil image: {e}")
                pil_soil = None
        else:
            pil_soil = None

    with col_s_out:
        if soil_file and pil_soil and soil_e:
            with st.spinner("Analyzing soil colour witness..."):
                w, h = pil_soil.size
                m = 0.25
                box = [w * m, h * m, w * (1 - m), h * (1 - m)]
                rgba = np.dstack([np.asarray(pil_soil), np.full((h, w), 255, np.uint8)])
                req = {
                    "width": w, "height": h,
                    "rgba": base64.b64encode(rgba.tobytes()).decode(),
                    "soil_box": box,
                    "corners": None,
                    "moist_hint": not moist_hint
                }
                try:
                    res = soil_e.analyze(req)
                except ValueError as e:
                    st.error(f"Soil analysis: {e}")
                    res = None

                if isinstance(res, dict):
                    step1 = res.get("step1")
                    preds = res.get("step2")

                    if isinstance(step1, dict):
                        hex_col = str(step1.get("hex", "#785032"))
                        raw_lab = step1.get("lab")
                        lab_vals = raw_lab if isinstance(raw_lab, list) and len(raw_lab) >= 3 else [50, 10, 15]

                        st.markdown("#### Colour Witness Extraction")
                        col_sw, col_lab = st.columns([1, 3])
                        with col_sw:
                            st.markdown(
                                f'<div style="background-color: {hex_col}; width: 80px; height: 80px; border-radius: 8px; border: 2px solid #cbd5e1;"></div>',
                                unsafe_allow_html=True
                            )
                        with col_lab:
                            st.write(f"**Hex:** `{hex_col}`")
                            st.write(f"**CIELAB:** $L^*={lab_vals[0]}$, $a^*={lab_vals[1]}$, $b^*={lab_vals[2]}$")

                        warnings = step1.get("warnings")
                        if isinstance(warnings, list):
                            for w_msg in warnings:
                                st.warning(f"⚠️ {w_msg}")

                    if isinstance(preds, list):
                        st.markdown("#### Predicted Soil Properties (90% Uncertainty Ranges)")
                        name_map = {"OC": "Organic Carbon (OC)", "N": "Total Nitrogen (N)", "Ctot": "Total Carbon (Ctot)"}
                        for p in preds:
                            if isinstance(p, dict):
                                p_name = str(p.get("name", ""))
                                raw_pred = p.get("predicted")
                                pred_v = float(raw_pred) if isinstance(raw_pred, (int, float, str)) else 0.0
                                raw_lo = p.get("lo")
                                lo_v = float(raw_lo) if isinstance(raw_lo, (int, float, str)) else 0.0
                                raw_hi = p.get("hi")
                                hi_v = float(raw_hi) if isinstance(raw_hi, (int, float, str)) else 0.0

                                full_name = name_map.get(p_name, p_name)
                                st.markdown(f"**{full_name}:** `{pred_v:.2f}%`  *(90% Range: {lo_v:.2f}% — {hi_v:.2f}%)*")
                                st.progress(min(1.0, max(0.0, pred_v / 10.0)))
        elif soil_file and not soil_e:
            st.error("Soil Spectroscopy Brain is not available. Please ensure models/colour_brain_kssl3.joblib exists.")
        elif not soil_file:
            st.info("👈 Upload or capture a soil sample photo to estimate organic carbon and nitrogen.")


# ================================================================== TAB 3: Crop Suitability
with tab_crops:
    st.markdown("### 🌾 Multi-Soil Crop Suitability Advisor")
    st.markdown("Ranks 25 Indian agricultural crops using **FAO EcoCrop ranges** and Liebig's law of the minimum.")

    col_c_in1, col_c_in2, col_c_in3 = st.columns(3)

    with col_c_in1:
        temp_c = st.slider("Mean Temperature (°C)", min_value=5.0, max_value=45.0, value=26.0, step=0.5)
        rain_mm = st.slider("Annual Rainfall (mm)", min_value=100.0, max_value=3000.0, value=850.0, step=25.0)

    with col_c_in2:
        ph_mode = st.radio("Soil pH Assessment:", ["Single pH Value", "Uncertain / Multi-Soil Range"], horizontal=True)
        if ph_mode == "Single pH Value":
            ph_val = st.slider("Soil pH (H₂O)", min_value=3.5, max_value=10.0, value=6.5, step=0.1)
            ph_lo: float = 5.5
            ph_hi: float = 7.8
        else:
            ph_val = None
            ph_range = st.slider("pH Range", min_value=4.0, max_value=9.5, value=(5.5, 7.8), step=0.1)
            ph_lo, ph_hi = float(ph_range[0]), float(ph_range[1])

    with col_c_in3:
        texture = st.selectbox("Soil Texture Class:", ["medium (loam/silt)", "light (sandy)", "heavy (clay)"])
        tex_code = texture.split()[0]
        irrigated = st.checkbox("Field is Irrigated (mitigates rainfall deficit)", value=False)
        min_score = st.slider("Minimum Suitability Score (%)", min_value=0, max_value=100, value=40, step=5)

    if st.button("Calculate Crop Suitability", type="primary", key="btn_crops"):
        from app.crop.suitability import Field, ph_range_scenarios, rank_crops

        if not crops_d:
            st.error("Crop database could not be loaded.")
        else:
            if ph_val is not None:
                field_obj = Field(ph=ph_val, rain_mm=rain_mm, temp_c=temp_c, texture=tex_code, irrigated=irrigated)
                ranked = rank_crops(field_obj, crops_d)
                scenario_desc = f"Single soil (pH {ph_val:.1f}, {temp_c}°C, {rain_mm:.0f} mm)"
            else:
                scenarios = ph_range_scenarios(ph_lo, ph_hi, rain_mm, temp_c, texture=tex_code, irrigated=irrigated)
                ranked = rank_crops(scenarios, crops_d)
                scenario_desc = f"Multi-soil average (pH range {ph_lo:.1f} to {ph_hi:.1f})"

            st.markdown(f"#### Results ({scenario_desc})")

            crop_meta = {c["name"]: c for c in crops_d}
            table_rows = []
            for r in ranked:
                score_pct = round(r.score * 100, 1)
                if score_pct < min_score:
                    continue

                meta = crop_meta.get(r.name, {})
                t_opt = meta.get("temp_opt")
                r_opt = meta.get("rain_opt")
                p_opt = meta.get("ph_opt")

                temp_str = f"{t_opt[0]:g}–{t_opt[1]:g}°C" if t_opt and len(t_opt) == 2 and None not in t_opt else "N/A"
                rain_str = f"{r_opt[0]:g}–{r_opt[1]:g} mm" if r_opt and len(r_opt) == 2 and None not in r_opt else "N/A"
                ph_str = f"{p_opt[0]:g}–{p_opt[1]:g}" if p_opt and len(p_opt) == 2 and None not in p_opt else "N/A"
                lim_str = (r.limiting or "None").replace("_", " ").title()

                table_rows.append({
                    "Crop": r.name,
                    "Suitability": f"{score_pct}%",
                    "Score": score_pct,
                    "Limiting Factor": lim_str,
                    "Temperature Range": temp_str,
                    "Rainfall Range": rain_str,
                    "pH Range": ph_str,
                })

            df_ranked = pd.DataFrame(table_rows)
            if not df_ranked.empty:
                st.dataframe(
                    df_ranked[["Crop", "Suitability", "Limiting Factor", "Temperature Range", "Rainfall Range", "pH Range"]],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("No crops met the minimum suitability threshold with the specified climate/soil constraints.")


# ================================================================== TAB 4: Lab Report Audit
with tab_report:
    st.markdown("### 🔍 Soil Lab Report Audit & Swap Detector")
    st.markdown("Verifies whether a laboratory test report is statistically consistent with a soil photo witness, detecting accidental sample swaps and transcription slips.")

    col_rep_in, col_rep_out = st.columns([1, 1])

    with col_rep_in:
        audit_file = st.file_uploader("Upload Soil Sample Photo", type=["jpg", "jpeg", "png"], key="audit_photo")
        st.markdown("##### Laboratory Report Data")
        rep_oc = st.number_input("Reported Organic Carbon (OC %)", min_value=0.01, max_value=50.0, value=2.50, step=0.1)
        rep_n = st.number_input("Reported Total Nitrogen (N %)", min_value=0.001, max_value=5.0, value=0.18, step=0.01)
        rep_ctot = st.number_input("Reported Total Carbon (Ctot %)", min_value=0.01, max_value=60.0, value=2.80, step=0.1)

    with col_rep_out:
        if audit_file and soil_e:
            try:
                pil_audit = Image.open(audit_file)
                pil_audit = ImageOps.exif_transpose(pil_audit).convert("RGB")
            except (OSError, ValueError) as e:
                st.error(f"Could not read audit photo: {e}")
                pil_audit = None

            if pil_audit:
                w, h = pil_audit.size
                box = [w * 0.25, h * 0.25, w * 0.75, h * 0.75]
                rgba = np.dstack([np.asarray(pil_audit), np.full((h, w), 255, np.uint8)])

                report_dict = {
                    "OC": rep_oc,
                    "N": rep_n,
                    "Ctot": rep_ctot
                }

                req = {
                    "width": w, "height": h,
                    "rgba": base64.b64encode(rgba.tobytes()).decode(),
                    "soil_box": box,
                    "report": report_dict
                }

                with st.spinner("Checking report consistency against soil colour witness..."):
                    try:
                        audit_res = soil_e.analyze(req)
                    except ValueError as e:
                        st.error(f"Soil analysis: {e}")
                        audit_res = None

                    if isinstance(audit_res, dict):
                        st.markdown("#### Consistency Evaluation")
                        step2 = audit_res.get("step2")
                        if isinstance(step2, list):
                            for p in step2:
                                if isinstance(p, dict):
                                    name = str(p.get("name", ""))
                                    rep_v = p.get("reported")
                                    pred_v = p.get("predicted")
                                    z_val = p.get("z")
                                    status = str(p.get("status", "unknown"))

                                    badge_cls = "status-badge-ok" if status == "consistent" else ("status-badge-warn" if status == "unusual" else "status-badge-bad")
                                    rep_str = f"{rep_v:.2f}%" if isinstance(rep_v, (int, float)) else "N/A"
                                    pred_str = f"{pred_v:.2f}%" if isinstance(pred_v, (int, float)) else "N/A"
                                    z_str = f"(z = {z_val:+.2f})" if isinstance(z_val, (int, float)) else ""

                                    col_m1, col_m2 = st.columns(2)
                                    with col_m1:
                                        st.markdown(f"**{name} Reported:** `{rep_str}` &nbsp; <span class=\"{badge_cls}\">{status.upper()}</span> {z_str}", unsafe_allow_html=True)
                                    with col_m2:
                                        st.markdown(f"**{name} Predicted from Colour:** `{pred_str}`", unsafe_allow_html=True)

                        step4 = audit_res.get("step4")
                        if isinstance(step4, dict):
                            st.markdown("---")
                            st.markdown("#### Joint Batch Verdict")
                            raw_rows = step4.get("rows")
                            rows = [r for r in raw_rows if isinstance(r, dict)] if isinstance(raw_rows, list) else []
                            mine = next((r for r in rows if r.get("yours")), rows[-1] if rows else {})
                            rank = mine.get("rank", "N/A")
                            score = mine.get("score")
                            why = str(mine.get("why") or "")
                            verdict = str(step4.get("verdict", "N/A"))

                            v_badge = "status-badge-ok" if verdict == "looks fine" else ("status-badge-warn" if verdict == "check" else "status-badge-bad")

                            st.markdown(f"**Verdict:** <span class=\"{v_badge}\">{verdict.upper()}</span>", unsafe_allow_html=True)
                            st.write(f"**Cohort Batch Suspicion Rank:** `{rank}/12`")
                            if isinstance(score, (int, float)):
                                st.write(f"**Batch Suspicion Score:** `{score:.3f}`")
                            if why:
                                st.warning(f"🔎 Diagnostic Detail: {why}")
        elif audit_file and not soil_e:
            st.error("Soil Spectroscopy Brain is not available. Please ensure models/colour_brain_kssl3.joblib exists.")
        elif not audit_file:
            st.info("👈 Upload a soil photo and enter the lab report values to audit consistency.")
