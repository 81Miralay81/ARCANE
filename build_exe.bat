@echo off
chcp 65001 >nul
echo Kanatix Arcade - EXE olusturuluyor...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name KanatixArcade --icon assets\icon.ico --add-data "assets;assets" main.py
echo.
echo Hazir: dist\KanatixArcade.exe
pause
