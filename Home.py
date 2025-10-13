# Home.py

# --- Initialize DB schema before anything else ---
from db_init import init_schema
try:
    init_schema()
except Exception as e:
    import streamlit as st
    st.error(f"DB init failed: {e}")

import streamlit as st

st.set_page_config(page_title="HealthVault — Personal Data Store", page_icon="🔒", layout="wide")

# ---------- CSS & Fonts (must be in <style>, must use unsafe_allow_html=True) ----------
st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">

<style>
:root{
  --brand:#0D55FF; --brand-dark:#0D2847; --chip:#F2F6FB;
}

/* Sidebar */
[data-testid="stSidebar"]{ background: var(--brand-dark); color:#fff; }
[data-testid="stSidebar"] *{ color:#fff !important; }

/* Global */
*{ font-family:'Inter', system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }

/* Hero */
.hero{ margin: 10px auto 8px auto; text-align:center; }
.logo-wrap{
  width:84px; height:84px; margin:0 auto 6px auto;
  background: radial-gradient(120px 120px at 50% 30%, #BFE0FF 0%, rgba(191,224,255,0.0) 60%),
              linear-gradient(135deg, #0EA5E9 0%, #1D4ED8 100%);
  border-radius:22px; box-shadow: 0 10px 25px rgba(13,85,255,0.25); position:relative;
}
.logo-wrap:before{ content:""; position:absolute; inset:14px; border-radius:16px; background:#0D2847; opacity:.06; }
.title{ font-weight:800; font-size:38px; color:#0EA5E9; letter-spacing:.2px; text-shadow:0 1px 0 #fff; }
.subtitle{ margin-top:2px; color:#223041; font-size:18px; font-weight:600; }

/* Pills */
.pills{ margin:14px auto 18px; display:flex; gap:10px; justify-content:center; flex-wrap:wrap; }
.pill{
  background:#EAF2FF; border:1px solid #D7E6FF; color:#2463EB;
  padding:8px 12px; border-radius:999px; font-weight:600; font-size:13px;
  display:flex; align-items:center; gap:8px;
}

/* Grid */
.grid{ max-width:980px; margin:6px auto 0; display:grid; grid-template-columns:1fr 1fr; gap:16px; }
@media (max-width:900px){ .grid{ grid-template-columns:1fr; } }

/* Cards */
.card{
  background:#fff; border:1px solid #E4ECF7; border-radius:16px; padding:20px; min-height:210px; position:relative;
  box-shadow: 0 8px 24px rgba(13,85,255,0.06);
}
.card.border-green{ border-color:#CDEEE0; box-shadow:0 8px 24px rgba(45,191,113,0.08); }
.badge-num{
  position:absolute; top:-10px; left:-10px; background:#2D68FF; color:#fff; font-weight:800; font-size:14px;
  width:34px; height:34px; border-radius:10px; display:flex; align-items:center; justify-content:center;
  box-shadow:0 8px 18px rgba(13,85,255,.25);
}
.badge-num.green{ background:#25C27A; box-shadow:0 8px 18px rgba(37,194,122,.25); }
.icon{ width:28px; height:28px; border-radius:10px; background:#EAF2FF; color:#2463EB; display:inline-flex; align-items:center; justify-content:center; margin-right:10px; }
.icon.green{ background:#E8FAF1; color:#1E9F63; }
.card h3{ margin:0 0 8px 0; font-size:18px; color:#132339; }
.card p{ color:#415268; font-size:14px; line-height:1.55; }

/* CTA */
.cta-bar{
  max-width:520px; margin:26px auto 12px; background:linear-gradient(90deg, #0D55FF, #18C08D);
  border-radius:12px; padding:8px; text-align:center; box-shadow:0 16px 30px rgba(13,85,255,.25);
}
.halo{ width:100%; max-width:760px; margin:0 auto; height:80px;
       background:radial-gradient(220px 60px at 50% 0%, rgba(13,85,255,.18), transparent 70%); filter: blur(16px); }

/* Chips & footer */
.chips{ display:flex; flex-wrap:wrap; gap:10px; justify-content:center; margin:14px auto 8px;}
.chip{ background:var(--chip); border:1px solid #E5EEF7; color:#26405A; padding:8px 12px; border-radius:999px; font-weight:600; font-size:12px; }
.footer{ text-align:center; color:#6C7C90; font-size:12px; margin:12px 0 6px; }
</style>
    """,
    unsafe_allow_html=True
)

# ---------- HERO ----------
st.markdown(
    """
<div class="hero">
  <div class="logo-wrap"></div>
  <div class="title">HealthVault</div>
  <div class="subtitle">Your Health Data, Your Control</div>

  <div class="pills">
    <div class="pill">🔒 Secure</div>
    <div class="pill">🪪 Transparent</div>
    <div class="pill">🧮 Rewarding</div>
  </div>
</div>
""",
    unsafe_allow_html=True
)

# ---------- GRID 2×2 ----------
st.markdown('<div class="grid">', unsafe_allow_html=True)

st.markdown(
    """
    <div class="card">
      <div class="badge-num">1</div>
      <div style="display:flex;align-items:center;"><div class="icon">🏷️</div><h3>Business Case</h3></div>
      <p>People lose control of their health data. HealthVault lets you securely store, manage, and share your data — and earn rewards when authorised organisations access it.</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="card border-green">
      <div class="badge-num green">2</div>
      <div style="display:flex;align-items:center;"><div class="icon green">🧠</div><h3>Why It’s Innovative</h3></div>
      <p>End-to-end encryption, consent-driven sharing, smart rewards, and transparency compliant with NZ Privacy Act 2020 & GDPR.</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="card">
      <div class="badge-num">3</div>
      <div style="display:flex;align-items:center;"><div class="icon">🔐</div><h3>Why It’s Better</h3></div>
      <p>You own your data. Every access is logged and auditable. Encrypted SQLite storage ensures full security.</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="card border-green">
      <div class="badge-num green">4</div>
      <div style="display:flex;align-items:center;"><div class="icon green">👥</div><h3>Why People Will Use It</h3></div>
      <p>Patients gain privacy; researchers get ethical data; and providers simplify compliance — building a trusted health-data ecosystem.</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('</div>', unsafe_allow_html=True)

# ---------- CTA ----------
st.markdown('<div class="cta-bar">', unsafe_allow_html=True)
mid = st.columns([1,3,1])[1]
with mid:
    if st.button("Empower your health data. Empower yourself.", use_container_width=True):
        st.switch_page("pages/0_Login.py")
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="halo"></div>', unsafe_allow_html=True)

# ---------- Footer chips & team ----------
st.markdown(
    """
<div class="chips">
  <div class="chip">🛡️ Privacy First</div>
  <div class="chip">🏥 Health-Focused</div>
  <div class="chip">🧾 Data Ownership</div>
  <div class="chip">⚡ Real-Time Control</div>
</div>
<div class="footer">Team 15 – Members-Only | Vpat766 · Hpat227 · Hson126 · Kpra201</div>
""",
    unsafe_allow_html=True
)
