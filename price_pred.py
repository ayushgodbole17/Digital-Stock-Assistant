import yfinance as yf
import pandas as pd
import numpy as np
from sktime.forecasting.arima import AutoARIMA
from sktime.forecasting.model_selection import temporal_train_test_split
from sktime.forecasting.base import ForecastingHorizon
from sktime.performance_metrics.forecasting import mean_absolute_percentage_error, mean_squared_error, mean_absolute_error
from datetime import datetime, time as dtime, timedelta
import joblib
from joblib import Parallel, delayed
import logging
import os

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of company symbols
company_symbols = {
    "Google": "GOOGL",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Facebook": "META",
    "Tesla": "TSLA",
    "Netflix": "NFLX"
}

# Ensure the prices folder exists
prices_folder = 'prices'
os.makedirs(prices_folder, exist_ok=True)

# Check if today is a business day and within market hours
def is_market_open():
    now = datetime.now()
    today = now.date()
    current_time = now.time()
    # Check if today is Saturday or Sunday
    if today.weekday() >= 5:  # 5 is Saturday, 6 is Sunday
        return False
    # Check if time is after 4 PM Friday and before 9:30 AM Monday
    if today.weekday() == 4 and current_time > dtime(16, 0):
        return False
    if today.weekday() == 0 and current_time < dtime(9, 30):
        return False
    return True

# Check if the latest date in the data is today's date
def needs_update(file_path):
    if not os.path.exists(file_path):
        logger.info(f"File {file_path} does not exist. Needs update.")
        print(f"File {file_path} does not exist. Needs update.")
        return True
    df = pd.read_csv(file_path, index_col=0, parse_dates=True)
    last_date = df.index[-1].date()
    today = datetime.now().date()
    logger.info(f"Last date in {file_path}: {last_date}, Today's date: {today}")
    print(f"Last date in {file_path}: {last_date}, Today's date: {today}")
    if last_date < today:
        logger.info(f"Data in {file_path} is not up to date. Needs update.")
        print(f"Data in {file_path} is not up to date. Needs update.")
        return True
    else:
        logger.info(f"Data in {file_path} is up to date. No update needed.")
        print(f"Data in {file_path} is up to date. No update needed.")
        return False

# Fetch historical data
def fetch_data(symbol, start_date=None):
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    if start_date is None:
        start_date = "2010-01-01"  # Default start date if no start_date is provided
    
    try:
        stock_data = yf.download(symbol, start=start_date, end=end_date)
        if stock_data.empty:
            stock_data = yf.download(symbol)
        stock_data = stock_data.asfreq('B')  # Set the frequency to business days
        stock_data = stock_data.interpolate(method='linear')  # Interpolate missing values
        logger.info(f"Data for {symbol} fetched from {start_date} to {stock_data.index[-1].date()}")
        print(f"Data for {symbol} fetched from {start_date} to {stock_data.index[-1].date()}")
        return stock_data
    except Exception as e:
        logger.error(f"Could not fetch data for {symbol}: {e}")
        print(f"Could not fetch data for {symbol}: {e}")
        return None

# Train and forecast using sktime AutoARIMA
def train_and_forecast(company, symbol):
    try:
        forecast_path = os.path.join(prices_folder, f"{company}_forecast.csv")
        data_path = os.path.join(prices_folder, f"{company}_data.csv")
        model_path = os.path.join(prices_folder, f"{company}_model.joblib")
        
        # Check if the data is up to date
        if not needs_update(data_path):
            logger.info(f"Data for {company} is up to date. Skipping update.")
            print(f"Data for {company} is up to date. Skipping update.")
            return
        
        # Get the last date from the existing data
        if os.path.exists(data_path):
            existing_data = pd.read_csv(data_path, index_col=0, parse_dates=True)
            last_date = existing_data.index[-1].date()
            # Start fetching from the next day
            start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            start_date = "2010-01-01"  # Start from a default date if no existing data
        
        # Fetch only the missing data
        new_data = fetch_data(symbol, start_date)
        if new_data is None or new_data.empty:
            return
        
        # Combine the old data with the new data
        if os.path.exists(data_path):
            combined_data = pd.concat([existing_data, new_data])
        else:
            combined_data = new_data
        
        combined_data.to_csv(data_path)  # Save the updated data
        y = combined_data['Close']
        
        # Split the data into training and test sets
        y_train, y_test = temporal_train_test_split(y, test_size=10)
        
        # Define the forecasting horizon
        fh = ForecastingHorizon(y_test.index, is_relative=False)
        
        # Initialize and train the AutoARIMA model
        model = AutoARIMA(sp=1, suppress_warnings=True)
        model.fit(y_train)
        
        # Make predictions
        y_pred = model.predict(fh)
        
        # Save the forecast
        y_pred.to_csv(forecast_path, header=True)
        print(f"Forecast saved for {company} in {forecast_path}")

        # Save the model
        joblib.dump(model, model_path)
        print(f"Model saved for {company} in {model_path}")
    except Exception as e:
        logger.error(f"Error processing {company}: {e}")
        print(f"Error processing {company}: {e}")


# Main execution with market open check
def main():
    if not is_market_open():
        logger.info("Market is closed. Skipping script execution.")
        print("Market is closed. Skipping script execution.")
        return
    
    # Parallel processing for faster execution
    Parallel(n_jobs=-1)(delayed(train_and_forecast)(company, symbol) for company, symbol in company_symbols.items())

if __name__ == "__main__":
    main()
