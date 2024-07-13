@echo off

:: Directory of the script
set script_dir=%~dp0

:: Activate the virtual environment
call %script_dir%Windows\Scripts\activate

:: Change directory to where your app.py is located
cd /d %script_dir%

:: Start your app.py script
python app.py

:: Deactivate the virtual environment
deactivate
