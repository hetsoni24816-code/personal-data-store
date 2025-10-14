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

# ---------- CSS & Fonts ----------
st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">

<style>
:root{
  --brand:#0D55FF; --brand-dark:#0D2847; --chip:#F2F6FB; --ink:#0F1F2E;
}

/* Sidebar */
[data-testid="stSidebar"]{ background: var(--brand-dark); color:#fff; }
[data-testid="stSidebar"] *{ color:#fff !important; }

/* Global */
*{ font-family:'Inter', system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }

/* Hero */
.hero{ margin: 10px auto 8px auto; text-align:center; }
.logo-wrap{
  width:84px; height:84px; margin:0 auto 10px auto;
  background: radial-gradient(120px 120px at 50% 30%, #BFE0FF 0%, rgba(191,224,255,0.0) 60%),
              linear-gradient(135deg, #0EA5E9 0%, #1D4ED8 100%);
  border-radius:22px; box-shadow: 0 10px 25px rgba(13,85,255,0.25); position:relative;
}
.logo-wrap:before{ content:""; position:absolute; inset:14px; border-radius:16px; background:#0D2847; opacity:.06; }

/* Title & Slogan */
.title{ font-weight:800; font-size:40px; color:var(--ink); letter-spacing:.2px; }
.slogan{
  display:inline-block; margin-top:8px;
  padding:10px 14px; font-weight:700; font-size:16px; color:var(--ink);
  background:linear-gradient(0deg,#FFFFFF 0%,#F6FAFF 100%);
  border:1px solid #E0E8F5; border-radius:14px;
  box-shadow:0 8px 18px rgba(13,85,255,.06);
}

/* Subtitle */
.subtitle{ margin-top:10px; color:#223041; font-size:16px; font-weight:600; }

/* Pills */
.pills{ margin:14px auto 18px; display:flex; gap:10px; justify-content:center; flex-wrap:wrap; }
.pill{
  background:#EAF2FF; border:1px solid #D7E6FF; color:#2463EB;
  padding:8px 12px; border-radius:999px; font-weight:600; font-size:13px;
  display:flex; align-items:center; gap:8px;
}

/* Grid */
.grid{ max-width:980px; margin:12px auto 0; display:grid; grid-template-columns:1fr 1fr; gap:16px; }
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
  max-width:560px; margin:26px auto 12px; background:linear-gradient(90deg, #0D55FF, #18C08D);
  border-radius:12px; padding:8px; text-align:center; box-shadow:0 16px 30px rgba(13,85,255,.25);
}
.halo{ width:100%; max-width:760px; margin:0 auto; height:80px;
       background:radial-gradient(220px 60px at 50% 0%, rgba(13,85,255,.18), transparent 70%); filter: blur(16px); }

/* Chips & footer */
.chips{ display:flex; flex-wrap:wrap; gap:10px; justify-content:center; margin:14px auto 8px;}
.chip{ background:var(--chip); border:1px solid #E5EEF7; color:#26405A; padding:8px 12px; border-radius:999px; font-weight:600; font-size:12px; }
.footer{ text-align:center; color:#6C7C90; font-size:12px; margin:12px 0 6px; }

/* Small helper text */
.muted{ color:#5B6B7D; font-size:12px; margin-top:8px; }
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

  <div class="slogan">Your Health Data. Your Control. Your Benefit.</div>
  <div class="subtitle">Store securely · Share with consent · Earn as it is used</div>

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

# Card 1 - Blue
st.markdown(
    """
    <div class="card">
      <div class="badge-num">1</div>
      <div style="display:flex;align-items:center;"><div class="icon">🏷️</div><h3>How HealthVault Works</h3></div>
      <p>Upload and manage your personal health data in a private, encrypted environment. Files are stored securely so that only you can access them unless you grant permission. Your data is held in encrypted SQLite which protects your information even when the app is offline.</p>
      <p class="muted">You are always in control with clear visibility settings for each dataset.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Card 2 - Green
st.markdown(
    """
    <div class="card border-green">
      <div class="badge-num green">2</div>
      <div style="display:flex;align-items:center;"><div class="icon green">🧠</div><h3>Trusted Access</h3></div>
      <p>Mark a dataset as Trusted to allow verified organisations and researchers to request access. You review and approve each request before any download occurs. After approval, the organisation can securely retrieve your dataset.</p>
      <p class="muted">Every download from a different verified organisation rewards you with 1 point valued at $0.10.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Card 3 - Blue
st.markdown(
    """
    <div class="card">
      <div class="badge-num">3</div>
      <div style="display:flex;align-items:center;"><div class="icon">🔐</div><h3>Public Data Sharing</h3></div>
      <p>Mark a dataset as Public to let both users and organisations view and download anonymised information for research and innovation. Public visibility helps your data contribute to community insights and healthcare improvements.</p>
      <p class="muted">You can switch visibility back to Private or Trusted at any time.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Card 4 - Green
st.markdown(
    """
    <div class="card border-green">
      <div class="badge-num green">4</div>
      <div style="display:flex;align-items:center;"><div class="icon green">👥</div><h3>Privacy and Compliance</h3></div>
      <p>HealthVault follows strict data protection standards aligned with the New Zealand Privacy Act 2020 and the General Data Protection Regulation. Access requests, approvals, and downloads are logged to provide full transparency.</p>
      <p class="muted">Consent driven access protects your rights while enabling secure collaboration.</p>
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
        try:
            st.switch_page("pages/0_Login.py")
        except Exception:
            st.toast("Go to: pages/0_Login.py")
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
<div class="footer">Team 7 – Members-Only | Vpat766 · Hpat227 · Hson126 · Kpra201</div>
""",
    unsafe_allow_html=True
)
