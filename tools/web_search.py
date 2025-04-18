import requests


# os.getenv("SERPER_API_KEY")
# export SERPER_API_KEY="key"

SEARCH_URL = "https://google.serper.dev/search"

def google_search(query, num_results=5):
    headers = {"X-API-KEY": SERPER_API_KEY}
    payload = {"q": query}

    response = requests.post(SEARCH_URL, json=payload, headers=headers)
    data = response.json()

    results = []
    for item in data.get("organic", [])[:num_results]:
        results.append({
            "title": item["title"],
            "url": item["link"],
            "snippet": item.get("snippet", "")
        })

    return results
