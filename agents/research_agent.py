# agents/research_agent.py
from tools.web_search import google_search

def run_research_agent(claim):
    # Use a search API to get links
    results = google_search(claim)
    return results
