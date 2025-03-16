
# تشغيل تطبيق محلل البيتكوين في Visual Studio Code
import os
import sys
import streamlit.web.cli as stcli

# تشغيل تطبيق Streamlit
sys.argv = ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
stcli.main()
