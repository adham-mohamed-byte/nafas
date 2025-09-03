
# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import io, hashlib, math, random, textwrap

st.set_page_config(page_title="Lung Insight (Demo)",
                   page_icon="🫁",
                   layout="wide",
                   initial_sidebar_state="expanded")

# ---- Custom purple theme ----
PRIMARY = "#6C2BD9"  # violet-700
BG = "#0B021B"       # near-black purple
CARD = "#140B2B"
TEXT = "#F5F3FF"

st.markdown(f"""
    <style>
    .stApp {{
        background: radial-gradient(60% 80% at 20% 10%, #1E0B45 0%, #0B021B 60%);
        color: {TEXT};
    }}
    .stButton>button {{
        background: {PRIMARY} !important;
        color: white !important;
        border-radius: 16px;
        padding: 0.6rem 1rem;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 6px 20px rgba(108,43,217,0.25);
    }}
    .css-1y4p8pa, .css-10trblm, .stMarkdown, .stText, .stSubheader, h1,h2,h3,h4,h5,h6, p, span {{
        color: {TEXT} !important;
    }}
    .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
    }}
    .glass {{
        background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 18px;
        padding: 1rem 1.2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.35);
    }}
    .metric-card {{
        background: linear-gradient(180deg, rgba(108,43,217,0.10), rgba(108,43,217,0.03));
        border: 1px solid rgba(108,43,217,0.15);
        border-radius: 18px;
        padding: 1rem 1.2rem;
    }}
    .small {{
        opacity: 0.85;
        font-size: 0.9rem;
    }}
    .disclaimer {{
        background: rgba(255,255,255,0.06);
        border-left: 4px solid {PRIMARY};
        padding: .75rem 1rem;
        border-radius: 12px;
        margin-top: .5rem;
        font-size: 0.92rem;
    }}
    </style>
""", unsafe_allow_html=True)

# ---- Header ----
col1, col2 = st.columns([1,2])
with col1:
    st.markdown("### 🫁 **Lung Insight – Demo (Educational)**")
    st.markdown("#### نموذج تجريبي للتنبؤ بالمخاطر وتحليل الصور (غير تشخيصي)")
