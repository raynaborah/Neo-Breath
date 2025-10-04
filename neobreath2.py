# neobreath_advanced.py
# NeoBreath — Birth Asphyxia Early-Response (Advanced Demo)
# NOTE: Educational demo only — not medical advice.

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(page_title="NeoBreath – Advanced", page_icon="👶", layout="centered")

st.title("👶 NeoBreath — Advanced Demo")
st.caption("Early-response assistant for the first 60 seconds of life (Golden Minute). *Hackathon demo — not a medical device.*")

# -----------------------------
# Session state init
# -----------------------------
def ss_init():
    if "assessments" not in st.session_state:
        st.session_state.assessments = []   # list of dict logs
    if "timer_start" not in st.session_state:
        st.session_state.timer_start = None
    if "reassess_round" not in st.session_state:
        st.session_state.reassess_round = 1
    if "case_id" not in st.session_state:
        st.session_state.case_id = f"NB-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

ss_init()

# -----------------------------
# Sidebar controls
# -----------------------------
with st.sidebar:
    st.header("⚙️ Controls")
    simulate = st.toggle("Demo Mode: Simulate inputs", value=False, help="Prefill fields with plausible values for a smooth demo.")
    st.markdown("---")
    if st.session_state.timer_start:
        elapsed = (datetime.utcnow() - st.session_state.timer_start).total_seconds()
        remaining = max(0, 60 - int(elapsed))
        st.metric("⏱️ Golden Minute", f"{remaining}s left")
        if remaining == 0:
            st.error("⏰ Golden Minute exceeded — escalate care immediately.")
        if st.button("🔁 Reset Timer"):
            st.session_state.timer_start = None
    else:
        if st.button("▶️ Start Golden Minute Timer"):
            st.session_state.timer_start = datetime.utcnow()
    st.markdown("---")
    st.caption("Tip: Use **Demo Mode** + **Start Timer** before you present.")

# -----------------------------
# Patient / Case info
# -----------------------------
st.subheader("🧾 Case Info")
colA, colB = st.columns(2)
with colA:
    mother_id = st.text_input("Mother/Case Name (optional)", value="Patient X" if simulate else "")
    place = st.selectbox("Birth Setting", ["Clinic", "Home", "Rural Health Post", "Hospital"], index=2 if simulate else 0)
with colB:
    gest_age = st.selectbox("Gestational Age", ["Term (≥37w)", "Late Preterm (34–36w)", "Preterm (<34w)"],
                            index=(1 if simulate else 0))
    meconium = st.selectbox("Meconium-Stained Fluid?", ["No", "Yes"], index=(1 if simulate else 0))

st.markdown("---")

# -----------------------------
# Assessment inputs
# -----------------------------
st.subheader(f"🩺 Newborn Assessment (Round {st.session_state.reassess_round})")

def default_for_sim(val, sim_alt):
    return sim_alt if simulate else val

col1, col2 = st.columns(2)
with col1:
    crying = st.radio("Crying within 30 sec?", ["Yes", "No"], index=default_for_sim(0, 1))
    breathing = st.radio("Visible chest movement?", ["Yes", "No"], index=default_for_sim(0, 1))
    color = st.radio("Skin color", ["Pink", "Blue", "Pale"], index=default_for_sim(0, 1))  # Blue sim
with col2:
    movement = st.radio("Any body movement?", ["Yes", "No"], index=default_for_sim(0, 1))
    hr = st.slider("Heart Rate (bpm)", min_value=0, max_value=200, value=default_for_sim(120, 40), step=5,
                   help="Optional. If unknown, leave as is.")
    cry_time = st.slider("Time to first cry (sec)", min_value=0, max_value=180, value=default_for_sim(10, 45), step=5)

st.markdown("**Note:** Inputs are intentionally simple for low-resource use. Vitals optional.")

