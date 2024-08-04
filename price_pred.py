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
def fetch_data(symbol, start_date="2015-01-01"):
    end_date = datetime.now().strftime("%Y-%m-%d")
    try:
        stock_data = yf.download(symbol, start=start_date, end=end_date)
        if stock_data.empty:
            stock_data = yf.download(symbol)
        stock_data = stock_data.asfreq('B')  # Set the frequency to business days
        stock_data = stock_data.interpolate(method='linear')  # Interpolate missing values
        logger.info(f"Data for {symbol} starts from {stock_data.index[0].date()} and ends at {stock_data.index[-1].date()}")
        print(f"Data for {symbol} starts from {stock_data.index[0].date()} and ends at {stock_data.index[-1].date()}")
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
        
        if not needs_update(data_path):
            logger.info(f"Data for {company} is up to date. Skipping update.")
            print(f"Data for {company} is up to date. Skipping update.")
            return

        df = fetch_data(symbol)
        if df is None:
            return

        df = df[['Close']]
        df.to_csv(data_path)  # Save the updated data
        y = df['Close']
        
        # Split the data into training and test sets
        y_train, y_test = temporal_train_test_split(y, test_size=30)
        
        # Define the forecasting horizon
        fh = ForecastingHorizon(y_test.index, is_relative=False)
        
        # Initialize and train the AutoARIMA model
        model = AutoARIMA(sp=1, suppress_warnings=True)
        model.fit(y_train)
        
        # Make predictions
        y_pred = model.predict(fh)
        
        # Calculate and print evaluation metrics
        mape = mean_absolute_percentage_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        logger.info(f"MAPE for {company}: {mape:.2f}")
        logger.info(f"RMSE for {company}: {rmse:.2f}")
        logger.info(f"MAE for {company}: {mae:.2f}")
        print(f"MAPE for {company}: {mape:.2f}")
        print(f"RMSE for {company}: {rmse:.2f}")
        print(f"MAE for {company}: {mae:.2f}")

        # Save the forecast
        y_pred.to_csv(forecast_path, header=True)
        logger.info(f"Forecast saved for {company} in {forecast_path}")
        print(f"Forecast saved for {company} in {forecast_path}")

        # Save the model
        joblib.dump(model, model_path)
        logger.info(f"Model saved for {company} in {model_path}")
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
