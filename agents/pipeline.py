from agents.reader_agent import summarize_url
from agents.judge_agent import judge_claim_against_summary
from agents.research_agent import run_research_agent
from tools.local_llm import local_llm_chain_ask
from collections import Counter
from retriever.vector_store import store_fact_check, search_similar_claims, format_results
from tools.scrape_url import extract_percentage, scrape_url
import queue
import threading


def aggregate_final_verdict(results):
    verdicts = [r["verdict"] for r in results]
    counter = Counter(verdicts)
    majority = counter.most_common(1)[0]

    final_verdict =  f"Final Verdict for claim: {majority[0]}\n" + \
            f"{counter.get('Supports', 0)} articles support claim\n" + \
            f"{counter.get('Refutes', 0)} articles Refutes claim\n" + \
            f"{counter.get('Neutral', 0)} articles take Neutral stand for claim\n" + \
            f"Total articles refered : {len(results)}\n"
    return final_verdict

def run_fact_check_stream(claim: str, session_id: str):
    output_queue = queue.Queue()
    summary= []
    sources = run_research_agent(claim)
    print(f"Searching web for: {claim}")
    output_queue.put(f"🌐 Searching web for: {claim}\n")
    sources = run_research_agent(claim)

    def stream_resources():
        for src in sources:
            print(f"Checking accessibility: {src['url']}")
            raw_text = scrape_url(src['url'])
            if raw_text.strip():
                output_queue.put(f"✔️ Found source: {src['url']}\n")
            else:
                output_queue.put(f"Skipping source (unreachable or empty): {src['url']}\n")
    stream_resources()
    output_queue.put(f"\n\n🧠 Summarizing all resources : \n")

    def stream_summaries():
        print(f"Summarizing all resources")

        for i, src in enumerate(sources):
            summ , short_summary = summarize_url(src['url'])
            summary.append(summ)
            output_queue.put(f"🔍 Summary of {src['url']}:\n{short_summary}\n")

    def stream_judgments():

        judgments = []
        print(f"Judging claim against {len(sources)} summaries")
        if len(summary)==len(sources):
            output_queue.put(f"⚖️ Judging claim against {len(sources)} sources\n")

        while len(summary) < len(sources):
            pass  # Wait for summaries

        for i, src in enumerate(sources):
            result = judge_claim_against_summary(claim, summary[i])
            print(result["raw"])

            judgments.append({
                "title": src["title"],
                "url": src["url"],
                "summary": summary[i],
                "verdict": result["verdict"],
                "confidence": result["confidence"],
                "reason": result["reason"]
            })

            output_queue.put(f"💡 Judgment for {src['url']}:\n" + \
                f"Verdict: {result['verdict']}\n" + \
                # f"Confidence: {result['confidence']}%\n" + \
                f"Reason: {result['reason']}\n")

        print(f"Storing results in vector DB")
        for r in judgments:
            if r["verdict"] in {"Supports", "Refutes"}:
                store_fact_check(
                    claim=claim,
                    verdict=r["verdict"],
                    summary=r["summary"],
                    metadata={"url": r["url"], "title": r["title"]}
                )

        summary_stats = aggregate_final_verdict(judgments)
        output_queue.put(f"📊 Final Verdict:\n{summary_stats}\n")
        output_queue.put(None)  # signal end


    # def combine_streams():
    #     # Yield resources, summaries, and judgments in sequence
    #     yield from stream_resources()
    #     yield from stream_summaries()
    #     yield from stream_judgments()
    threading.Thread(target=stream_summaries, daemon=True).start()
    threading.Thread(target=stream_judgments, daemon=True).start()

    def stream_output():
        while True:
            msg = output_queue.get()
            if msg is None:
                break
            yield msg

    return stream_output()

def answer_followup(session, question: str, claim: str):

    session_history = session.get("history", [])
    original_claim = session_history[0]["content"] if session_history else "unknown claim"

    # Retrieve and format past relevant fact-checks
    past_evidence = search_similar_claims(claim)
    if past_evidence and past_evidence.get("documents") and past_evidence["documents"][0]:
        past_context = format_results(
            past_evidence["documents"][0],
            past_evidence["metadatas"][0]
        )
    else:
        past_context = "No relevant past fact-checks found."

    print(f"Past facts found : {past_context}")
    context = f"Claim: {original_claim}\n\n"
    context += f"Relevant past facts:\n{past_context}\n\n"
    context += "Conversation history:\n"
    for h in session_history:
        context += f"{h['role'].capitalize()}: {h['content']}\n"
    context += f"\nUser: {question}\nAssistant:"

    answer = local_llm_chain_ask(prompt_text="", template=context)

    session["history"].append({"role": "user", "content": question})
    session["history"].append({"role": "assistant", "content": answer})

    return answer

