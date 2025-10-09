@echo off
echo Deploying Cross-Modal Moderator to AWS...
cd /d %~dp0..\src

sam build
sam deploy --guided

echo ✅ Deployment complete!
pause