@echo off
set DEEPFIND_PORT=8888
set DEEPFIND_USER_DATA_DIR=%~dp0test_data
set DEEPFIND_CONTROL_TOKEN=secret_token_123
set DEEPFIND_INSTANCE_ID=instance_abc
echo Starting backend...
"engine\dist\deepfind-engine\deepfind-engine.exe"
