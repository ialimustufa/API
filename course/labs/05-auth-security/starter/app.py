"""Lab starter. Fill each TODO, then compare with solution/app.py."""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="TaskBox auth lab")
class Login(BaseModel):
    username: str
    password: str

@app.post("/api/v1/auth/token")
def token(form: Login):
    # TODO: look up a password hash, verify it, and return a short-lived JWT.
    raise NotImplementedError

@app.get("/api/v1/me")
def me():
    # TODO: require Bearer credentials and return the token subject.
    raise NotImplementedError
