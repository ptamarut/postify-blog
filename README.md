# ✍️ Postify

**Postify** je privatni blog razvijen u Pythonu.  
Backend pokreće **FastAPI**, frontend je izrađen u **Streamlitu**, a podaci se pohranjuju u **SQLite** bazu putem **SQLAlchemy ORM-a**.  

🔑 **Administrator** (nakon prijave) može:  
- kreirati nove objave  
- uređivati postojeće  
- brisati objave  

👥 **Čitatelji** mogu:  
- pregledavati sve objave  
- filtrirati po kategoriji ili naslovu  
- koristiti **semantičko pretraživanje** (SentenceTransformers)  

---

## 🚀 Tehnologije

- [FastAPI](https://fastapi.tiangolo.com/) – brzi Python framework za API-je  
- [Streamlit](https://streamlit.io/) – jednostavan frontend framework  
- [SQLite](https://www.sqlite.org/index.html) – lagana baza podataka  
- [SQLAlchemy](https://www.sqlalchemy.org/) – ORM za rad s bazom  
- [JWT](https://jwt.io/) – autentikacija i autorizacija admina  
- [SentenceTransformers](https://www.sbert.net/) – semantičko pretraživanje  

---

## ▶️ Pokretanje projekta

Pokreni backend i frontend iz root mape projekta:

```bash
# Backend (FastAPI)
python -m uvicorn backend.main:app --reload --port 8000

# Frontend (Streamlit)
streamlit run frontend/streamlit_app.

```bash
streamlit run frontend/streamlit_app.py

