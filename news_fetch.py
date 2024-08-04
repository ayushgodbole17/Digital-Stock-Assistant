import warnings
warnings.filterwarnings("ignore", message="floor_divide is deprecated, and will be removed in a future version of pytorch")

import requests
import json
import os
from bs4 import BeautifulSoup
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# News API configuration
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
NEWS_API_URL = 'https://newsapi.org/v2/everything'
NEWS_API_SOURCES = 'forbes,financial-times,the-wall-street-journal,bloomberg,reuters'

# Ensure the news folder exists
news_folder = 'news'
os.makedirs(news_folder, exist_ok=True)

# Ensure the models folder exists
models_folder = 'models'
os.makedirs(models_folder, exist_ok=True)

# Paths to the local model files
model_name = "sshleifer/distilbart-cnn-12-6"
model_path = os.path.join(models_folder, model_name.replace('/', '_'))

# Download and save the model if not already present
if not os.path.exists(model_path):
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model.save_pretrained(model_path)
    tokenizer.save_pretrained(model_path)
else:
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)

# Initialize the summarizer
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)

# Function to fetch the latest financial news with specific keywords from specified sources
def fetch_latest_news():
    try:
        params = {
            'apiKey': NEWS_API_KEY,
            'q': 'stock OR financial OR earnings OR investment OR market',
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 5,
            'domains': 'forbes.com,ft.com,wsj.com,bloomberg.com,reuters.com'
        }
        response = requests.get(NEWS_API_URL, params=params)

        news_data = response.json()
        articles = news_data.get('articles', [])
        if not articles:
            raise ValueError("No news articles found.")
        
        top_articles = articles[:5]
        news_data = [{'title': article['title'], 'url': article['url']} for article in top_articles]
        return news_data
    except Exception as e:
        raise ValueError(f"Could not fetch the latest news: {e}")

# Function to fetch and summarize article content
def fetch_article_summary(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        content = ' '.join([para.get_text() for para in paragraphs])

        # Truncate or split content if it's too long for the model
        max_length = 1024
        if len(content) > max_length:
            content = content[:max_length]

        summary = summarizer(content, max_length=150, min_length=50, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        raise ValueError(f"Could not fetch or summarize the article: {e}")

# Function to save news to a file
def save_news_to_file(news_data, file_path='news/latest_news.json'):
    with open(file_path, 'w') as file:
        json.dump(news_data, file)

# Function to load existing news from a file
def load_existing_news(file_path='news/latest_news.json'):
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r') as file:
        return json.load(file)

# Check if the fetched news is different from the existing news
def is_news_different(fetched_news, existing_news):
    if existing_news is None:
        return True
    fetched_titles = {news['title'] for news in fetched_news}
    existing_titles = {news['title'] for news in existing_news}
    return fetched_titles != existing_titles

# Main function
def main():
    try:
        # Fetch the latest financial news
        fetched_news = fetch_latest_news()

        # Load existing news
        existing_news = load_existing_news()

        # Check if the fetched news is different from the existing news
        if not is_news_different(fetched_news, existing_news):
            print("News is up to date. Skipping summarization.")
            return

        # Summarize the fetched news
        for news in fetched_news:
            news['summary'] = fetch_article_summary(news['url'])
        
        # Save the summarized news data to a file
        save_news_to_file(fetched_news)
        print("Latest financial news saved successfully.")
    except ValueError as ve:
        print(ve)
    except Exception as e:
        print(f"Error fetching or saving news: {e}")
if __name__ == "__main__":
    main()
