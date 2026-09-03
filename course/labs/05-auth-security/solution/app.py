"""A compact, runnable JWT boundary for the TaskBox lessons."""
from datetime import UTC, datetime, timedelta
import os
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pwdlib import PasswordHash
from pydantic import BaseModel

app = FastAPI(title="TaskBox auth lab")
bearer = HTTPBearer(auto_error=False)
passwords = PasswordHash.recommended()
USERS = {"ada": passwords.hash("correct horse"), "grace": passwords.hash("compiler")}
SECRET = os.getenv("TASKBOX_JWT_SECRET", "dev-only-change-me")

class Login(BaseModel):
    username: str
    password: str

def unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail="Invalid authentication credentials", headers={"WWW-Authenticate": "Bearer"})

@app.post("/api/v1/auth/token")
def token(form: Login):
    stored = USERS.get(form.username)
    if not stored or not passwords.verify(form.password, stored):
        raise unauthorized()
    now = datetime.now(UTC)
    return {"access_token": jwt.encode({"sub": form.username, "iat": now, "exp": now + timedelta(minutes=15)}, SECRET, algorithm="HS256"), "token_type": "bearer", "expires_in": 900}

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise unauthorized()
    try:
        claims = jwt.decode(credentials.credentials, SECRET, algorithms=["HS256"])
        if not isinstance(claims.get("sub"), str):
            raise ValueError
        return claims["sub"]
    except (jwt.PyJWTError, ValueError):
        raise unauthorized()

@app.get("/api/v1/me")
def me(user: str = Depends(current_user)):
    return {"username": user}

@app.get("/healthz")
def health():
    return {"status": "ok"}
