import uuid
import shutil
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

DB_PATH = "./memory/chroma_db"
db = chromadb.PersistentClient(path=DB_PATH, settings=Settings(anonymized_telemetry=False))

embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

collection = db.get_or_create_collection("fact_checks", embedding_function=embedder)

def store_fact_check(claim: str, summary: str, verdict: str, metadata: dict):
    """
    Store a new fact-check entry in the vector store.
    """
    doc_id = str(hash(claim + summary))  # fallback ID
    try:
        # Prevent duplicate IDs on same hash
        existing = collection.get(ids=[doc_id])
        if existing and existing["ids"]:
            doc_id = f"{doc_id}-{uuid.uuid4()}"
    except Exception:
        pass  # likely ID doesn't exist

    collection.add(
        documents=[summary],
        metadatas=[{
            "claim": claim,
            "verdict": verdict,
            "summary": summary,
            **metadata
        }],
        ids=[doc_id]
    )


def search_similar_claims(claim: str, top_k: int = 3):
    """
    Search for previously fact-checked claims similar to the input.
    """
    try:
        results = collection.query(query_texts=[claim], n_results=top_k)
        if not results or not results.get("documents") or not results["documents"][0]:
            print("No matches found in memory.")
        return results
    except Exception as e:
        print(f" Search failed: {e}")
        return {}


def format_results(docs, metas):
    """
    Format memory results for display.
    """
    if not docs or not metas:
        return "No past fact-checks found."
    return "\n\n".join(
        f"[PAST] Claim: {m['claim']}\nVerdict: {m['verdict']}\nSummary: {d}"
        for d, m in zip(docs, metas)
    )


def reset_memory():
    """
    Reset the local memory database by deleting stored fact-checks.
    """
    shutil.rmtree(DB_PATH, ignore_errors=True)
    print("Memory reset: All stored fact checks deleted.")


if __name__ == "__main__":

    result = search_similar_claims("AI will take away jobs")
    if result:
        print(format_results(result.get("documents", [[]])[0], result.get("metadatas", [[]])[0]))
    # reset_memory()