# -----------------------------
# Risk engine (transparent)
# -----------------------------
def compute_risk(crying, breathing, color, movement, hr, cry_time, gest_age, meconium):
    """
    Very simplified scoring model for demo/pitch transparency (NOT clinical).
    """
    score = 0
    rationale = []

    # Core signs
    if crying == "No":
        score += 3; rationale.append("No cry within 30s")
    if breathing == "No":
        score += 4; rationale.append("No visible breathing")
    if color in ["Blue", "Pale"]:
        score += 2; rationale.append(f"Skin color: {color}")
    if movement == "No":
        score += 2; rationale.append("No body movement")

    # Vitals (optional)
    if hr < 100:
        score += 3; rationale.append(f"Low heart rate ({hr} bpm)")
    if cry_time > 30:
        score += 2; rationale.append(f"Delayed first cry ({cry_time}s)")

    # Context modifiers
    if gest_age != "Term (≥37w)":
        score += 1; rationale.append(f"Prematurity risk ({gest_age})")
    if meconium == "Yes":
        score += 1; rationale.append("Meconium-stained fluid")

    # Map to level
    # 0–2: green, 3–6: yellow, ≥7: red
    if score >= 7 or (breathing == "No" and crying == "No"):
        level = "Critical"
        color_code = "red"
    elif score >= 3:
        level = "Caution"
        color_code = "yellow"
    else:
        level = "Normal"
        color_code = "green"

    return {"score": score, "level": level, "color": color_code, "rationale": rationale}

# -----------------------------
# Action cards
# -----------------------------
def show_actions(result):
    lvl = result["level"]
    if lvl == "Critical":
        st.error("🔴 **CRITICAL: High risk of birth asphyxia**")
        st.markdown(
            "- Begin **positive-pressure ventilation** if trained\n"
            "- **Stimulate**: rub back, flick soles\n"
            "- **Keep warm**: dry & wrap\n"
            "- **Call for help / escalate immediately**\n"
            "- **Reassess in 30 seconds**"
        )
    elif lvl == "Caution":
        st.warning("🟡 **CAUTION: Possible delay in breathing**")
        st.markdown(
            "- **Stimulate** gently and **clear airway if needed**\n"
            "- Keep baby **warm** (skin-to-skin)\n"
            "- **Reassess in 30 seconds**"
        )
    else:
        st.success("🟢 **NORMAL: Breathing adequate**")
        st.markdown(
            "- **Keep warm** & monitor\n"
            "- Initiate early breastfeeding when appropriate\n"
            "- Recheck if any concern"
        )

# -----------------------------
# Submit / Reassess / Save
# -----------------------------
colL, colR = st.columns([1,1])
with colL:
    run_check = st.button("🧠 Analyze Risk", use_container_width=True)
with colR:
    reassess = st.button("🔁 Reassess (30s later)", use_container_width=True)

def log_assessment(result):
    row = {
        "timestamp_utc": datetime.utcnow().isoformat(timespec="seconds"),
        "case_id": st.session_state.case_id,
        "round": st.session_state.reassess_round,
        "mother_id": mother_id,
        "place": place,
        "gest_age": gest_age,
        "meconium": meconium,
        "crying": crying,
        "breathing": breathing,
        "color": color,
        "movement": movement,
        "heart_rate": hr,
        "time_to_cry_s": cry_time,
        "risk_score": result["score"],
        "risk_level": result["level"],
        "rationale": "; ".join(result["rationale"]),
    }
    st.session_state.assessments.append(row)
    return row

if run_check:
    result = compute_risk(crying, breathing, color, movement, hr, cry_time, gest_age, meconium)

    # Badge + rationale
    colA, colB = st.columns([1,2])
    with colA:
        if result["color"] == "red":
            st.error(f"Risk: {result['level']} (score {result['score']})")
        elif result["color"] == "yellow":
            st.warning(f"Risk: {result['level']} (score {result['score']})")
        else:
            st.success(f"Risk: {result['level']} (score {result['score']})")
    with colB:
        st.markdown("**Why:** " + ", ".join(result["rationale"]))

    show_actions(result)

    # Log
    log_assessment(result)
    st.markdown("---")

if reassess:
    st.session_state.reassess_round += 1
    st.info(f"Round {st.session_state.reassess_round} — update answers if condition changed, then click **Analyze Risk** again.")

# -----------------------------
# History + Export
# -----------------------------
st.subheader("🗂️ Case Log")
if st.session_state.assessments:
    df = pd.DataFrame(st.session_state.assessments)
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV Log", data=csv, file_name=f"{st.session_state.case_id}_log.csv", mime="text/csv")
else:
    st.caption("No assessments yet. Run **Analyze Risk** to log a round.")

st.markdown("---")
with st.expander("📚 Educational Notes (for judges)"):
    st.markdown(
        "- **Golden Minute**: The first 60 seconds after birth are critical for establishing breathing.\n"
        "- This demo uses a **transparent rule/score heuristic** (no ML) to keep it explainable and offline-friendly.\n"
        "- Real deployments would include **training, protocols, and clinical validation**."
    )

st.caption("© NeoBreath (Hackathon Demo) — Built for CruzHacks. Not for clinical use.")
