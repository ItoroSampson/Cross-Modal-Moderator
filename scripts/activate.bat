@echo off
echo Activating Lambda Python 3.11 Environment...
cd /d %~dp0..\
call lambda-env\Scripts\activate.bat
echo ✅ Now using Python 3.11 for AWS Lambda development
echo 📁 Project: cross-modal-moderator
cmd /k