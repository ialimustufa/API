"""Starter app for the testing exercise; complete the TODO route behavior."""
from uuid import UUID
from fastapi import FastAPI

app = FastAPI(title="Notes API")

@app.get("/api/v1/notes/{note_id}")
def get_note(note_id: UUID):
    # TODO: return a note for a known id and a 404 for an unknown id.
    raise NotImplementedError
