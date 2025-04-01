from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from url_shortener.app.schemas.link import LinkCreate, LinkUpdate, LinkRead
from url_shortener.app.db.models import Link
from url_shortener.app.api.dependencies import get_db, get_current_user, get_redis

router = APIRouter(
    prefix="/links",
    tags=["links"]
)

@router.post("/shorten", response_model=LinkRead, status_code=status.HTTP_201_CREATED)
def create_link(link_data: LinkCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if link_data.alias:
        existing = db.query(Link).filter(Link.short_code == link_data.alias).first()
        if existing:
            raise HTTPException(status_code=400, detail="Alias already exists")
        short_code = link_data.alias
    else:
        from url_shortener import generate_short_code
        short_code = generate_short_code(db)
    new_link = Link(
        original_url=link_data.original_url,
        short_code=short_code,
        expires_at=link_data.expires_at,
        owner_id=current_user.id if current_user else None
    )
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link

@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(short_code: str, db: Session = Depends(get_db), redis = Depends(get_redis), current_user = Depends(get_current_user)):
    link = db.query(Link).filter(Link.short_code == short_code, Link.owner_id == current_user.id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    db.delete(link)
    db.commit()
    redis.delete(f"link:{short_code}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{short_code}", response_model=LinkRead)
def update_link(short_code: str, link_update: LinkUpdate, db: Session = Depends(get_db), redis = Depends(get_redis), current_user = Depends(get_current_user)):
    link = db.query(Link).filter(Link.short_code == short_code, Link.owner_id == current_user.id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    if link_update.alias and link_update.alias != short_code:
        existing = db.query(Link).filter(Link.short_code == link_update.alias).first()
        if existing:
            raise HTTPException(status_code=400, detail="Alias already exists")
        redis.delete(f"link:{short_code}")
        link.short_code = link_update.alias
    if link_update.original_url:
        link.original_url = link_update.original_url
        redis.delete(f"link:{link.short_code}")
    if link_update.expires_at:
        link.expires_at = link_update.expires_at
    db.commit()
    db.refresh(link)
    return link

@router.get("/{short_code}/stats", response_model=LinkRead)
def link_stats(short_code: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    link = db.query(Link).filter(Link.short_code == short_code, Link.owner_id == current_user.id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link

@router.get("/search", response_model=List[LinkRead])
def search_links(original_url: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    links = db.query(Link).filter(Link.original_url == original_url, Link.owner_id == current_user.id).all()
    return links
