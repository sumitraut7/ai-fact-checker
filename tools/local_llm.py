# tools/local_llm.py

from langchain_community.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

MODEL = "mistral"

# Create an Ollama LLM instance
llm = Ollama(model=MODEL)


def local_llm_ask(prompt: str, system_prompt: str = None) -> str:
    """
    Ask the local LLM using a simple prompt (optionally with a system message).
    """
    if system_prompt:
        prompt = f"{system_prompt}\n\n{prompt}"
    return llm.invoke(prompt)


def local_llm_chain_ask(prompt_text: str, template: str = None) -> str:
    """
    Use LangChain's prompt templating system for more structured prompts.
    """
    if template is None:
        template = "You are a helpful assistant. Answer the following query:\n\n{query}"

    prompt = PromptTemplate(
        input_variables=["query"],
        template=template
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(query=prompt_text)


if __name__ == "__main__":
    # Simple direct use
    response = local_llm_ask("Can you write code?")
    print("Direct response:\n", response)

    # Example with LangChain prompt template
    template = "Rewrite the following text to make it more professional:\n\n{query}"
    chain_response = local_llm_chain_ask("hey there! i want u to help", template)
    print("LangChain templated response:\n", chain_response)
