
import os
import sys
import time
import threading
import webbrowser
import subprocess
import traceback

def resource_path(relative_path):
    """ توفير المسار المطلق للموارد للتعامل مع PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def open_browser():
    time.sleep(3)  # انتظار لفترة أطول للتأكد من بدء التطبيق
    try:
        webbrowser.open("http://localhost:8501")
        print("تم فتح المتصفح!")
    except Exception as e:
        print(f"خطأ في فتح المتصفح: {e}")

def show_welcome():
    print("=" * 50)
    print("مرحباً بك في محلل البيتكوين الذكي!")
    print("جاري تشغيل التطبيق... يرجى الانتظار")
    print("سيتم فتح المتصفح تلقائياً خلال ثوان...")
    print("=" * 50)

def check_requirements():
    # التحقق من وجود المكتبات الضرورية
    required_modules = ["streamlit", "pandas", "numpy", "nltk", "requests", "yfinance"]
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"تنبيه: المكتبات التالية غير موجودة: {', '.join(missing_modules)}")
        print("جاري تثبيت المكتبات المطلوبة...")
        
        for module in missing_modules:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module])
                print(f"تم تثبيت {module}")
            except Exception as e:
                print(f"خطأ في تثبيت {module}: {e}")
                return False
    
    return True

def main():
    # عرض رسالة الترحيب
    show_welcome()
    
    try:
        # التحقق من وجود المكتبات المطلوبة
        if not check_requirements():
            print("يرجى تثبيت المكتبات المطلوبة يدوياً باستخدام setup_windows.bat")
            input("اضغط Enter للخروج...")
            return
        
        # تهيئة NLTK
        try:
            import nltk
            nltk.download('vader_lexicon', quiet=True)
        except Exception as e:
            print(f"خطأ في تهيئة NLTK: {e}")
            print("سيتم محاولة المتابعة...")
        
        # جلب مسار ملف main.py
        main_path = resource_path("main.py")
        if not os.path.exists(main_path):
            print(f"خطأ: لم يتم العثور على الملف {main_path}")
            print("المسار الحالي:", os.getcwd())
            print("محتويات المجلد:", os.listdir("."))
            input("اضغط Enter للخروج...")
            return
        
        print(f"جاري تشغيل Streamlit مع الملف: {main_path}")
        
        # تشغيل المتصفح في خلفية تشغيل التطبيق
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # تشغيل تطبيق Streamlit
        import streamlit.web.cli as stcli
        
        sys.argv = ["streamlit", "run", main_path, "--server.port=8501", "--server.address=localhost"]
        sys.exit(stcli.main())
        
    except Exception as e:
        print(f"خطأ في تشغيل التطبيق: {e}")
        print("تفاصيل الخطأ:")
        traceback.print_exc()
        input("اضغط Enter للخروج...")

if __name__ == "__main__":
    main()
