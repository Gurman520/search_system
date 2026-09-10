from fastapi import Request, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User


class NotAuthenticated(Exception):
    pass

def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise NotAuthenticated()
    user = db.get(User, user_id)
    if not user:
        request.session.clear()
        raise NotAuthenticated()
    return user
