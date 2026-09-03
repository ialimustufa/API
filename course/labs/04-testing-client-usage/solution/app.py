"""Importable copy of the Lab 03 solution for an isolated test run."""

from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
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
    saved = Note(id=uuid4(), **note.model_dump())
    notes[saved.id] = saved
    return saved


@app.get("/api/v1/notes", response_model=list[Note])
def list_notes():
    return list(notes.values())


@app.delete("/api/v1/notes/{note_id}", status_code=204)
def delete_note(note_id: UUID):
    if note_id not in notes:
        raise HTTPException(404, "Note not found")
    del notes[note_id]
