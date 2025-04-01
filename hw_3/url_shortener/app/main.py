from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from datetime import datetime
from url_shortener.app.api.routers import auth, links
from url_shortener.app.db.models import Base, Link
from url_shortener.app.db.session import engine
from url_shortener.app.api.dependencies import get_db, get_redis

# Создаем таблицы при запуске (для разработки)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener API",
    description="Сервис сокращения ссылок на FastAPI, PostgreSQL и Redis",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(links.router)

# Редирект по короткому коду: GET /{short_code}
@app.get("/{short_code}", include_in_schema=False)
def redirect(short_code: str, db = Depends(get_db), redis = Depends(get_redis)):
    cache_key = f"link:{short_code}"
    cached_url = redis.get(cache_key)
    if cached_url:
        return RedirectResponse(url=cached_url.decode("utf-8"))
    from url_shortener.app.db.models import Link
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Link expired")
    # Обновляем счетчик переходов
    link.click_count += 1
    link.last_click_at = datetime.utcnow()
    db.commit()
    redis.set(cache_key, link.original_url, ex=3600)
    return RedirectResponse(url=link.original_url)