@echo off
:: Si sposta nella cartella dove si trova questo file .bat
cd /d "%~dp0"

:: Attiva conda e l'ambiente "dati"
call C:\Users\pfrapoli\AppData\Local\miniconda3\Scripts\activate.bat dati

:: Lancia l'app
streamlit run App.py

:: Lascia la finestra aperta in caso di errore
pause