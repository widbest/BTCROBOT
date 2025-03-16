
@echo off
echo ===== إعداد محلل بيتكوين =====
echo.

REM تحقق من وجود Python
python --version >nul 2>&1
if errorlevel 1 (
    echo خطأ: لم يتم العثور على Python.
    echo يرجى تثبيت Python (الإصدار 3.11 أو أحدث) من: https://www.python.org/downloads/
    echo تأكد من تفعيل خيار "Add Python to PATH" أثناء التثبيت
    pause
    exit /b 1
)

echo تم العثور على Python. جاري إعداد البيئة...
echo.

REM تحديث pip
echo 1. تحديث أداة pip...
python -m pip install --upgrade pip

REM تثبيت المكتبات المطلوبة
echo 2. تثبيت المكتبات المطلوبة...
python -m pip install -r requirements.txt

REM تثبيت مكتبات إضافية للتأكد من عمل التطبيق
echo 3. تثبيت مكتبات إضافية...
python -m pip install streamlit pandas-ta yfinance requests nltk scikit-learn numpy scipy

REM تحميل موارد NLTK
echo 4. تحميل موارد اللغة الضرورية...
python -c "import nltk; nltk.download('vader_lexicon', quiet=True)"

echo.
echo تم إعداد البيئة بنجاح!
echo.
echo لتشغيل التطبيق، قم بتشغيل ملف run_app.bat
echo.

pause
