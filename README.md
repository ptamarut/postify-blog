# ✍️ Postify

Privatni blog: **FastAPI** (backend) + **Streamlit** (frontend).  
Admin se prijavljuje i može kreirati/uređivati/brisati postove; čitatelji čitaju i pretražuju (filtriranje + semantičko).

## Pokretanje

Backend
```bash
python -m uvicorn backend.main:app --reload --port 8000

**Frontend**

streamlit run frontend/streamlit_app.py
