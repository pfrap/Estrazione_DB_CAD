@echo off
:: Si sposta nella cartella dove si trova questo file .bat
cd /d "%~dp0"

:: Lancia l'app
streamlit run App.py

:: Lascia la finestra aperta in caso di errore (opzionale)
pause