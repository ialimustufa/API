from uuid import UUID, uuid4
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Notes API")
notes: dict[UUID, "Note"] = {}


class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(default="", max_length=10_000)


class Note(NoteIn):
    id: UUID


@app.post("/api/v1/notes", response_model=Note, status_code=201)
def create_note(note: NoteIn):
    # TODO
    raise NotImplementedError


@app.get("/api/v1/notes", response_model=list[Note])
def list_notes():
    # TODO
    raise NotImplementedError


@app.put("/api/v1/notes/{note_id}", response_model=Note)
def replace_note(note_id: UUID, note: NoteIn):
    # TODO: use HTTPException(status_code=404) when absent.
    raise NotImplementedError


@app.delete("/api/v1/notes/{note_id}", status_code=204)
def delete_note(note_id: UUID):
    # TODO
    raise NotImplementedError
