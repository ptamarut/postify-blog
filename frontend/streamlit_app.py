import os
from io import BytesIO
from datetime import datetime

import requests
import streamlit as st
from PIL import Image

API = os.getenv("API_URL", "http://127.0.0.1:8000")
DEFAULT_MAX_SIDE = int(os.getenv("MAX_IMAGE_SIDE", "1200"))

st.set_page_config(page_title="✍️ Postify", layout="wide")

#Global style
st.markdown("""
<style>
/* Sidebar as full-height flex so we can stick login at bottom */
section[data-testid="stSidebar"] > div {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.sb-bottom { margin-top: auto; }
.hero {height: 42vh;background-image:url('https://images.unsplash.com/photo-1515378791036-0648a3ef77b2');background-size:cover;background-position:center;border-radius:12px;display:flex;align-items:center;justify-content:center;margin-bottom:10px;}
.overlay {position:absolute;inset:0;background:rgba(0,0,0,.55);border-radius:12px;}
.hero-wrap {position:relative;width:100%;}
.hero-text {position:relative;color:#fff;text-align:center;z-index:2;padding:0 16px;}
.hero-text h1 {font-size:3em;margin-bottom:.2em;}
.hero-text p {font-size:1.2em;margin:0;}
</style>
""", unsafe_allow_html=True)

