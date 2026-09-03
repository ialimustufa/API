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


def get_existing(note_id: UUID) -> Note:
    try:
        return notes[note_id]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Note not found") from exc


@app.post("/api/v1/notes", response_model=Note, status_code=201)
def create_note(note: NoteIn) -> Note:
    saved = Note(id=uuid4(), **note.model_dump())
    notes[saved.id] = saved
    return saved


@app.get("/api/v1/notes", response_model=list[Note])
def list_notes() -> list[Note]:
    return list(notes.values())


@app.put("/api/v1/notes/{note_id}", response_model=Note)
def replace_note(note_id: UUID, note: NoteIn) -> Note:
    get_existing(note_id)
    saved = Note(id=note_id, **note.model_dump())
    notes[note_id] = saved
    return saved


@app.delete("/api/v1/notes/{note_id}", status_code=204)
def delete_note(note_id: UUID) -> None:
    get_existing(note_id)
    del notes[note_id]
