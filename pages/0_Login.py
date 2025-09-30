# pages/0_Login.py
# Login / Sign Up with user/org roles (positional create_user)

import sys, pathlib, time
from datetime import date
import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from auth import authenticate, create_user
from security import valid_email, valid_password

NOW = lambda: time.strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(page_title="Login / Sign Up", page_icon="🔐", layout="wide")
st.title("Personal Data Store — Login / Sign Up")

# ---------- CSS: rounded cards with title outside ----------
st.markdown("""
<style>
[data-testid="stSidebar"] {
            background-color: #0D2847; /* dark blue */
            color: white;
        }
        [data-testid="stSidebar"] * {
            color: white !important;
        }
.card-wrap { position: relative; margin-top: 1.25rem; }
.card-title {
  position: absolute;
  top: -12px;
  left: 16px;
  padding: 2px 10px;
  border-radius: 9999px;
  font-weight: 600;
  background: var(--background-color);
  border: 1px solid var(--secondary-background-color);
  line-height: 1.6;
}
.card-container {
  border: 1px solid var(--secondary-background-color);
  border-radius: 16px;
  padding: 18px;
  background: var(--background-color);
  box-shadow: 0 1px 2px rgba(0,0,0,.04);
}
</style>
""", unsafe_allow_html=True)

# ---------------- helpers ----------------
def _norm_email(e: str) -> str:
    return (e or "").strip().lower()

def _mk_user(first_name: str, last_name: str, dob_iso: str, email: str, password: str):
    """Gracefully handle older create_user signatures (no DOB)."""
    try:
        return create_user(first_name, last_name, dob_iso, email, password, "user", True)  # verified=True for prototype
    except TypeError:
        return create_user(first_name, last_name, "1900-01-01", email, password, "user", True)

def _mk_org(org_name: str, email: str, password: str,
            contact_first: str | None, contact_last: str | None, dob_iso: str):
    first = (contact_first or "").strip() or org_name
    last  = (contact_last  or "").strip() or "Org"
    try:
        return create_user(first, last, dob_iso, email, password, "org", True)
    except TypeError:
        return create_user(first, last, "1900-01-01", email, password, "org", True)

def _display_name(user: dict) -> str:
    fn, ln = user.get("first_name", ""), user.get("last_name", "")
    if fn or ln:
        return " ".join([fn, ln]).strip()
    if user.get("name"):
        return str(user.get("name"))
    return (user.get("email", "") or "").split("@")[0]

# ---------------- already logged in ----------------
if st.session_state.get("uid"):
    st.success(f"Logged in as **{st.session_state.get('name','')}** ({st.session_state.get('role','')})")
    if st.button("Log out", key="logout_btn"):
        for k in ("uid", "email", "name", "role", "verified"):
            st.session_state.pop(k, None)
        st.rerun()
    st.divider()

# ---------------- tabs ----------------
tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

# ---------------- Log In ----------------
with tab_login:
    
    st.markdown('<div class="card-container">', unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        email_in = st.text_input("Email", key="login_email")
        pw_in = st.text_input("Password", type="password", key="login_pw")
        submitted = st.form_submit_button("Log In", use_container_width=True)

    if submitted:
        if not email_in or not pw_in:
            st.error("Please enter email and password.")
        else:
            email_norm = _norm_email(email_in)
            if not valid_email(email_norm):
                st.error("Invalid email format.")
            else:
                try:
                    user = authenticate(email_norm, pw_in)
                    if not user:
                        st.error("Invalid email or password.")
                    else:
                        st.session_state["uid"] = user["id"]
                        st.session_state["email"] = user["email"]
                        st.session_state["role"] = user.get("role") or "user"
                        st.session_state["verified"] = user.get("verified", 0)
                        st.session_state["name"] = _display_name(user)
                        st.success("Logged in.")
                        st.rerun()
                except Exception:
                    st.error("Login failed. Please try again.")

    st.markdown('</div></div>', unsafe_allow_html=True)

# ---------------- Sign Up ----------------
with tab_signup:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)

    role_choice = st.radio(
        "Account type",
        options=["user", "org"],
        index=0,
        horizontal=True,
        key="signup_role",
        help="Choose 'org' if you're an organisation that will request access to user data.",
    )

    if role_choice == "user":
        with st.form("signup_user_form"):
            c1, c2 = st.columns(2)
            with c1:
                first_name = st.text_input("First name", key="su_user_first")
            with c2:
                last_name  = st.text_input("Last name",  key="su_user_last")

            dob = st.date_input("Date of birth", format="YYYY-MM-DD", key="su_user_dob")
            email_new = st.text_input("Email", key="su_user_email")
            pw_new    = st.text_input("Create password (min 8 chars, letters & numbers)",
                                      type="password", key="su_user_pw")

            submit_user = st.form_submit_button("Sign Up", use_container_width=True)

        if submit_user:
            email_norm = _norm_email(email_new)
            if not (first_name and last_name and isinstance(dob, date) and email_norm and pw_new):
                st.error("Please enter your first and last name, DOB, email, and password.")
            elif dob > date.today():
                st.error("Date of birth cannot be in the future.")
            elif not valid_email(email_norm):
                st.error("Invalid email format.")
            else:
                ok_pw, msg_pw = valid_password(pw_new)
                if not ok_pw:
                    st.error(msg_pw)
                else:
                    try:
                        ok, msg = _mk_user(first_name.strip(), last_name.strip(),
                                           dob.isoformat(), email_norm, pw_new)
                        if ok:
                            st.success("Account created successfully. Please log in.")
                        else:
                            st.error(msg or "Sign up failed.")
                    except Exception:
                        st.error("Sign up failed. Please try again.")

    else:  # org
        with st.form("signup_org_form"):
            org_name = st.text_input("Organisation name", key="su_org_name")
            oc1, oc2 = st.columns(2)
            with oc1:
                contact_first = st.text_input("Contact first name (optional)", key="su_org_contact_first")
            with oc2:
                contact_last  = st.text_input("Contact last name (optional)",  key="su_org_contact_last")

            dob_org = st.date_input("Founding date or any date (required)",
                                    value=date(2000, 1, 1), format="YYYY-MM-DD", key="su_org_dob")
            org_email = st.text_input("Org email", key="su_org_email")
            org_pw    = st.text_input("Create password (min 8 chars, letters & numbers)",
                                      type="password", key="su_org_pw")

            submit_org = st.form_submit_button("Create Org Account", use_container_width=True)

        if submit_org:
            org_email_norm = _norm_email(org_email)
            if not (org_name and isinstance(dob_org, date) and org_email_norm and org_pw):
                st.error("Please provide organisation name, a date, email, and password.")
            elif dob_org > date.today():
                st.error("The date cannot be in the future.")
            elif not valid_email(org_email_norm):
                st.error("Invalid email format.")
            else:
                ok_pw, msg_pw = valid_password(org_pw)
                if not ok_pw:
                    st.error(msg_pw)
                else:
                    try:
                        ok, msg = _mk_org(org_name.strip(), org_email_norm, org_pw,
                                          (contact_first or "").strip() or None,
                                          (contact_last  or "").strip() or None,
                                          dob_org.isoformat())
                        if ok:
                            st.success("Organisation account created. Please log in.")
                        else:
                            st.error(msg or "Sign up failed.")
                    except Exception:
                        st.error("Sign up failed. Please try again.")

    st.markdown('</div></div>', unsafe_allow_html=True)
