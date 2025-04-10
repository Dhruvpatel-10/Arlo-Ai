import json
# https://docs.python.org/3/library/urllib.request.html#module-urllib.request
import os
import urllib.request
from dotenv import load_dotenv; load_dotenv()

def get_news(category: str = "technology"):
    """
    Get news from gnews.io

    Args:
        category (str): Defaults to "technology".

    Returns:
        None
    """
    apikey = os.getenv("NEWS_API_KEY")
    url = f"https://gnews.io/api/v4/top-headlines?category={category}&lang=en&country=in&max=10&apikey={apikey}"
    news_data = list()
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))
        articles = data["articles"]
        rounds = min(len(articles), 7)
        for i in range(rounds):
            news_data.append((str(i+1) + str(". " + "Title: " + articles[i]["title"]), str("Description: " + articles[i]['description'])))

    return news_data