@echo off

echo Activating Conda environment...
call C:\Users\Ayush\anaconda3\Scripts\activate.bat jarvis2


echo Running the news fetch script...
python news_fetch.py

echo Running the price fetch script...
python price_pred.py

echo Running the assistant script...
python main_assistant.py

exit
