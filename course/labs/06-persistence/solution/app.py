import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

URL = os.getenv("TASKBOX_DATABASE_URL", "sqlite:///./taskbox-lab.db")
engine = create_engine(
    URL, connect_args={"check_same_thread": False} if URL.startswith("sqlite") else {}
)


class Base(DeclarativeBase):
    pass


class TaskRow(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TaskIn(BaseModel):
    title: str


class Task(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    created_at: datetime


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="TaskBox persistence lab", lifespan=lifespan)


@app.post("/api/v1/tasks", response_model=Task, status_code=201)
def create_task(item: TaskIn):
    with Session(engine) as db:
        row = TaskRow(title=item.title, created_at=datetime.now(UTC))
        db.add(row)
        db.commit()
        db.refresh(row)
        return row


@app.get("/api/v1/tasks", response_model=list[Task])
def list_tasks():
    with Session(engine) as db:
        return list(db.scalars(select(TaskRow).order_by(TaskRow.id)))


@app.get("/api/v1/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    with Session(engine) as db:
        row = db.get(TaskRow, task_id)
        if not row:
            raise HTTPException(404, "Task not found")
        return row
