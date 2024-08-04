# Digital-Stock-Assistant

About:  
A financial digital assistant app, inspired by J.A.R.V.I.S.  
To run, run the run_all.bat script.  

Current State: (as of 5th August 2024):    
1) Fetches the stock price for a pre-determind list of companies.
2) Predicts the next-day price for a particular company, using ARIMA time-series prediction.
3) Fetches 5 news headlines from a pre-determined list of sources, like Forbes and Bloomberg.
4) Elaborates on a particular headline if asked, by using beautifulsoup and BERT to scrape the article in question and summarise it.

There are checks in the price and news scripts to ensure that if data already exists, it does not run the prediction models in the respective scripts.  

Future Ideas:
1) Improve the summarisation model, either bulding a model from scratch, fine-tuning a pre-trained model, or just finding a better pre-trained model.
2) Improve the time-series model using additional information. (For example, if Google reports that they suffered a loss, that might result in a stock plunge the next day. Also, companies in a particular sector, tend to go up and down together. So, integrating those headlines or any other additional information (?) could improve price prediction)
3) Train a tts model to use a custom voice.  
4) Improve prompts and prompt recognition.  
5) Add more functionality, such as weather updates.
