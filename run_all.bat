@echo off

REM Load environment variables from .env file
for /f "tokens=1,2 delims==" %%A in ('type .env') do (
    if "%%A"=="CONDA_PATH" set CONDA_PATH=%%B
    if "%%A"=="CONDA_ENV" set CONDA_ENV=%%B
)

echo Activating Conda environment...
call %CONDA_PATH% %CONDA_ENV%

echo Running the news fetch script...
python news_fetch.py

echo Running the price fetch script...
python price_pred.py

echo Running the assistant script...
python main_assistant.py

exit
