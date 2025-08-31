import os
import time
import shutil
from typing import List, Optional

from fastapi import (
    FastAPI, HTTPException, Depends,
    UploadFile, File, BackgroundTasks, Form
)
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from backend.database import SessionLocal, init_db
from backend.models import Post, User
from backend.schemas import PostRead
from backend.embeddings import add_doc_to_index, search_index, clear_index
from backend.auth import router as auth_router, get_current_user, hash_password

# inicijalizacija baze (kreira tablice ako ne postoje)
init_db()

app = FastAPI(title="Blogger API")

# Uključi auth rute
app.include_router(auth_router)

# direktorij za uploadane slike i statički servis
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# DB session po zahtjevu (FastAPI ovisi o ovome)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# seed admin korisnika iz ENV varijabli
def seed_admin():
    username = os.getenv("ADMIN_USERNAME", "admin")
    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "admin12345")
    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.username == username).first()
        if not exists:
            u = User(username=username, email=email, hashed_password=hash_password(password))
            db.add(u)
            db.commit()
            print(f"[seed] Kreiran admin korisnik: {username}")
    finally:
        db.close()


# kompletni rebuild semantičkog indeksa (sam otvara/zatvara DB sesiju)
def rebuild_whole_index() -> int:
    db = SessionLocal()
    try:
        posts = db.query(Post).all()
        clear_index()
        for p in posts:
            add_doc_to_index(p.id, p.title, p.content, p.category)
        return len(posts)
    finally:
        db.close()


# pri pokretanju procesa
@app.on_event("startup")
def _on_startup():
    seed_admin()
    n = rebuild_whole_index()
    print(f"[startup] Reindeksirano {n} postova.")


# CREATE: novi post (+ opcionalno slika) — ZAŠTIĆENO
@app.post("/posts/", response_model=PostRead)
async def create_post(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  #samo admin s JWT
):
    if not title.strip() or not content.strip() or not category.strip():
        raise HTTPException(status_code=400, detail="title, content i category su obavezni")

    image_filename = None
    if image:
        ext = os.path.splitext(image.filename)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg"):
            raise HTTPException(status_code=400, detail="Dozvoljeni formati slike su: png, jpg, jpeg")
        image_filename = f"{int(time.time() * 1000)}{ext}"
        path = os.path.join(uploads_dir, image_filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(image.file, f)

    post = Post(
        title=title.strip(),
        content=content.strip(),
        category=category.strip(),
        image_filename=image_filename
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    background_tasks.add_task(add_doc_to_index, post.id, post.title, post.content, post.category)

    return PostRead(
        id=post.id,
        title=post.title,
        content=post.content,
        category=post.category,
        image_url=f"/uploads/{post.image_filename}" if post.image_filename else None,
        created_at=post.created_at,
    )


# READ: svi postovi (otvoreno)
@app.get("/posts/", response_model=List[PostRead])
def list_posts(db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    return [
        PostRead(
            id=p.id,
            title=p.title,
            content=p.content,
            category=p.category,
            image_url=f"/uploads/{p.image_filename}" if p.image_filename else None,
            created_at=p.created_at,
        )
        for p in posts
    ]


# UPDATE: izmjena (ZAŠTIĆENO)
@app.put("/posts/{post_id}", response_model=PostRead)
def update_post(
    post_id: int,
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user), 
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post ne postoji")

    post.title = title.strip()
    post.content = content.strip()
    post.category = category.strip()

    db.commit()
    db.refresh(post)

    if background_tasks is not None:
        background_tasks.add_task(rebuild_whole_index)

    return PostRead(
        id=post.id,
        title=post.title,
        content=post.content,
        category=post.category,
        image_url=f"/uploads/{post.image_filename}" if post.image_filename else None,
        created_at=post.created_at,
    )


# DELETE: briše post (ZAŠTIĆENO)
@app.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user), 
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post ne postoji")

    if post.image_filename:
        path = os.path.join(uploads_dir, post.image_filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    db.delete(post)
    db.commit()

    if background_tasks is not None:
        background_tasks.add_task(rebuild_whole_index)

    return {"detail": "Post obrisan"}


# FILTER
@app.get("/filter/", response_model=List[PostRead])
def filter_posts(
    category: Optional[str] = None,
    title: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Post)
    if category:
        q = q.filter(Post.category == category)
    if title:
        q = q.filter(Post.title.ilike(f"%{title}%"))

    posts = q.order_by(Post.created_at.desc()).all()
    return [
        PostRead(
            id=p.id,
            title=p.title,
            content=p.content,
            category=p.category,
            image_url=f"/uploads/{p.image_filename}" if p.image_filename else None,
            created_at=p.created_at,
        )
        for p in posts
    ]


# SEMANTIČKA PRETRAGA
@app.get("/search/")
def search(q: str, k: int = 5, db: Session = Depends(get_db)):
    try:
        hits = search_index(q, top_k=k)
        enriched = []
        for h in hits:
            p = db.query(Post).filter(Post.id == h["id"]).first()
            image_url = f"/uploads/{p.image_filename}" if p and p.image_filename else None
            enriched.append(
                {
                    "id": h["id"],
                    "title": h["title"],
                    "content": h["content"],
                    "category": h["category"],
                    "score": h["score"],
                    "image_url": image_url,
                    "created_at": p.created_at if p else None,
                }
            )
        return enriched
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# health
@app.get("/health")
def health():
    return {"status": "ok"}
