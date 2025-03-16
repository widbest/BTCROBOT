
@echo off
echo ===== تشغيل محلل بيتكوين =====
echo.

REM تأكد من تثبيت Python أولاً
python --version >nul 2>&1
if errorlevel 1 (
    echo خطأ: يرجى تثبيت Python (الإصدار 3.11 أو أحدث) أولاً.
    echo يمكنك تنزيله من: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo جاري بدء تشغيل التطبيق...
echo.
echo سيتم فتح التطبيق في المتصفح تلقائياً.
echo.
echo (اضغط Ctrl+C لإيقاف التطبيق)
echo.

REM إضافة تأخير قصير قبل فتح المتصفح
timeout /t 2 /nobreak > nul

REM فتح المتصفح بعد فترة قصيرة
start http://localhost:8501

REM تشغيل التطبيق
streamlit run main.py --server.port=8501 --server.address=localhost

pause
