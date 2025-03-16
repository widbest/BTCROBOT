import streamlit as st
import time
from datetime import datetime, timedelta
import pandas as pd
from news_analyzer import NewsAnalyzer
from price_analyzer import PriceAnalyzer
from signal_generator import SignalGenerator
from elliott_wave_analyzer import ElliottWaveAnalyzer
from utils import initialize_session_state

# Page config
st.set_page_config(
    page_title="محلل البيتكوين الذكي",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
initialize_session_state()

# Add smoother auto-refresh every second for real-time updates
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

# تأكيد التحديث كل ثانية بالضبط مع تحديد حد أقصى للتحديثات
refresh_interval = 1.0  # ثانية واحدة
max_updates_per_minute = 30  # الحد الأقصى للتحديثات في الدقيقة

# حساب عدد التحديثات في الدقيقة الحالية
if 'updates_this_minute' not in st.session_state:
    st.session_state.updates_this_minute = 0
    st.session_state.last_minute = int(time.time() / 60)

current_minute = int(time.time() / 60)
if current_minute > st.session_state.last_minute:
    st.session_state.updates_this_minute = 0
    st.session_state.last_minute = current_minute

# التحديث إذا لم يتم تجاوز الحد الأقصى
if (time.time() - st.session_state.last_refresh >= refresh_interval and 
    st.session_state.updates_this_minute < max_updates_per_minute):
    st.session_state.last_refresh = time.time()
    st.session_state.updates_this_minute += 1
    time.sleep(0.1)  # تأخير بسيط لمنع الاستخدام المفرط للمعالج
    st.rerun()

# Create instances of our analyzers
price_analyzer = PriceAnalyzer()
signal_generator = SignalGenerator()
elliott_analyzer = ElliottWaveAnalyzer()

# التأكد من إنشاء محلل الأخبار بشكل صحيح مع إمكانية إدارة الأخطاء
try:
    news_analyzer = NewsAnalyzer()
    if not hasattr(news_analyzer, 'api_key') or not news_analyzer.api_key:
        st.sidebar.warning("⚠️ تنبيه: مفتاح API للأخبار غير متوفر - بعض الميزات قد لا تعمل")
        print("تنبيه: تم إنشاء محلل الأخبار ولكن مفتاح API غير متوفر")
except Exception as e:
    error_msg = f"خطأ في إنشاء محلل الأخبار: {str(e)}"
    st.sidebar.error(error_msg)
    print(error_msg)
    news_analyzer = None

# Main title
st.title("🤖 محلل البيتكوين الذكي")

# Initialize updates counter
if 'updates_count' not in st.session_state:
    st.session_state.updates_count = 0
st.session_state.updates_count += 1

# Display current time with milliseconds, updates count and seconds counter
now = datetime.now()
st.write(f"آخر تحديث: {now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

# إضافة عداد للثواني
if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()
seconds_running = int((now - st.session_state.start_time).total_seconds())

col1, col2 = st.columns(2)
with col1:
    st.write(f"⏱️ وقت التشغيل: {seconds_running} ثانية")
with col2:
    st.write(f"🔄 عدد التحديثات: {st.session_state.updates_count}")

# Auto reset stats every hour
if 'last_reset' not in st.session_state:
    st.session_state.last_reset = datetime.now()

if (datetime.now() - st.session_state.last_reset) > timedelta(hours=1):
    st.session_state.accuracy = 98.0
    st.session_state.total_signals = 0
    st.session_state.predictions = []
    st.session_state.last_market_state = None
    st.session_state.last_reset = datetime.now()
    st.session_state.updates_count = 0

# Sidebar
with st.sidebar:
    st.header("إحصائيات النظام")
    st.metric("دقة التوقعات", f"{st.session_state.accuracy:.1f}%")
    st.metric("عدد التوصيات الناجحة", st.session_state.total_signals)

    # Add confidence threshold control
    confidence_threshold = st.slider(
        "مستوى الثقة المطلوب للإشارات",
        min_value=0.1,
        max_value=0.9,
        value=0.2,
        step=0.1
    )
    signal_generator.confidence_threshold = confidence_threshold

# Main content
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📈 سعر البيتكوين الحالي")
    current_price = price_analyzer.get_current_price()
    price_change = price_analyzer.get_price_change()
    st.metric(
        "BTC/USD",
        f"${current_price:,.2f}",
        delta=f"{price_change:.2f}%"
    )

with col2:
    st.subheader("📊 حالة السوق")
    market_state = price_analyzer.get_market_state()

    # Check for market state change
    if 'last_market_state' not in st.session_state:
        st.session_state.last_market_state = market_state
    elif st.session_state.last_market_state != market_state:
        st.warning(f"⚠️ تنبيه: تغير اتجاه السوق من {st.session_state.last_market_state} إلى {market_state}")
        st.session_state.last_market_state = market_state

    state_color = {
        'صاعد': 'green',
        'هابط': 'red',
        'محايد': 'orange'
    }

    state_emoji = {
        'صاعد': '⬆️',
        'هابط': '⬇️',
        'محايد': '↔️'
    }

    st.markdown(f"<h2 style='color: {state_color[market_state]};'>{state_emoji[market_state]} {market_state}</h2>", unsafe_allow_html=True)

    # عرض اتجاه الشموع للإطارات الزمنية المختلفة بشكل محسن
    if hasattr(price_analyzer, 'technical_indicators') and 'candle_trends' in price_analyzer.technical_indicators:
        candle_trends = price_analyzer.technical_indicators['candle_trends']
        
        st.markdown("### 🕯️ اتجاه الشموع - تحديث كل ثانية")
        
        # إنشاء جدول لعرض اتجاه الشموع
        candle_data = []
        for timeframe, data in candle_trends.items():
            emoji = "🟢" if data['color'] == 'أخضر' else "🔴"
            direction = data['direction']
            consecutive = data['consecutive_count']
            candle_data.append([timeframe, f"{emoji} {direction}", consecutive])
        
        # تحويل البيانات إلى DataFrame
        candle_df = pd.DataFrame(candle_data, columns=["الإطار الزمني", "الاتجاه", "عدد الشموع المتتالية"])
        
        # تغيير أسماء الإطارات الزمنية لتكون أكثر وضوحاً
        candle_df = candle_df.replace({
            "1min": "دقيقة",
            "15min": "15 دقيقة",
            "1hour": "ساعة",
            "1day": "يوم"
        })
        
        # عرض الجدول مع تحسين الشكل باستخدام CSS
        st.markdown("""
        <style>
        .highlight-green {
            background-color: rgba(0, 255, 0, 0.15);
            border-left: 5px solid green;
            padding: 10px;
            border-radius: 5px;
        }
        .highlight-red {
            background-color: rgba(255, 0, 0, 0.15);
            border-left: 5px solid red;
            padding: 10px;
            border-radius: 5px;
        }
        .time-label {
            font-weight: bold;
            margin-bottom: 5px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.table(candle_df)
        
        # إظهار ملخص للاتجاه العام بناءً على الأطر الزمنية المختلفة
        up_frames = sum(1 for data in candle_trends.values() if data['direction'] == 'صاعدة')
        down_frames = sum(1 for data in candle_trends.values() if data['direction'] == 'نازلة')
        
        if up_frames > down_frames:
            st.markdown("<div class='highlight-green'>🔔 الاتجاه العام: صاعد في معظم الأطر الزمنية</div>", unsafe_allow_html=True)
        elif down_frames > up_frames:
            st.markdown("<div class='highlight-red'>🔔 الاتجاه العام: هابط في معظم الأطر الزمنية</div>", unsafe_allow_html=True)
        else:
            st.markdown("🔔 الاتجاه العام: متعادل بين الصعود والهبوط")
        
        # إظهار تنبيهات إضافية لأنماط مهمة
        for timeframe, data in candle_trends.items():
            if data['consecutive_count'] >= 3:
                direction = data['direction']
                timeframe_name = {"1min": "دقيقة", "15min": "15 دقيقة", "1hour": "ساعة", "1day": "يوم"}.get(timeframe, timeframe)
                
                if direction == "صاعدة":
                    st.markdown(f"<div class='highlight-green'>⚠️ تنبيه: {data['consecutive_count']} شموع {direction} متتالية على الإطار الزمني {timeframe_name}!</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='highlight-red'>⚠️ تنبيه: {data['consecutive_count']} شموع {direction} متتالية على الإطار الزمني {timeframe_name}!</div>", unsafe_allow_html=True)

    # Show technical indicators
    if hasattr(price_analyzer, 'technical_indicators'):
        ti = price_analyzer.technical_indicators
        st.write("المؤشرات الفنية:")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("RSI", f"{ti['rsi']:.1f}")
            st.metric("ADX", f"{ti['adx']:.1f}")
        with col2:
            st.metric("MACD", f"{ti['macd']:.2f}")
            st.metric("MFI", f"{ti['mfi']:.1f}")

with col3:
    st.subheader("📰 تحليل الأخبار")
    try:
        if news_analyzer and hasattr(news_analyzer, 'get_sentiment'):
            news_sentiment = news_analyzer.get_sentiment()
            sentiment_emoji = "🟢" if news_sentiment > 0 else "🔴" if news_sentiment < 0 else "⚪"
            st.write(f"مؤشر المشاعر: {sentiment_emoji} {news_sentiment:.2f}")
        else:
            st.warning("📰 محلل الأخبار غير متاح حالياً")
            news_sentiment = 0
    except Exception as e:
        st.error(f"خطأ في تحليل الأخبار: {str(e)}")
        news_sentiment = 0

# Generate and display signal
st.header("🎯 إشارة التداول")
signal = signal_generator.generate_signal(current_price, news_sentiment, market_state, price_analyzer, elliott_analyzer)

# قسم قرارات الدخول التلقائية بناءً على اتجاه السوق
st.header("⚡ قرار الدخول التلقائي")

# إنشاء مخزن للصفقات في session_state إذا لم يكن موجوداً
if 'active_trades' not in st.session_state:
    st.session_state.active_trades = []
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []

# إعطاء قرار الدخول التلقائي بناءً على اتجاه السوق
auto_decision = {
    "action": "انتظار",
    "entry_price": current_price,
    "target_price": current_price * 1.02,  # هدف افتراضي 2%
    "stop_loss": current_price * 0.98,     # وقف خسارة افتراضي 2%
    "timestamp": datetime.now(),
    "market_state": market_state
}

# اتخاذ قرار بناءً على حالة السوق
if market_state == "صاعد":
    auto_decision["action"] = "شراء"
    auto_decision["target_price"] = round(current_price * 1.03, 2)  # هدف 3%
    auto_decision["stop_loss"] = round(current_price * 0.985, 2)   # وقف خسارة 1.5%
    auto_decision["reason"] = "دخول تلقائي ⬆️: السوق صاعد"
    auto_color = "green"
elif market_state == "هابط":
    auto_decision["action"] = "بيع"
    auto_decision["target_price"] = round(current_price * 0.97, 2)  # هدف 3%
    auto_decision["stop_loss"] = round(current_price * 1.015, 2)    # وقف خسارة 1.5%
    auto_decision["reason"] = "دخول تلقائي ⬇️: السوق هابط"
    auto_color = "red"
else:
    auto_decision["reason"] = "انتظار: السوق غير محدد الاتجاه"
    auto_color = "gray"

# عرض قرار الدخول التلقائي بشكل واضح
if auto_decision["action"] != "انتظار":
    st.markdown(f"""
    <div style="padding: 15px; border-radius: 10px; background-color: {'rgba(0, 255, 0, 0.1)' if auto_decision['action'] == 'شراء' else 'rgba(255, 0, 0, 0.1)'}; margin-bottom: 20px;">
        <h3 style="color: {auto_color};">{auto_decision['action']} الآن عند السعر ${current_price:,.2f}</h3>
        <p>⏱️ وقت الإشارة: {auto_decision['timestamp'].strftime('%H:%M:%S')}</p>
        <p>📈 السعر المستهدف: ${auto_decision['target_price']:,.2f} | الربح المتوقع: {abs((auto_decision['target_price']/current_price - 1) * 100):,.1f}%</p>
        <p>🛑 وقف الخسارة: ${auto_decision['stop_loss']:,.2f} | الخسارة المتوقعة: {abs((auto_decision['stop_loss']/current_price - 1) * 100):,.1f}%</p>
        <p>ℹ️ السبب: {auto_decision['reason']}</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info(f"⏳ {auto_decision['reason']}")

# عرض إشارة نظام التحليل أيضاً
if signal["action"] != "انتظار":
    st.success(f"""
    ⚡ إشارة تداول من نظام التحليل!

    {signal['action']} الآن عند السعر ${current_price:,.2f}

    📈 الهدف: ${signal['target_price']:,.2f}
    🎯 الربح المتوقع: {abs((signal['target_price']/current_price - 1) * 100):,.1f}%
    🛑 وقف الخسارة: ${signal['stop_loss']:,.2f}
    💫 الخسارة المتوقعة: {abs((signal['stop_loss']/current_price - 1) * 100):,.1f}%

    ✨ نسبة النجاح المتوقعة: {signal['confidence']*100:.1f}%
    """)

st.markdown(f"### {signal['action']}")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("السعر المستهدف", f"${signal['target_price']:,.2f}")
with col2:
    st.metric("وقف الخسارة", f"${signal['stop_loss']:,.2f}")
with col3:
    st.metric("مستوى الثقة", f"{signal.get('confidence', 0)*100:.1f}%")
st.write(f"السبب: {signal['reason']}")

# Recent news with sentiment analysis
st.header("📰 آخر الأخبار المؤثرة")
try:
    if news_analyzer and hasattr(news_analyzer, 'get_recent_news'):
        news_items = news_analyzer.get_recent_news()
        if news_items:
            for news in news_items:
                sentiment_color = 'green' if news['sentiment'] > 0 else 'red' if news['sentiment'] < 0 else 'gray'
                with st.expander(f"{news['title']} ({news['sentiment']:.2f})"):
                    st.write(news['description'])
                    st.write(f"المصدر: {news['source']} | التاريخ: {news['date']}")
        else:
            st.info("لا توجد أخبار حديثة متاحة حالياً")
    else:
        st.warning("📰 خدمة الأخبار غير متاحة حالياً")
except Exception as e:
    st.error(f"خطأ في عرض الأخبار: {str(e)}")

# Add Elliott Wave Analysis section
st.header("🌊 تحليل موجات إليوت")

# Perform Elliott Wave analysis
wave_state = elliott_analyzer.get_current_wave_state()
wave_prediction = elliott_analyzer.get_wave_prediction()

if wave_state:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("حالة الموجة الحالية")
        st.markdown(f"""
        - **الموجة الحالية:** {wave_state.get('current_wave', 'غير محدد')}
        - **المرحلة:** {wave_state.get('current_phase', 'غير محدد')}
        - **النمط:** {wave_state.get('pattern', 'غير محدد')}
        - **نسبة الثقة:** {wave_state.get('confidence', 0)*100:.1f}%
        """)
    
    with col2:
        st.subheader("التوقع المستقبلي")
        move_color = "green" if wave_prediction['prediction'] == 'صاعد' else "red" if wave_prediction['prediction'] == 'هابط' else "orange"
        
        st.markdown(f"""
        - **الحركة المتوقعة:** <span style='color:{move_color};'>{wave_prediction['prediction']}</span>
        - **الهدف السعري:** ${wave_prediction['wave_target']:,.2f}
        - **التغير المتوقع:** {wave_prediction['target_move']*100:.1f}%
        - **نسبة الثقة:** {wave_prediction['confidence']*100:.1f}%
        """, unsafe_allow_html=True)
    
    # Show Elliott Wave explanation
    with st.expander("🔍 شرح نظرية موجات إليوت"):
        st.markdown("""
        ### نظرية موجات إليوت
        
        نظرية موجات إليوت هي تقنية تحليل فني طورها رالف نيلسون إليوت في الثلاثينيات. تشرح هذه النظرية تحركات أسعار السوق باعتبارها انعكاسًا لنفسية المستثمر الجماعية، وتتكون من:
        
        #### الدورة الكاملة: 8 موجات
        - **5 موجات دافعة** (1-2-3-4-5) في اتجاه الترند الرئيسي
        - **3 موجات تصحيحية** (A-B-C) عكس اتجاه الترند الرئيسي
        
        #### خصائص الموجات الدافعة:
        - الموجات 1، 3، 5 في اتجاه الترند الرئيسي
        - الموجات 2، 4 تصحيحية عكس الترند
        - الموجة 3 عادة الأطول والأقوى
        - الموجة 5 غالباً ما تظهر علامات ضعف
        
        #### خصائص الموجات التصحيحية:
        - الموجات A، C في عكس اتجاه الترند
        - الموجة B في اتجاه الترند الرئيسي
        
        هذه الأنماط تتكرر على مقاييس مختلفة (فرامات مختلفة) من الرسوم البيانية طويلة الأجل إلى فترات قصيرة الأجل.
        """)

# Historical predictions
st.header("📊 سجل التوصيات السابقة")
if st.session_state.predictions:
    df = pd.DataFrame(st.session_state.predictions)
    st.dataframe(df)