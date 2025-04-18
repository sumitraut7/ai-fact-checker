from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.pipeline import answer_followup, run_fact_check_stream
from server.session import SessionManager
from fastapi.responses import StreamingResponse

app = FastAPI()
session_manager = SessionManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class FactCheckRequest(BaseModel):
    claim: str
    session_id: str = None

class FollowUpRequest(BaseModel):
    session_id: str
    question: str

@app.post("/fact-check")
async def fact_check(request: FactCheckRequest):
    session_id = request.session_id or session_manager.create_session()
    session_manager.add_claim(session_id, request.claim)

    def generate_fact_check_stream(claim):
        for chunk in run_fact_check_stream(claim, session_id):
            yield chunk

    return StreamingResponse(generate_fact_check_stream(request.claim), media_type="text/plain")

@app.post("/followup-stream")
def followup_stream(request: FollowUpRequest):
    session = session_manager.get_session(request.session_id)
    claim = session_manager.get_session(request.session_id)['claim']

    return StreamingResponse(answer_followup(session, request.question, claim), media_type="text/plain")

@app.post("/new-session")
def new_session():
    return {"session_id": session_manager.create_session()}
