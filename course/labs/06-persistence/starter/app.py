from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI(title="TaskBox persistence lab")
class TaskIn(BaseModel): title: str
@app.post("/api/v1/tasks", status_code=201)
def create_task(item: TaskIn):
    # TODO: persist a row in SQLite and return its generated id.
    raise NotImplementedError
@app.get("/api/v1/tasks")
def list_tasks():
    # TODO: read rows in deterministic id order.
    raise NotImplementedError
