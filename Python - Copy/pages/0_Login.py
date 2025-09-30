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
st.title("🔐 Personal Data Store — Login / Sign Up")

# ------- helpers ----------------------------------------------------
def _mk_user(first_name: str, last_name: str, dob_iso: str, email: str, password: str):
    try:
        return create_user(first_name, last_name, dob_iso, email, password, "user", True)
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

# ------- already logged in -----------------------------------------
if st.session_state.get("uid"):
    st.success(f"Logged in as **{st.session_state.get('name','')}** ({st.session_state.get('role','')})")
    if st.button("Log out", key="logout_btn"):
        for k in ("uid", "email", "name", "role", "verified"):
            st.session_state.pop(k, None)
        st.rerun()
    st.caption("Use the sidebar to navigate to Upload, Permissions, and Logs.")
    st.divider()

# ------- tabs -------------------------------------------------------
tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

# ------- Log In -----------------------------------------------------
with tab_login:
    st.subheader("Log in to your account")
    email_in = st.text_input("Email", key="login_email")
    pw_in = st.text_input("Password", type="password", key="login_pw")

    colA, colB = st.columns([1, 4])
    with colA:
        if st.button("Log In", key="login_btn", use_container_width=True):
            if not email_in or not pw_in:
                st.error("Please enter email and password.")
            elif not valid_email(email_in):
                st.error("Invalid email format.")
            else:
                try:
                    user = authenticate(email_in.strip(), pw_in)
                    if not user:
                        st.error("Invalid email or password.")
                    else:
                        st.session_state["uid"] = user["id"]
                        st.session_state["email"] = user["email"]
                        st.session_state["name"] = user.get("name") or ""
                        st.session_state["role"] = user.get("role") or "user"
                        st.session_state["verified"] = user.get("verified", 0)
                        st.success("Logged in.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")
    with colB:
        st.caption("Forgot password? (Not implemented in prototype)")

# ------- Sign Up ----------------------------------------------------
with tab_signup:
    st.subheader("Create an account")

    role_choice = st.radio(
        "Account type",
        options=["user", "org"],
        index=0,
        horizontal=True,
        key="signup_role",
        help="Choose 'org' if you're an organisation that will request access to user data.",
    )

    if role_choice == "user":
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("First name", key="su_user_first")
        with c2:
            last_name  = st.text_input("Last name",  key="su_user_last")

        dob = st.date_input("Date of birth", format="YYYY-MM-DD", key="su_user_dob")
        email_new = st.text_input("Email", key="su_user_email")
        pw_new    = st.text_input("Create password (min 8 chars, letters & numbers)",
                                  type="password", key="su_user_pw")

        if st.button("Sign Up", key="su_user_btn", use_container_width=True):
            if not (first_name and last_name and isinstance(dob, date) and email_new and pw_new):
                st.error("Please enter your first and last name, DOB, email, and password.")
            elif not valid_email(email_new):
                st.error("Invalid email format.")
            else:
                ok_pw, msg_pw = valid_password(pw_new)
                if not ok_pw:
                    st.error(msg_pw)
                else:
                    try:
                        ok, msg = _mk_user(first_name.strip(), last_name.strip(),
                                           dob.isoformat(), email_new.strip(), pw_new)
                        if ok:
                            st.success("Account created successfully. Please log in.")
                        else:
                            st.error(msg or "Sign up failed.")
                    except Exception as e:
                        st.error(f"Sign up failed: {e}")

    else:  # ORG
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

        if st.button("Create Org Account", key="su_org_btn", use_container_width=True):
            if not (org_name and isinstance(dob_org, date) and org_email and org_pw):
                st.error("Please provide organisation name, a date, email, and password.")
            elif not valid_email(org_email):
                st.error("Invalid email format.")
            else:
                ok_pw, msg_pw = valid_password(org_pw)
                if not ok_pw:
                    st.error(msg_pw)
                else:
                    try:
                        ok, msg = _mk_org(org_name.strip(), org_email.strip(), org_pw,
                                          (contact_first or "").strip() or None,
                                          (contact_last  or "").strip() or None,
                                          dob_org.isoformat())
                        if ok:
                            st.success("Organisation account created. Please log in.")
                        else:
                            st.error(msg or "Sign up failed.")
                    except Exception as e:
                        st.error(f"Sign up failed: {e}")

st.caption(
    "Tip: Use a **user** account to upload data. Use an **org** account to request access. "
    "Pages like *Request Access* are visible to orgs only."
)
