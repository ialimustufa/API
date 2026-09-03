from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Greetings API", version="1.0.0")


class Greeting(BaseModel):
    name: str = Field(min_length=1, max_length=80)


@app.get("/api/v1/greetings", response_model=Greeting)
def get_greeting(name: str = "API learner") -> Greeting:
    return Greeting(name=name)


@app.post("/api/v1/greetings", response_model=Greeting, status_code=201)
def create_greeting(greeting: Greeting) -> Greeting:
    return greeting
