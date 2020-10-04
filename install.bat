REM Install USBEventManager on Windows 10
REM https://github.com/gestas/USBEventManager

SETLOCAL ENABLEEXTENSIONS
ECHO "Installing USBEventManager..."

SET _PROJECT_DIR=%~dp0
SET _APP="USBEventManager"
SET _BIN_DIR="%USERPROFILE\bin\%_APP\"
SET _START_SCRIPT_PATH="%_BIN_DIR\%_APP.bat"
SET _FINAL_CONFIG_PATH="%_BIN_DIR\usbeventmanager.yml"
SET _SOURCE_CONFIG_FILE="%_PROJECT_DIR\errata\usbeventmanager.yml"

IF NOT EXIST "%_BIN_DIR" (
    mkdir "%_BIN_DIR"
    )

WHERE virtualenv
IF "%ERRORLEVEL" NEQ "0" (
    ECHO "virtualenv is required."
    ECHO "Installation documentation - https://pypi.org/project/virtualenv/1.7.1.2/"
    EXIT /B 1
    )

WHERE py
IF "%ERRORLEVEL" NEQ "0" (
    ECHO "py is required."
    EXIT /B 1
    )

ECHO Creating the start script at %_START_SCRIPT_PATH
@ECHO OFF
ECHO REM Activates the virtualenv then starts USBEventManager. > %_START_SCRIPT_PATH
ECHO REM Allows us to run in a virtualenv as Administrator. >> %_START_SCRIPT_PATH
ECHO cd %_PROJECT_DIR >> %_START_SCRIPT_PATH
ECHO .\env\Scripts\activate >> %_START_SCRIPT_PATH
ECHO runas /trustlevel:0x20000 python ./%_APP/usbeventmanager.py %* >> %_START_SCRIPT_PATH
@ECHO ON

ECHO Creating and activating a new Python 3.8 virtualenv
py -3.8 -m venv %_PROJECT_DIR
.\env\Scripts\activate

REM We need the newest version of setuptools to avoid a "AttributeError: install_layout" error
pip install --upgrade setuptools
REM Install USBEventManager
pip install %_PROJECT_DIR

REM Copy the source config file if required
IF NOT EXIST %_FINAL_CONFIG_PATH" (
    cp %_SOURCE_CONFIG_FILE %_FINAL_CONFIG_PATH
    )

ECHO " "
ECHO "Setup complete."
ECHO " "

@ECHO OFF
SET /p LEARN="Do you want to add devices to the default whitelist? Yes/No"
IF x%LEARN:y=%==x%LEARN (
    CMD %_START_SCRIPT_PATH learn

SET /p AUTO="Do you want to start USBEventManager automatically? Yes/No"
IF x%AUTO:n=%==x"%AUTO" (
    CMD runas /trustlevel:0x20000 %_START_SCRIPT_PATH automatic-start
@ECHO ON
EXIT /B 0