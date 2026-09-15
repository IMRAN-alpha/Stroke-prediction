import streamlit as st
import pandas as pd
import joblib

# =====================================================
# PAGE CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="Stroke Risk Prediction",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# HTML RENDER HELPER
# -----------------------------------------------------
# st.markdown(..., unsafe_allow_html=True) STILL runs the
# text through Streamlit's Markdown parser before injecting
# it as HTML. Markdown treats any line indented 4+ spaces as
# a literal code block — and Python f-strings/triple-quoted
# strings almost always carry leading indentation from how
# they're written in source. That indentation was silently
# turning chunks of HTML (like the recommendations box) into
# a rendered <code> block instead of real markup.
#
# Fix: strip leading whitespace from every line before it
# ever reaches st.markdown. HTML doesn't care about
# indentation (unless you're inside a <pre>/<code> tag,
# which we never are here), so this is always safe.
# =====================================================
def render_html(html: str):
    flattened = "\n".join(line.strip() for line in html.strip().split("\n"))
    st.markdown(flattened, unsafe_allow_html=True)


# =====================================================
# THEME / CSS
# =====================================================
render_html(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600;700&display=swap');

    :root {
        --bg: #F5F8F9;
        --surface: #FFFFFF;
        --surface-alt: #EEF4F5;
        --ink: #16232E;
        --muted: #5C7080;
        --primary: #0E7C7B;
        --primary-dark: #0A5958;
        --line: #2FA6A0;
        --border: #DCE6E8;
        --risk-high: #C1442D;
        --risk-high-bg: #FBEAE6;
        --risk-low: #1F8A5F;
        --risk-low-bg: #E7F5EE;
    }

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
        color: var(--ink);
    }

    .stApp {
        background: var(--bg);
    }

    h1, h2, h3 {
        font-family: 'IBM Plex Sans Condensed', sans-serif !important;
        letter-spacing: 0.01em;
    }

    section[data-testid="stSidebar"] {
        background: var(--primary-dark);
    }
    section[data-testid="stSidebar"] * {
        color: #EAF4F3 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.18);
    }
    section[data-testid="stSidebar"] .stAlert {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 8px;
    }

    .clinic-header {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.6rem 2rem 0.4rem 2rem;
        margin-bottom: 1.4rem;
    }
    .clinic-eyebrow {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--primary);
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .clinic-title {
        font-family: 'IBM Plex Sans Condensed', sans-serif;
        font-size: 2.1rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
        color: var(--ink);
    }
    .clinic-sub {
        color: var(--muted);
        font-size: 0.98rem;
        margin-bottom: 0.6rem;
        max-width: 640px;
    }

    .section-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.4rem 1.6rem 0.6rem 1.6rem;
        margin-bottom: 1.2rem;
    }
    .section-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--primary);
        font-weight: 600;
        margin-bottom: 0.2rem;
    }
    .section-title {
        font-family: 'IBM Plex Sans Condensed', sans-serif;
        font-size: 1.3rem;
        font-weight: 700;
        margin: 0 0 0.8rem 0;
        border-bottom: 1px solid var(--border);
        padding-bottom: 0.7rem;
    }

    .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        font-family: 'IBM Plex Mono', monospace !important;
        border-radius: 8px !important;
    }
    label, .stSelectbox label, .stNumberInput label {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-weight: 500 !important;
        color: var(--ink) !important;
        font-size: 0.88rem !important;
    }

    div[data-testid="stButton"] button {
        background: var(--primary);
        color: #FFFFFF;
        font-family: 'IBM Plex Sans Condensed', sans-serif;
        font-weight: 700;
        letter-spacing: 0.03em;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 0;
        font-size: 1.02rem;
        transition: background 0.15s ease;
    }
    div[data-testid="stButton"] button:hover {
        background: var(--primary-dark);
        color: #FFFFFF;
    }

    .result-card {
        border-radius: 16px;
        padding: 1.8rem 2rem 1.6rem 2rem;
        margin-top: 1rem;
        border: 1px solid var(--border);
    }
    .result-high { background: var(--risk-high-bg); border-color: #EFC7BC; }
    .result-low  { background: var(--risk-low-bg);  border-color: #BFE3D0; }

    .result-eyebrow {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    .result-high .result-eyebrow { color: var(--risk-high); }
    .result-low .result-eyebrow  { color: var(--risk-low); }

    .result-headline {
        font-family: 'IBM Plex Sans Condensed', sans-serif;
        font-size: 1.7rem;
        font-weight: 700;
        margin: 0 0 1rem 0;
    }
    .result-high .result-headline { color: var(--risk-high); }
    .result-low .result-headline  { color: var(--risk-low); }

    .vitals-row {
        display: flex;
        gap: 2.2rem;
        margin-bottom: 0.8rem;
        align-items: flex-end;
    }
    .vital-block {
        font-family: 'IBM Plex Mono', monospace;
    }
    .vital-value {
        font-size: 2.1rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .vital-label {
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 0.78rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.2rem;
    }
    .result-high .vital-value { color: var(--risk-high); }
    .result-low .vital-value  { color: var(--risk-low); }

    .waveform-strip {
        background: rgba(255,255,255,0.55);
        border-radius: 10px;
        padding: 0.4rem 0.8rem;
        margin-bottom: 1rem;
    }

    .rec-box {
        background: rgba(255,255,255,0.65);
        border-radius: 10px;
        padding: 1rem 1.3rem;
    }
    .rec-box strong {
        font-family: 'IBM Plex Sans Condensed', sans-serif;
        font-size: 1rem;
        letter-spacing: 0.02em;
    }
    .rec-box ul {
        margin: 0.5rem 0 0 0;
        padding-left: 1.1rem;
    }
    .rec-box li {
        margin-bottom: 0.35rem;
        color: var(--ink);
        font-size: 0.94rem;
        line-height: 1.4;
    }

    .clinic-footer {
        color: var(--muted);
        font-size: 0.8rem;
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border);
    }
    </style>
    """
)

# =====================================================
# LOAD MODEL
# =====================================================
model = joblib.load("stroke_model.pkl")
scaler = joblib.load("scaler.pkl")
model_columns = joblib.load("model_columns.pkl")


# =====================================================
# ECG WAVEFORM (signature element)
# =====================================================
def ecg_svg(kind="steady", color="#2FA6A0", height=64):
    if kind == "steady":
        path = (
            "M0,32 L40,32 L52,32 L58,10 L64,54 L70,32 L110,32 "
            "L150,32 L162,32 L168,10 L174,54 L180,32 L220,32 "
            "L260,32 L272,32 L278,10 L284,54 L290,32 L330,32 "
            "L370,32 L382,32 L388,10 L394,54 L400,32 L440,32"
        )
    else:
        path = (
            "M0,32 L30,32 L40,18 L48,46 L56,8 L64,40 L72,26 L80,32 "
            "L110,32 L120,44 L128,14 L136,50 L144,20 L152,32 "
            "L180,32 L190,12 L198,48 L206,28 L214,32 "
            "L250,32 L262,40 L270,16 L278,52 L286,24 L294,32 "
            "L330,32 L342,20 L350,44 L358,12 L366,32 "
            "L400,32 L412,46 L420,18 L428,32 L440,32"
        )
    points = path.replace("M", "").replace("L", " ")
    return (
        f'<svg width="100%" height="{height}" viewBox="0 0 440 64" '
        f'preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">'
        f'<polyline points="{points}" fill="none" stroke="{color}" '
        f'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" '
        f'opacity="0.9"/></svg>'
    )


# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    st.markdown("### 🩺 Stroke Prediction")
    st.markdown("---")
    st.write(
        "This application uses a machine learning model to estimate "
        "the likelihood of stroke based on patient health information."
    )
    st.markdown("---")
    st.markdown("**Developer**")
    st.write("MD IMRAN")
    st.caption("Public Health · AI & Machine Learning")
    st.markdown("--")
    st.info(
        "This application is intended for educational purposes only "
        "and should not replace professional medical advice."
    )

# =====================================================
# HEADER
# =====================================================
render_html(
    f"""
    <div class="clinic-header">
        <div class="clinic-eyebrow">Clinical Decision Support · Preliminary Screening</div>
        <div class="clinic-title">🩺 Stroke Risk Prediction System</div>
        <div class="clinic-sub">
            Estimate an individual's stroke risk using a trained machine learning model.
            Enter the patient's information below and run the assessment.
        </div>
        {ecg_svg("steady", "#B7D9D8", height=48)}
    </div>
    """
)

# =====================================================
# INPUT FIELDS
# =====================================================
render_html(
    """
    <div class="section-card">
        <div class="section-label">Step 1</div>
        <div class="section-title">Patient Demographics</div>
    """
)
d1, d2, d3 = st.columns(3)
with d1:
    age = st.number_input("Age", min_value=0, max_value=120, value=30)
with d2:
    gender = st.selectbox("Gender", ["Male", "Female"])
with d3:
    ever_married = st.selectbox("Ever Married", ["No", "Yes"])
render_html("</div>")

render_html(
    """
    <div class="section-card">
        <div class="section-label">Step 2</div>
        <div class="section-title">Clinical Vitals &amp; Labs</div>
    """
)
v1, v2, v3, v4 = st.columns(4)
with v1:
    avg_glucose_level = st.number_input(
        "Avg. Glucose Level", min_value=0.0, max_value=300.0, value=100.0
    )
with v2:
    bmi = st.number_input("BMI", min_value=0.0, max_value=80.0, value=25.0)
with v3:
    hypertension = st.selectbox("Hypertension", ["No", "Yes"])
with v4:
    heart_disease = st.selectbox("Heart Disease", ["No", "Yes"])
render_html("</div>")

render_html(
    """
    <div class="section-card">
        <div class="section-label">Step 3</div>
        <div class="section-title">Lifestyle &amp; History</div>
    """
)
l1, l2, l3 = st.columns(3)
with l1:
    work_type = st.selectbox(
        "Work Type",
        ["Private", "Self-employed", "Govt_job", "children", "Never_worked"],
    )
with l2:
    residence_type = st.selectbox("Residence Type", ["Urban", "Rural"])
with l3:
    smoking_status = st.selectbox(
        "Smoking Status",
        ["never smoked", "formerly smoked", "smokes", "Unknown"],
    )
render_html("</div>")

predict_clicked = st.button(" Predict Stroke Risk", use_container_width=True)

# =====================================================
# PREDICTION
# =====================================================
if predict_clicked:

    with st.spinner("Analyzing patient information..."):

        input_dict = {
            "age": age,
            "hypertension": 1 if hypertension == "Yes" else 0,
            "heart_disease": 1 if heart_disease == "Yes" else 0,
            "avg_glucose_level": avg_glucose_level,
            "bmi": bmi,
            "gender": gender,
            "ever_married": ever_married,
            "work_type": work_type,
            "Residence_type": residence_type,
            "smoking_status": smoking_status,
        }

        input_df = pd.DataFrame([input_dict])

        input_encoded = pd.get_dummies(
            input_df,
            columns=[
                "gender",
                "ever_married",
                "work_type",
                "Residence_type",
                "smoking_status",
            ],
            drop_first=True,
            dtype=int,
        )

        for col in model_columns:
            if col not in input_encoded.columns:
                input_encoded[col] = 0

        input_encoded = input_encoded[model_columns]

        cols_to_scale = ["age", "avg_glucose_level", "bmi"]
        input_encoded[cols_to_scale] = scaler.transform(input_encoded[cols_to_scale])

        prediction = model.predict(input_encoded)[0]
        probability = model.predict_proba(input_encoded)[0][1]

    is_high = prediction == 1
    result_class = "result-high" if is_high else "result-low"
    waveform = ecg_svg(
        "irregular" if is_high else "steady",
        "#C1442D" if is_high else "#1F8A5F",
        height=56,
    )

    if is_high:
        recs = (
            "<ul>"
            "<li>Consult a healthcare professional promptly.</li>"
            "<li>Monitor blood pressure regularly.</li>"
            "<li>Maintain healthy blood sugar levels.</li>"
            "<li>Stay physically active.</li>"
            "<li>Eat a balanced diet.</li>"
            "<li>Avoid smoking and excessive alcohol consumption.</li>"
            "</ul>"
        )
        headline = "Elevated Stroke Risk Detected"
        eyebrow = "Result · Requires Attention"
    else:
        recs = (
            "<ul>"
            "<li>Continue maintaining a healthy lifestyle.</li>"
            "<li>Exercise regularly.</li>"
            "<li>Eat a balanced diet.</li>"
            "<li>Attend routine medical check-ups.</li>"
            "<li>Monitor your health periodically.</li>"
            "</ul>"
        )
        headline = "Lower Stroke Risk Detected"
        eyebrow = "Result · Within Expected Range"

    render_html(
        f"""
        <div class="result-card {result_class}">
            <div class="result-eyebrow">{eyebrow}</div>
            <div class="result-headline">{headline}</div>
            <div class="vitals-row">
                <div class="vital-block">
                    <div class="vital-value">{probability:.1%}</div>
                    <div class="vital-label">Estimated Probability</div>
                </div>
                <div class="vital-block">
                    <div class="vital-value">{"HIGH" if is_high else "LOW"}</div>
                    <div class="vital-label">Risk Level</div>
                </div>
            </div>
            <div class="waveform-strip">{waveform}</div>
            <div class="rec-box">
                <strong>Recommendations</strong>
                {recs}
            </div>
        </div>
        """
    )

# =====================================================
# FOOTER
# =====================================================
render_html(
    """
    <div class="clinic-footer">
        ⚠️ Disclaimer: This application is intended for educational purposes only
        and should not be used as a substitute for professional medical advice,
        diagnosis, or treatment.
    </div>
    """
)
