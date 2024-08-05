import speech_recognition as sr
import pyttsx3
import yfinance as yf
import pandas as pd
import os
import random
import json

# Initialize recognizer and text-to-speech engine
recognizer = sr.Recognizer()
microphone = sr.Microphone()
engine = pyttsx3.init()

# Set the voice to Voice 1 (Microsoft Zira Desktop - English (United States))
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

# Dictionary mapping company names to their stock symbols
company_symbols = {
    "Google": "GOOGL",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Facebook": "META",
    "Tesla": "TSLA",
    "Netflix": "NFLX"
}

# Ensure the prices and news folders exist
prices_folder = 'prices'
news_folder = 'news'
os.makedirs(prices_folder, exist_ok=True)
os.makedirs(news_folder, exist_ok=True)

# List of responses for "thank you"
thank_you_responses = ["Of course, mister Stark", "No worries, mister Stark", "You're welcome, mister Stark", "My pleasure, mister Stark", "Anytime, mister Stark"]

def listen_for_activation():
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening for 'Hey Jarvis'...")
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio)
        print(f"Heard for activation: {command}")
        command = command.lower()
        
        # Check for variations
        if "hey jarvis" in command or "hair jarvis" in command or "hairdress" in command:
            return "hey jarvis"
        else:
            return ""
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""


def listen_for_command():
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening for your command...")
        audio = recognizer.listen(source)

    try:
        command = recognizer.recognize_google(audio)
        print(f"Heard for command: {command}")
        return command.lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""

def respond(text):
    engine.say(text)
    engine.runAndWait()

def get_stock_price(symbol):
    stock = yf.Ticker(symbol)
    todays_data = stock.history(period='1d')
    if todays_data.empty:
        raise ValueError(f"No data found for {symbol}")
    return todays_data['Close'][0]

def fetch_predicted_price(company):
    try:
        forecast_path = os.path.join(prices_folder, f"{company}_forecast.csv")
        forecast_df = pd.read_csv(forecast_path)
        print(f"Columns in {forecast_path}: {forecast_df.columns.tolist()}")
        
        # Assuming the predicted price is in the last column
        predicted_price = forecast_df.iloc[-1, -1]
        return predicted_price
    except Exception as e:
        raise ValueError(f"Could not fetch the predicted price for {company}: {e}")

def read_news_from_file(file_path='news/latest_news.json'):
    try:
        with open(file_path, 'r') as file:
            news_data = json.load(file)
        return news_data
    except Exception as e:
        raise ValueError(f"Could not read the news from file: {e}")

def handle_command(command):
    if "thank you" in command:
        response = random.choice(thank_you_responses) 
        respond(response)
        print(response)
        exit()

    if "news" in command:
        try:
            news_data = read_news_from_file()
            for idx, news in enumerate(news_data):
                respond(f"Headline {idx + 1}: {news['title']}")
                print(f"Headline {idx + 1}: {news['title']}")
        except ValueError as ve:
            respond(str(ve))
            print(ve)
        except Exception as e:
            respond("I could not fetch the latest news. Please try again.")
            print(e)
        return

    if "elaborate" in command:
        try:
            keyword = command.replace("elaborate on", "").strip().lower()
            news_data = read_news_from_file()
            for news in news_data:
                if keyword in news['title'].lower():
                    respond(news['summary'])
                    print(news['summary'])
                    return
            respond(f"Sorry, I couldn't find any article related to {keyword}.")
            print(f"Sorry, I couldn't find any article related to {keyword}.")
        except ValueError as ve:
            respond(str(ve))
            print(ve)
        except Exception as e:
            respond("I could not fetch the article summary. Please try again.")
            print(e)
        return
    
    if "portfolio" in command:
        print("Handling portfolio command")  # Debugging statement
        try:
            portfolio_prices = []
            for company, symbol in company_symbols.items():
                price = get_stock_price(symbol)
                portfolio_prices.append(f"{company} ({symbol}) is ${price:.2f}")
            respond("Here are the current prices in your portfolio:")
            for price_info in portfolio_prices:
                respond(price_info)
                print(price_info)
        except Exception as e:
            respond("I could not fetch the portfolio prices. Please try again.")
            print(f"Error fetching portfolio prices: {e}")
        return


    for key in company_symbols:
        if key.lower() in command:
            symbol = company_symbols[key]
            if "price" in command:
                try:
                    price = get_stock_price(symbol)
                    respond(f"The current price of {key} ({symbol}) is ${price:.2f}")
                    print(f"The current price of {key} ({symbol}) is ${price:.2f}")
                except ValueError as ve:
                    respond(str(ve))
                    print(ve)
                except Exception as e:
                    respond("I could not fetch the stock price. Please try again.")
                    print(e)
            elif "predict" in command:
                try:
                    predicted_price = fetch_predicted_price(key)
                    respond(f"The predicted price of {key} ({symbol}) for the next day is ${predicted_price:.2f}")
                    print(f"The predicted price of {key} ({symbol}) for the next day is ${predicted_price:.2f}")
                except ValueError as ve:
                    respond(str(ve))
                    print(ve)
                except Exception as e:
                    respond("I could not fetch the predicted stock price. Please try again.")
                    print(e)

    respond("Sorry, I don't have data for that company.")
    print(f"Command not recognized: {command}")

    for key in company_symbols:
        if key.lower() in command:
            symbol = company_symbols[key]
            if "price" in command:
                try:
                    price = get_stock_price(symbol)
                    respond(f"The current price of {key} ({symbol}) is ${price:.2f}")
                    print(f"The current price of {key} ({symbol}) is ${price:.2f}")
                except ValueError as ve:
                    respond(str(ve))
                    print(ve)
                except Exception as e:
                    respond("I could not fetch the stock price. Please try again.")
                    print(e)
            elif "predict" in command:
                try:
                    predicted_price = fetch_predicted_price(key)
                    respond(f"The predicted price of {key} ({symbol}) for the next day is ${predicted_price:.2f}")
                    print(f"The predicted price of {key} ({symbol}) for the next day is ${predicted_price:.2f}")
                except ValueError as ve:
                    respond(str(ve))
                    print(ve)
                except Exception as e:
                    respond("I could not fetch the predicted stock price. Please try again.")
                    print(e)
            return

    respond("Sorry, I don't have data for that company.")
    print(f"Command not recognized: {command}")

# Main loop to listen for "Hey Jarvis" and commands
while True:
    activation_command = listen_for_activation()
    if "hey jarvis" in activation_command:
        respond("How can I assist you?")
        while True:
            user_command = listen_for_command()
            if user_command:
                handle_command(user_command)