with col2:
    st.markdown("""
    <div class="disclaimer">
    <b>تنبيه مهم:</b> هذا التطبيق لأغراض تعليمية وتجريبية فقط، ولا يقدم تشخيصًا طبيًا ولا يستبدل الطبيب. 
    لا تعتمد على نتائجه لاتخاذ قرارات صحية. إذا كانت لديك أعراض مقلقة، راجع مختصًا.
    </div>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ⚙️ الإعدادات")
    st.write("املأ العوامل المختلفة لتقدير مخاطر سرطان الرئة (تجريبي).")

    age = st.slider("العمر", 18, 90, 45)
    sex = st.selectbox("النوع", ["ذكر", "أنثى"])
    smoker = st.selectbox("هل تدخن حاليًا؟", ["لا", "نعم"])
    years_smoked = st.slider("سنوات التدخين", 0, 60, 5)
    packs_per_day = st.slider("عدد علب السجائر/اليوم", 0.0, 3.0, 0.5, 0.1)
    family = st.selectbox("تاريخ عائلي لسرطان الرئة", ["لا", "نعم"])
    copd = st.selectbox("COPD/انسداد رئوي مزمن", ["لا", "نعم"])
    exposure = st.multiselect("تعرض مهني/بيئي", ["الأسبستوس", "الرادون", "عادم الديزل", "أخرى"])
    symptoms = st.multiselect("أعراض", ["سعال مزمن", "بلغم مدمم", "ضيق تنفس", "فقدان وزن"])

    st.markdown("---")
    st.markdown("### 🖼️ صورة الأشعة (اختياري)")
    img_file = st.file_uploader("ارفع صورة أشعة صدر (PNG/JPG)—للشرح التجريبي فقط", type=["png","jpg","jpeg"])
    demo_mode = st.checkbox("تفعيل وضع العرض/العينات", value=True, help="يُولّد مناطق اشتباه وهمية للشرح.")

    st.markdown("---")
    analyze = st.button("🚀 احسب المخاطر وحلل الصورة")

def logistic(x):
    return 1/(1+math.exp(-x))

def risk_model(age, sex, smoker, years_smoked, packs_per_day, family, copd, exposure, symptoms):
    # لعبة أوزان بسيطة لتجربة الواجهة فقط
    x = -5.0
    x += 0.035 * age
    x += 0.6 if sex == "ذكر" else 0.4
    x += 0.9 if smoker == "نعم" else 0.0
    x += 0.02 * years_smoked
    x += 0.5 * packs_per_day
    x += 0.6 if family == "نعم" else 0.0
    x += 0.7 if copd == "نعم" else 0.0
    x += 0.3 * len(exposure)
    x += 0.25 * len(symptoms)
    p = logistic(x)
    return max(0.0, min(1.0, p))

def seeded_random(seed_text):
    h = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    seed = int(h[:16], 16)
    rng = random.Random(seed)
    return rng

def fake_lesion_overlay(image: Image.Image, rng: random.Random, n=2):
    img = image.convert("RGBA").resize((512,512))
    overlay = Image.new("RGBA", img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    W, H = img.size
    spots = []
    for i in range(n):
        r = rng.randint(18, 60)
        x = rng.randint(r, W-r)
        y = rng.randint(r, H-r)
        # draw soft circle
        grad = Image.new('L', (2*r, 2*r), 0)
        for rr in range(r, 0, -1):
            alpha = int(255 * (rr/r) ** 2)
            ImageDraw.Draw(grad).ellipse((r-rr, r-rr, r+rr, r+rr), fill=alpha)
        color = (108, 43, 217, 90)  # violet
        patch = Image.new('RGBA', (2*r, 2*r), color)
        patch.putalpha(grad)
        overlay.paste(patch, (x-r, y-r), patch)
        spots.append((x/W, y/H, r/max(W,H)))
    out = Image.alpha_composite(img, overlay)
    return out, spots

def spots_to_text(spots):
    lines = []
    for i,(nx, ny, nr) in enumerate(spots, start=1):
        loc = []
        loc.append("علوي" if ny < 0.33 else "سفلي" if ny > 0.66 else "وسطي")
        loc.append("أيمن" if nx < 0.5 else "أيسر")
        size_pct = int(nr*100)
        lines.append(f"منطقة اشتباه #{i}: ({', '.join(loc)}), الحجم التقريبي ~ {size_pct}% من عرض الصورة.")
    return "\n".join(lines) if lines else "لا توجد مناطق اشتباه معروضة."

if analyze:
    # --- Risk ---
    prob = risk_model(age, sex, smoker, years_smoked, packs_per_day, family, copd, exposure, symptoms)
    percent = int(prob*100)

    st.markdown("## 📈 نتيجة تقدير المخاطر (تجريبي)")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="metric-card"><h3>نسبة الخطورة المتوقعة</h3>
        <h1 style="margin:0;font-size:3rem">{percent}%</h1>
        <p class="small">احتمالية تقريبية مبنية على مدخلاتك (غير طبية)</p></div>""", unsafe_allow_html=True)
    with c2:
        packs = years_smoked * packs_per_day
        st.markdown(f"""<div class="metric-card"><h3>التعرّض التراكمي (تقريبي)</h3>
        <h1 style="margin:0;font-size:2.3rem">{packs:.1f}</h1>
        <p class="small">Pack-Years (حساب بدائي)</p></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card"><h3>عوامل مترافقة</h3>
        <h1 style="margin:0;font-size:2.3rem">{len(exposure)+len(symptoms)}</h1>
        <p class="small">عدد العوامل/الأعراض المحددة</p></div>""", unsafe_allow_html=True)

    # --- Image analysis (demo) ---
    st.markdown("## 🔎 تحليل صورة الأشعة (عرض تجريبي)")
    if img_file is not None:
        image = Image.open(img_file)
        seed_txt = (str(image.size)+image.mode+str(percent)) if demo_mode else "no-demo"
        rng = seeded_random(seed_txt)
        overlay, spots = fake_lesion_overlay(image, rng, n=2 if demo_mode else 0)
        buf = io.BytesIO()
        overlay.save(buf, format="PNG")
        st.image(overlay, caption="عرض توضيحي لمناطق اشتباه (ليست حقيقية)", use_column_width=True)
        st.markdown("#### تفاصيل المناطق (تجريبي):")
        st.code(spots_to_text(spots))
        if demo_mode and spots:
            # "severity" as percent of combined spot sizes (toy)
            severity = int(min(95, sum(int(s[2]*100) for s in spots) + rng.randint(3,12)))
            st.markdown(f"**نسبة تقديرية لشدة الاشتباه في الصورة: ~ {severity}% (توضيحي فقط)**")
    else:
        st.info("يمكنك رفع صورة أشعة صدر بصيغة PNG/JPG لرؤية تراكب ملون يوضح مناطق اشتباه *وهمية* للعرض.")

    # --- Educational content ---
    st.markdown("## 📚 معلومات مختصرة عن الرئة (للتوعية)")
    st.markdown("""
    - الرئتان مسؤولتان عن تبادل الغازات (الأكسجين وثاني أكسيد الكربون).
    - من عوامل خطورة سرطان الرئة: التدخين، التعرّض للرادون/الأسبستوس، التاريخ العائلي، ومرض الانسداد الرئوي.
    - الأعراض المقلقة قد تشمل: سعال لا يتحسن، نفث دم، ألم صدري، فقدان وزن غير مبرر.
    - الوقاية الأفضل: الإقلاع عن التدخين، التهوية الجيدة، وفحوصات دورية للفئات عالية الخطورة.
    """)

    # --- Neutral guidance ---
    st.markdown("### 🤝 ماذا تفعل تاليًا؟")
    st.markdown("""
    - احتفظ بهذه النتائج التعليمية للمتابعة الذاتية فقط.
    - إذا كانت لديك أعراض أو قلق، اطلب تقييمًا سريريًا من مختص.
    - نماذج الذكاء الاصطناعي الطبية يجب أن تُعتمد من الجهات التنظيمية قبل الاستعمال السريري.
    """)

else:
    st.markdown("""
    ### ✨ ابدأ التجربة
    اضبط المدخلات في الشريط الجانبي ثم اضغط **"احسب المخاطر وحلل الصورة"**.
    يمكن تفعيل **وضع العرض** لإظهار مناطق اشتباه *وهمية* على الصورة لتوضيح الفكرة.
    """)

# Footer
st.markdown("---")
st.markdown('<div class="small">© 2025 Lung Insight (Demo). Educational use only.</div>', unsafe_allow_html=True)
