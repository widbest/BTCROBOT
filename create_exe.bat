
@echo off
echo ===== تحويل محلل بيتكوين إلى ملف تنفيذي EXE =====
echo.

REM تأكد من تثبيت Python أولاً
python --version >nul 2>&1
if errorlevel 1 (
    echo خطأ: يرجى تثبيت Python (الإصدار 3.11 أو أحدث) أولاً.
    echo يمكنك تنزيله من: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 1. تثبيت متطلبات النظام...
python -m pip install --upgrade pip
python -m pip install --no-warn-script-location pyinstaller
python -m pip install --no-warn-script-location -r requirements.txt

REM تحميل موارد nltk اللازمة
echo 2. تحميل موارد اللغة الضرورية...
python -c "import nltk; nltk.download('vader_lexicon', quiet=True)"
echo.

echo 3. جاري إنشاء ملف التنفيذ... (قد تستغرق هذه العملية بضع دقائق)
if not exist "generated-icon.png" (
    echo لم يتم العثور على أيقونة، سيتم استخدام الأيقونة الافتراضية
)

REM حذف أي ملفات سابقة
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM إنشاء ملف EXE
pyinstaller --clean --noconfirm --onefile ^
    --add-data "%APPDATA%\nltk_data;nltk_data" ^
    --name "BTC-Analyzer" ^
    --icon=generated-icon.png ^
    --noconsole ^
    Bitcoin_Analyzer.py

if exist "dist\BTC-Analyzer.exe" (
    echo.
    echo تم إنشاء الملف التنفيذي بنجاح!
    echo يمكنك العثور على الملف التنفيذي في مجلد dist
    echo.
    
    REM نسخ الملفات المهمة لمجلد التنفيذ
    echo 4. نسخ الملفات المطلوبة...
    copy requirements.txt dist\
    copy main.py dist\
    copy price_analyzer.py dist\
    copy signal_generator.py dist\
    copy elliott_wave_analyzer.py dist\
    copy news_analyzer.py dist\
    copy utils.py dist\
    if exist ".streamlit" xcopy /E /I ".streamlit" "dist\.streamlit"
    
    echo 5. إنشاء اختصار لتشغيل التطبيق...
    echo @echo off > "dist\تشغيل المحلل.bat"
    echo start BTC-Analyzer.exe >> "dist\تشغيل المحلل.bat"
    
    echo.
    echo ملفات التطبيق جاهزة! اضغط مرتين على BTC-Analyzer.exe لتشغيل التطبيق.
) else (
    echo حدث خطأ أثناء إنشاء الملف التنفيذي.
    echo تحقق من سجل الأخطاء للمزيد من المعلومات.
)

echo.
echo جاري فتح مجلد الملفات...
start dist

pause
