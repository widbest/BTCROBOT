
import os
from datetime import datetime, timedelta
import requests
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import streamlit as st
import pandas as pd

class NewsAnalyzer:
    def __init__(self):
    # تحسين التعامل مع مفتاح API
    try:
        # Add the API key directly in the code
        self.api_key = "6139e3c32b244a60921dae43dd16e73f"
        
        # Keep the original code for fallback (in case you want to change the key later via environment variables)
        if not self.api_key:
            self.api_key = os.getenv("NEWS_API_KEY")
            if not self.api_key and hasattr(st, 'secrets') and "NEWS_API_KEY" in st.secrets:
                self.api_key = st.secrets["NEWS_API_KEY"]
        
        if not self.api_key:
            print("⚠️ مفتاح API للأخبار غير متوفر")
            self.api_key = None
        
        # تهيئة NLTK
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('vader_lexicon')

        self.sia = SentimentIntensityAnalyzer()
        self.cached_sentiment = 0
        self.last_update = datetime.now() - timedelta(hours=1)  # لضمان التحديث الأول
        
        # تهيئة مخزن الأخبار
        self.news_cache = []
        self.last_fetch = None
        self.cache_duration = timedelta(minutes=15)
    except Exception as e:
        print(f"خطأ في تهيئة محلل الأخبار: {str(e)}")
        self.api_key = None

    def get_sentiment(self):
        """الحصول على تحليل المشاعر من الأخبار"""
        try:
            # التحقق مما إذا كان يجب تحديث التحليل
            now = datetime.now()
            if (now - self.last_update) < timedelta(minutes=15):
                return self.cached_sentiment

            # تحليل الأخبار الجديدة
            news = self.get_recent_news()
            if not news:
                return 0

            # حساب المشاعر المرجحة بالوقت
            total_weight = 0
            weighted_sentiment = 0
            now = datetime.now()

            for article in news:
                article_time = datetime.strptime(article['date'], "%Y-%m-%d %H:%M")
                time_diff = (now - article_time).total_seconds() / 3600  # ساعات

                # الأخبار الأحدث تحصل على وزن أعلى
                weight = 1 / (1 + time_diff)
                weighted_sentiment += article['sentiment'] * weight
                total_weight += weight

            if total_weight > 0:
                self.cached_sentiment = weighted_sentiment / total_weight
                self.last_update = datetime.now()
            else:
                # لأغراض العرض، نعود بقيمة محايدة
                self.cached_sentiment = 0
                self.last_update = datetime.now()

            return self.cached_sentiment
        except Exception as e:
            print(f"خطأ في تحليل المشاعر: {str(e)}")
            return 0

    def get_recent_news(self):
        """جلب أخبار بيتكوين الحديثة مع التخزين المؤقت"""
        now = datetime.now()

        # التحقق من وجود مفتاح API
        if not self.api_key:
            return []

        # إعادة الأخبار المخزنة مؤقتًا إذا كانت لا تزال صالحة
        if self.last_fetch and (now - self.last_fetch) < self.cache_duration:
            return self.news_cache

        endpoint = "https://newsapi.org/v2/everything"
        params = {
            "q": "(bitcoin OR btc OR cryptocurrency) AND (price OR trading OR market)",
            "language": "en",
            "sortBy": "publishedAt",
            "apiKey": self.api_key,
            "from": (now - timedelta(days=1)).strftime("%Y-%m-%d")
        }

        try:
            # اضافة timeout لتجنب تعليق البرنامج
            response = requests.get(endpoint, params=params, timeout=10)
            
            # التعامل مع أخطاء الاستجابة
            if response.status_code != 200:
                print(f"خطأ في API الأخبار: كود الاستجابة {response.status_code}")
                return self.news_cache if self.news_cache else []
                
            data = response.json()
            
            if "articles" not in data or not data["articles"]:
                print("لم يتم العثور على مقالات")
                return []
                
            articles = data["articles"][:10]  # الحصول على أفضل 10 مقالات

            processed_articles = []
            for article in articles:
                # تجنب الخطأ في حالة عدم وجود حقول مطلوبة
                if not all(k in article for k in ["title", "description", "source", "publishedAt"]):
                    continue
                if not article["title"] or not article["description"]:
                    continue
                    
                try:
                    processed_articles.append({
                        "title": article["title"],
                        "description": article["description"],
                        "source": article["source"]["name"],
                        "date": datetime.strptime(article["publishedAt"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M"),
                        "sentiment": self._analyze_sentiment(f"{article['title']} {article['description']}")
                    })
                except Exception as e:
                    print(f"خطأ في معالجة المقال: {str(e)}")
                    continue

            # تحديث المخزن المؤقت
            self.news_cache = processed_articles
            self.last_fetch = now

            return processed_articles
        except Exception as e:
            print(f"خطأ في جلب الأخبار: {str(e)}")
            return self.news_cache if self.news_cache else []

    def _analyze_sentiment(self, text):
        """تحليل مشاعر النص مع سياق أكثر"""
        sentiment = self.sia.polarity_scores(text)

        # إضافة وزن إلى الكلمات المهمة
        bullish_words = ['surge', 'rally', 'jump', 'gain', 'bull', 'bullish', 'rise']
        bearish_words = ['crash', 'fall', 'drop', 'decline', 'bear', 'bearish', 'sink']

        text_lower = text.lower()
        for word in bullish_words:
            if word in text_lower:
                sentiment['compound'] += 0.1
        for word in bearish_words:
            if word in text_lower:
                sentiment['compound'] -= 0.1

        # تطبيع النتيجة النهائية
        sentiment['compound'] = max(min(sentiment['compound'], 1.0), -1.0)
        return sentiment['compound']