# Naslov
st.markdown("""
<div class="hero-wrap">
  <div class="hero">
    <div class="overlay"></div>
    <div class="hero-text">
      <h1>✍️ Postify</h1>
      <p>Piši. Objavi. Uredi. Obriši.</p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

#Constants & Session
CATEGORIES = ["Politika", "Zdravlje i ljepota", "Zabava", "Sport", "Tehnologija"]
defaults = {
    "form_title": "",
    "form_content": "",
    "form_category": CATEGORIES[0],
    "form_img_max_side": DEFAULT_MAX_SIDE,
    "upload_key": 0,
    "token": None,
    "username": None,
    "show_login": False,  # controls bottom login form visibility
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# Helpers
def _resize_image_if_needed(file, max_side):
    """Resize client-side to reduce upload size; return tuple (filename, fileobj, mime)."""
    if not file:
        return None
    img = Image.open(file)
    fmt = (img.format or "PNG").upper()
    if max(img.size) > max_side:
        img.thumbnail((max_side, max_side))
    out = BytesIO()
    if fmt in ["JPEG", "JPG"]:
        img.save(out, format="JPEG", quality=85, optimize=True)
        mime, ext = "image/jpeg", "jpg"
    else:
        img.save(out, format="PNG", optimize=True)
        mime, ext = "image/png", "png"
    out.seek(0)
    base = (getattr(file, "name", None) or f"upload.{ext}").rsplit(".", 1)[0]
    return (f"{base}_max{max_side}.{ext}", out, mime)

def reset_form():
    st.session_state.form_title = ""
    st.session_state.form_content = ""
    st.session_state.form_category = CATEGORIES[0]
    st.session_state.form_img_max_side = DEFAULT_MAX_SIDE
    st.session_state.upload_key += 1

def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}

#SIDEBAR
with st.sidebar:
    #Provjera jel backend spojen
    # try:
    #     r = requests.get(f"{API}/health", timeout=5)
    #     ok = (r.ok and r.json().get("status") == "ok")
    #     st.success("✅ Backend spojen" if ok else "⚠️ Backend se ne može dohvatiti")
    # except Exception as e:
    #     st.error(f"⚠️ Backend nije pokrenut ({e})")
    # st.divider()

    # Filter
    st.header("🔎 Filtriranje postova")
    selected_cat = st.selectbox("Kategorija", ["Sve"] + CATEGORIES, key="sb_cat")
    title_filter = st.text_input("Pretraži po naslovu", key="sb_title")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        do_filter = st.button("Traži", use_container_width=True)
    with col_f2:
        if st.button("Reset", use_container_width=True):
            st.session_state.sb_cat = "Sve"
            st.session_state.sb_title = ""
            st.rerun()

    if do_filter:
        params = {}
        if selected_cat != "Sve":
            params["category"] = selected_cat
        if title_filter:
            params["title"] = title_filter
        try:
            r = requests.get(f"{API}/filter/", params=params, timeout=20)
            r.raise_for_status()
            results = r.json()
            st.subheader("Rezultati")
            if not results:
                st.info("Nema postova za zadane filtere.")
            else:
                for p in results:
                    st.markdown(f"**{p['title']}**  \n_{p['category']}_")
                    if p.get("image_url"):
                        st.image(API.rstrip('/') + p["image_url"], width=150)
                    st.write(p["content"][:200] + ("…" if len(p["content"]) > 200 else ""))
                    st.markdown("---")
        except Exception as e:
            st.error(f"Greška: {e}")

    st.divider()

    st.header("🧠 Semantičko pretraživanje")
    sem_query = st.text_input("Upit", key="semantic_query")
    sem_k = st.slider("Broj rezultata", 1, 10, 5, key="semantic_k")
    if st.button("Traži semantički", use_container_width=True):
        if not sem_query.strip():
            st.warning("Upiši upit.")
        else:
            with st.spinner("Traži..."):
                try:
                    r = requests.get(f"{API}/search/", params={"q": sem_query, "k": sem_k}, timeout=30)
                    r.raise_for_status()
                    hits = r.json()
                    if not hits:
                        st.info("Nema rezultata.")
                    else:
                        for h in hits:
                            st.markdown(f"### {h['title']}")
                            st.write(h["content"])
                            st.caption(f"Kategorija: {h.get('category','')} • score: {h.get('score',0):.4f}")
                            if h.get("image_url"):
                                st.image(API.rstrip('/') + h["image_url"], width=300)
                            st.markdown("---")
                except Exception as e:
                    st.error(f"Greška pri pretraživanju: {e}")

    #LOGIN bottom
    st.markdown('<div class="sb-bottom">', unsafe_allow_html=True)
    st.write("")  # spacer

    if not st.session_state.token:
        st.info("Prijavite se kao admin da biste objavljivali, uređivali i brisali postove.")

    if st.session_state.token:
        st.success(f"Prijavljen: {st.session_state.username}")
        col_out1, col_out2 = st.columns(2)
        with col_out1:
            if st.button("Odjava", use_container_width=True, key="btn_logout"):
                st.session_state.token = None
                st.session_state.username = None
                st.session_state.show_login = False
                st.rerun()
        with col_out2:
            if st.button("Sakrij", use_container_width=True, key="btn_hide_logged"):
                st.session_state.show_login = False
                st.rerun()
    else:
        # Toggle button
        if not st.session_state.show_login:
            if st.button("🔐 Prijava", use_container_width=True, key="btn_show_login"):
                st.session_state.show_login = True
                st.rerun()
        else:
            # Login form
            with st.form("login_form_sidebar", border=True):
                u = st.text_input("Korisničko ime", key="login_u")
                p = st.text_input("Lozinka", type="password", key="login_p")
                c1, c2 = st.columns(2)
                submit = c1.form_submit_button("Prijavi se", use_container_width=True)
                cancel = c2.form_submit_button("Zatvori", use_container_width=True)

            if cancel:
                st.session_state.show_login = False
                st.rerun()

            if submit:
                try:
                    r = requests.post(f"{API}/auth/login", data={"username": u, "password": p}, timeout=15)
                    r.raise_for_status()
                    tok = r.json().get("access_token")
                    if not tok:
                        st.error("Neispravan odgovor poslužitelja.")
                    else:
                        me = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {tok}"}, timeout=15)
                        me.raise_for_status()
                        st.session_state.token = tok
                        st.session_state.username = me.json().get("username", u)
                        st.session_state.show_login = False
                        st.success("Prijava uspješna ✅")
                        st.rerun()
                except Exception as e:
                    st.error(f"Neuspjela prijava: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

#Novi post
if st.session_state.token:
    st.header("📌 Novi post")
    with st.form("new_post", clear_on_submit=False):
        title = st.text_input("Naslov", key="form_title")
        content = st.text_area("Sadržaj", key="form_content")
        category = st.selectbox("Kategorija", CATEGORIES, key="form_category")
        image = st.file_uploader(
            "Dodaj sliku (png/jpg/jpeg)",
            type=["png", "jpg", "jpeg"],
            key=f"form_image_{st.session_state.upload_key}",
        )
        img_max_side = st.slider(
            "Max dim. slike (px)", 600, 2400, st.session_state.form_img_max_side, step=100, key="form_img_max_side",
        )
        c1, c2 = st.columns(2)
        with c1:
            submitted = st.form_submit_button("Objavi", type="primary")
        with c2:
            st.form_submit_button("➕ Očisti formu", on_click=reset_form)

    if submitted:
        if not title.strip() or not content.strip():
            st.warning("Naslov i sadržaj ne smiju biti prazni.")
        else:
            try:
                data = {"title": title, "content": content, "category": category}
                files = {}
                if image:
                    resized = _resize_image_if_needed(image, img_max_side)
                    if resized:
                        files["image"] = resized
                with st.spinner("Objava u tijeku..."):
                    r = requests.post(f"{API}/posts/", data=data, files=files, headers=auth_headers(), timeout=30)
                    r.raise_for_status()
                st.success("Objavljeno ✅")
                reset_form()
                st.rerun()
            except Exception as e:
                st.error(f"Greška pri objavi: {e}")

#Edit
if "editing_post" in st.session_state and st.session_state.token:
    ep = st.session_state.editing_post
    st.subheader(f"✏️ Uredi post: {ep['title']}")
    with st.form("edit_post_form"):
        new_title = st.text_input("Naslov", ep["title"])
        new_content = st.text_area("Sadržaj", ep["content"])
        try:
            idx = CATEGORIES.index(ep["category"])
        except ValueError:
            idx = 0
        new_category = st.selectbox("Kategorija", CATEGORIES, index=idx)
        save = st.form_submit_button("💾 Spremi promjene", type="primary")
        cancel = st.form_submit_button("Odustani")

    if save:
        try:
            data = {"title": new_title, "content": new_content, "category": new_category}
            r = requests.put(f"{API}/posts/{ep['id']}", data=data, headers=auth_headers(), timeout=20)
            r.raise_for_status()
            st.toast("Post ažuriran ✅")
            del st.session_state["editing_post"]
            st.rerun()
        except Exception as e:
            st.error(f"Greška pri ažuriranju: {e}")
    elif cancel:
        del st.session_state["editing_post"]
        st.rerun()

#Arhiva postova
st.header("📜 Arhiva postova")
try:
    r = requests.get(f"{API}/posts/", timeout=20)
    r.raise_for_status()
    posts = r.json()

    if not posts:
        st.info("Još nema postova.")
    else:
        for p in posts:
            with st.container(border=True):
                st.markdown(f"### {p['title']}")
                st.caption(f"Kategorija: {p['category']}")
                if p.get("image_url"):
                    st.image(API.rstrip('/') + p["image_url"], width=420)
                st.write(p["content"])
                if p.get("created_at"):
                    try:
                        # backend vraća ISO8601; zamjena Z -> +00:00 je fallback
                        dt = datetime.fromisoformat(p["created_at"].replace("Z", "+00:00"))
                        st.caption(f"Objavljeno: {dt.strftime('%d.%m.%Y %H:%M:%S')}")
                    except Exception:
                        pass

                c1, c2 = st.columns(2)
                if st.session_state.token:
                    with c1:
                        if st.button("✏️ Uredi", key=f"edit_{p['id']}"):
                            st.session_state.editing_post = p
                            st.rerun()
                    with c2:
                        if st.button("🗑️ Obriši", key=f"del_{p['id']}"):
                            try:
                                rr = requests.delete(f"{API}/posts/{p['id']}", headers=auth_headers(), timeout=20)
                                rr.raise_for_status()
                                st.toast("Post obrisan ✅")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Greška pri brisanju: {e}")
except Exception as e:
    st.error(f"Greška pri dohvaćanju postova: {e}")

st.markdown("<hr><center>Postify • 2025</center>", unsafe_allow_html=True)
