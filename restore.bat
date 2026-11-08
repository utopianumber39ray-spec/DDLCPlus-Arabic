@echo off
title DDLC+ Arabic Patch - Restore
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0restore.ps1"
if errorlevel 1 pause
exit /b %errorlevel%
