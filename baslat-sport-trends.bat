@echo off
echo Sport Trends Marketing Agent baslatiliyor...
echo.

echo [1/3] Docker container'lari baslatiliyor...
cd /d "C:\Users\Legen\OneDrive\Desktop\marketing_manager\sportagent"
docker compose up -d
timeout /t 5

echo.
echo [2/3] Backend baslatiliyor (yeni pencere)...
start "Sport Trends Backend" cmd /k "cd /d C:\Users\Legen\OneDrive\Desktop\marketing_manager\sportagent\backend && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

timeout /t 5

echo.
echo [3/3] Frontend baslatiliyor (yeni pencere)...
start "Sport Trends Frontend" cmd /k "cd /d C:\Users\Legen\OneDrive\Desktop\marketing_manager\sportagent\frontend && npx next dev"

timeout /t 10

echo.
echo Tamam! Tarayicida aciliyor...
start http://localhost:3000

echo.
echo Backend log'unu gormek icin "Sport Trends Backend" penceresine bak.
echo Kapatmak icin: docker compose down + iki pencereyi de kapat.
pause