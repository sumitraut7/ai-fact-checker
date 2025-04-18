# agents/reader_agent.py

from tools.scrape_url import scrape_url
from tools.local_llm import local_llm_chain_ask

SUMMARY_PROMPT_TEMPLATE = """
You are a helpful assistant. Summarize the following article content clearly and concisely.

Article:
{article}
"""

SHORT_SUMMARY_PROMPT_TEMPLATE = """
You are a helpful assistant. Summarize the following content **briefly in 2-3 sentences. Focus only on the key facts.**

Article:
{article}
"""

def summarize_url(url: str) -> str:
    content = scrape_url(url)
    if not content:
        return "Could not extract content."

    summary = local_llm_chain_ask(
        prompt_text="",  # entire prompt comes from the template
        template=SUMMARY_PROMPT_TEMPLATE.format(article=content)
    )
    short_summary = local_llm_chain_ask(
        prompt_text="",  # entire prompt comes from the template
        template=SHORT_SUMMARY_PROMPT_TEMPLATE.format(article=content)
    )

    return summary, short_summary
