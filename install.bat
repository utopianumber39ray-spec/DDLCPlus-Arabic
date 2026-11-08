@echo off
title DDLC+ Arabic Patch - Installer
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 pause
exit /b %errorlevel%
