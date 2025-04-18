# app/utils/session.py
import uuid

class SessionManager:
    def __init__(self):
        self.sessions = {}

    def create_session(self):
        sid = str(uuid.uuid4())
        self.sessions[sid] = {"history": [], 'claim':None}
        return sid

    def add_claim(self, sid, claim):
        self.sessions[sid]["claim"] =  claim

    def get_session(self, sid):
        return self.sessions.get(sid, {"history": []})

    def save_interaction(self, sid, role, content):
        self.sessions[sid]["history"].append({"role": role, "content": content})
