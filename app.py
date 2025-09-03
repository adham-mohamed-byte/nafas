
# -*- coding: utf-8 -*-
import streamlit as st
from PIL import Image, ImageDraw
import io, random, math, hashlib

st.set_page_config(page_title="LungSight Pro (Demo)", page_icon="🫁", layout="wide")

PRIMARY = "#6C2BD9"  # violet
BG = "#0B021B"
TEXT = "#F5F3FF"

st.markdown(f"""
<style>
.stApp {{ background: radial-gradient(60% 80% at 20% 10%, #1E0B45 0%, #0B021B 60%); color: {TEXT}; }}
.block-container {{ padding-top:1rem; padding-bottom:2rem; }}
.stButton>button {{ background: {PRIMARY} !important; color: white !important; border-radius: 12px; padding: .6rem 1rem; }}
.card {{ background: linear-gradient(180deg, rgba(108,43,217,0.08), rgba(108,43,217,0.02)); border-radius: 14px; padding: 1rem; border: 1px solid rgba(255,255,255,0.04); }}
.small {{ opacity:0.9; font-size:0.95rem; }}
.disclaimer {{ background: rgba(255,255,255,0.04); border-left: 4px solid {PRIMARY}; padding: .75rem 1rem; border-radius: 10px; }}
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([2,1])
with col1:
    st.title("LungSight Pro")
    st.markdown("**Comprehensive patient intake & simulated tumor analysis**")
with col2:
    st.image("https://raw.githubusercontent.com/streamlit/demo/master/hello/st_lottie.gif", width=96)

st.markdown("""
<div class="disclaimer">
<strong>Important:</strong> This application is a simulation for demonstration purposes. It does NOT replace clinical assessment. Clinical decisions must be made by qualified healthcare professionals.
</div>
""", unsafe_allow_html=True)

# Sidebar - patient inputs
st.sidebar.header("Patient information")
age = st.sidebar.number_input("Age", min_value=18, max_value=100, value=55)
gender = st.sidebar.selectbox("Gender", ["Male", "Female", "Other"])
smoker = st.sidebar.selectbox("Smoking status", ["Never", "Former", "Current"])
packs_per_day = st.sidebar.slider("Packs per day (if smoker)", 0.0, 5.0, 0.5, 0.1)
years_smoked = st.sidebar.slider("Years smoked (if applicable)", 0, 60, 10)
family_history = st.sidebar.selectbox("Family history of lung cancer", ["No", "Yes"])
copd = st.sidebar.selectbox("COPD or chronic lung disease", ["No", "Yes"])
exposures = st.sidebar.multiselect("Environmental/Occupational exposures", ["Asbestos", "Radon", "Diesel exhaust", "Silica", "Other"])
symptoms = st.sidebar.multiselect("Symptoms", ["Chronic cough", "Hemoptysis (blood in sputum)", "Dyspnea (shortness of breath)", "Unexplained weight loss", "Chest pain", "Fatigue"])

st.sidebar.markdown("---")
st.sidebar.header("Image (optional)")
img_file = st.sidebar.file_uploader("Upload chest X-ray (PNG/JPG)", type=["png","jpg","jpeg"])
demo_mode = st.sidebar.checkbox("Demo overlay (simulate lesions)", value=True)

# Utility functions
def logistic(x): return 1/(1+math.exp(-x))

def compute_risk(age, smoker, years_smoked, packs, family, copd, exposures, symptoms):
    x = -6.0
    x += 0.04 * age
    x += 0.9 if smoker == "Current" else 0.4 if smoker == "Former" else 0.0
    x += 0.03 * years_smoked
    x += 0.6 * packs
    x += 0.7 if family == "Yes" else 0.0
    x += 0.6 if copd == "Yes" else 0.0
    x += 0.25 * len(exposures)
    x += 0.2 * len(symptoms)
    return max(0.0, min(1.0, logistic(x)))

def seeded_rng(seed_text):
    h = hashlib.sha256(seed_text.encode()).hexdigest()
    seed = int(h[:16],16)
    return random.Random(seed)

def fake_lesions(image, rng, n=1):
    img = image.convert("RGBA").resize((512,512))
    overlay = Image.new("RGBA", img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    W,H = img.size
    spots = []
    for i in range(n):
        r = rng.randint(12,70)
        x = rng.randint(r, W-r)
        y = rng.randint(r, H-r)
        # soft circle
        grad = Image.new('L', (2*r,2*r), 0)
        for rr in range(r,0,-1):
            alpha = int(200*(rr/r)**2)
            ImageDraw.Draw(grad).ellipse((r-rr,r-rr,r+rr,r+rr), fill=alpha)
        patch = Image.new('RGBA',(2*r,2*r),(108,43,217,120))
        patch.putalpha(grad)
        overlay.paste(patch,(x-r,y-r), patch)
        spots.append((x/W, y/H, r/max(W,H)))
    out = Image.alpha_composite(img, overlay)
    return out, spots

# Main action
if st.button("Analyze Patient"):
    # Risk score
    risk = compute_risk(age, smoker, years_smoked, packs_per_day, family_history, copd, exposures, symptoms)
    risk_pct = int(risk*100)

    # Tumor simulation
    seed_text = f"{age}{gender}{smoker}{years_smoked}{packs_per_day}{','.join(symptoms)}"
    rng = seeded_rng(seed_text)
    tumor_cm = round(rng.uniform(0.5, 6.0), 1)
    tumor_pct = round(min(95, (tumor_cm/30)*100), 1)  # arbitrary relative percent
    side = rng.choice(["Right", "Left"])
    position = rng.choice(["Upper lobe", "Middle lobe", "Lower lobe"])
    classification = rng.choices(["Benign", "Malignant"], weights=(40,60), k=1)[0]

    # Display analysis
    st.markdown("## Tumor Analysis")
    c1,c2 = st.columns([2,3])
    with c1:
        st.markdown(f"<div class='card'><h3>Tumor size</h3><h1 style='margin:0'>{tumor_cm} cm</h1><p class='small'>Measured maximal diameter</p></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card' style='margin-top:8px;'><h3>Relative volume</h3><h2 style='margin:0'>{tumor_pct}%</h2><p class='small'>Approximate % of lung cross-section</p></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card' style='margin-top:8px;'><h3>Location</h3><h2 style='margin:0'>{side} lung • {position}</h2></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><h3>Classification</h3><h1 style='margin:0'>{classification}</h1><p class='small'>Simulation-based output</p></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card' style='margin-top:8px;'><h3>Clinical risk score</h3><h2 style='margin:0'>{risk_pct}%</h2><p class='small'>Composite risk based on inputs</p></div>", unsafe_allow_html=True)

    # Image overlay
    st.markdown("## Image Inspection")
    if img_file is not None:
        image = Image.open(img_file)
        overlay, spots = fake_lesions(image, rng, n=1 if demo_mode else 0)
        buf = io.BytesIO()
        overlay.save(buf, format="PNG")
        st.image(overlay, caption="Overlayed image (simulated tumor highlight)", use_column_width=True)
        if spots:
            x,y,r = spots[0]
            loc = ("Upper" if y<0.33 else "Lower" if y>0.66 else "Middle")
            side_text = "Left" if x<0.5 else "Right"
            st.markdown(f"**Detected region:** {loc} • {side_text} • approx {int(r*100)}% of image width")
    else:
        st.info("No image uploaded. Upload a chest X-ray to view simulated overlay.")

    # Next steps and center referral
    st.markdown("## Recommended Next Steps")
    st.markdown("""- This simulation recommends referral to a specialized oncology center for further evaluation and management.
- Suggested center: **Baheya Cancer Center** — contact for scheduling diagnostic workup and treatment planning (surgery/chemotherapy/radiation as indicated).
""")

    st.markdown("### Patient Summary")
    st.write({
        "Age": age, "Gender": gender, "Smoking": smoker, "Years smoked": years_smoked,
        "Packs/day": packs_per_day, "Family history": family_history, "COPD": copd,
        "Exposures": exposures, "Symptoms": symptoms
    })

else:
    st.markdown("### Enter patient data in the sidebar and press **Analyze Patient** to generate the simulated tumor analysis.")

st.markdown("---")
st.markdown("<div class='small'>© 2025 LungSight Pro</div>", unsafe_allow_html=True)
