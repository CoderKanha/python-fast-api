from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import UserModel
from app.schema import LoginSchema, UserBaseSchema, TokenData, Token
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from app.utils import verify_password
from app.oauth2 import create_access_token

router = APIRouter(
    tags=["Authentication"]
)

@router.post("/login", response_model=Token)
def login(user_credential: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == user_credential.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"message": "Invalid user Credentials"})

    if not verify_password(user_credential.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"message": "Invalid user Credentials"})


    access_token = create_access_token(data={"user_id": user.id, "user_email": user.email})
    return Token(
        access_token=access_token,
        token_type="Bearer"
    ).dict()