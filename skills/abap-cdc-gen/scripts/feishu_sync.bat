@echo off
REM Sync Feishu Bitable checklist to local markdown file
REM Called by Windows Task Scheduler or can be run manually

python "%~dp0feishu_sync.py"