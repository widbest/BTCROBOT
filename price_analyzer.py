import yfinance as yf
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

class PriceAnalyzer:
    def __init__(self):
        self.symbol = "BTC-USD"
        self.price_cache = {}
        self.cache_duration = timedelta(milliseconds=100)  # Ultra-fast updates
        self.model = None
        self.last_training = None
        self.training_interval = timedelta(hours=1)
        self.scaler = StandardScaler()

    def get_current_price(self):
        """Get current Bitcoin price with ultra-fast updates"""
        now = datetime.now()

        # Return cached price if still valid
        if 'price' in self.price_cache and (now - self.price_cache['time']) < self.cache_duration:
            return self.price_cache['price']

        try:
            btc = yf.Ticker(self.symbol)
            price = btc.info['regularMarketPrice']

            # Update cache
            self.price_cache = {
                'price': price,
                'time': now
            }
            return price
        except Exception as e:
            st.error(f"خطأ في جلب السعر: {str(e)}")
            return self.price_cache.get('price', 0)

    def _calculate_indicators(self, hist):
        """Calculate enhanced technical indicators"""
        # Trend Indicators
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['EMA_12'] = hist['Close'].ewm(span=12).mean()
        hist['EMA_26'] = hist['Close'].ewm(span=26).mean()
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA_200'] = hist['Close'].rolling(window=200).mean()

        # Momentum Indicators
        # RSI with smoothing
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(span=14).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(span=14).mean()
        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))

        # Enhanced MACD
        hist['MACD'] = hist['EMA_12'] - hist['EMA_26']
        hist['Signal_Line'] = hist['MACD'].ewm(span=9).mean()
        hist['MACD_Hist'] = hist['MACD'] - hist['Signal_Line']

        # Bollinger Bands with dynamic multiplier
        volatility = hist['Close'].rolling(window=20).std() / hist['Close'].rolling(window=20).mean()
        bb_multiplier = 2 + volatility
        hist['BB_middle'] = hist['Close'].rolling(window=20).mean()
        hist['BB_upper'] = hist['BB_middle'] + bb_multiplier * hist['Close'].rolling(window=20).std()
        hist['BB_lower'] = hist['BB_middle'] - bb_multiplier * hist['Close'].rolling(window=20).std()

        # Enhanced ADX
        tr1 = abs(hist['High'] - hist['Low'])
        tr2 = abs(hist['High'] - hist['Close'].shift())
        tr3 = abs(hist['Low'] - hist['Close'].shift())
        tr = pd.DataFrame([tr1, tr2, tr3]).max()
        hist['TR'] = tr
        
        # تأكد من أن TR لا يحتوي على قيم NaN قبل حساب ATR
        hist['TR'] = hist['TR'].fillna(0)
        
        # حساب ATR
        hist['ATR'] = hist['TR'].rolling(window=14).mean()
        
        # التأكد من أن ATR لا يحتوي على قيم NaN (استخدام قيمة متوسط TR المتاحة)
        hist['ATR'] = hist['ATR'].fillna(hist['TR'].mean())
        
        # تأكد أن ATR ليس صفر أو NaN (لتجنب القسمة على صفر)
        hist['ATR'] = hist['ATR'].replace(0, hist['TR'].mean())

        plus_dm = hist['High'].diff()
        minus_dm = hist['Low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0

        tr14 = hist['TR'].rolling(window=14).sum()
        plus_di14 = 100 * (plus_dm.rolling(window=14).sum() / tr14)
        minus_di14 = 100 * (minus_dm.rolling(window=14).sum() / tr14)
        dx = 100 * abs(plus_di14 - minus_di14) / (plus_di14 + minus_di14)
        hist['ADX'] = dx.rolling(window=14).mean()

        # Volume-based indicators
        hist['OBV'] = (np.sign(hist['Close'].diff()) * hist['Volume']).cumsum()

        # MFI with volume weighting
        typical_price = (hist['High'] + hist['Low'] + hist['Close']) / 3
        raw_money_flow = typical_price * hist['Volume']

        pos_flow = raw_money_flow.where(typical_price > typical_price.shift(1), 0)
        neg_flow = raw_money_flow.where(typical_price < typical_price.shift(1), 0)

        pos_mf = pos_flow.rolling(window=14).sum()
        neg_mf = neg_flow.rolling(window=14).sum()

        hist['MFI'] = 100 - (100 / (1 + (pos_mf / neg_mf)))

        # Trend Strength
        hist['Trend_Strength'] = (
            (hist['Close'] > hist['SMA_20']).astype(int) * 0.3 +
            (hist['Close'] > hist['SMA_50']).astype(int) * 0.3 +
            (hist['Close'] > hist['SMA_200']).astype(int) * 0.4
        )

        return hist

    def _train_model(self, hist):
        """Train enhanced machine learning model"""
        if self.last_training and (datetime.now() - self.last_training) < self.training_interval:
            return

        try:
            # Enhanced feature set
            features = [
                'RSI', 'ADX', 'MFI', 'Trend_Strength',
                'MACD', 'MACD_Hist', 'OBV'
            ]
            X = hist[features].dropna()

            # Create sophisticated target variable
            future_returns = hist['Close'].pct_change(periods=3).shift(-3)  # 3-period future returns
            y = (future_returns > future_returns.rolling(window=20).mean()).dropna().astype(int)
            y = y[:len(X)]

            if len(X) < 100:
                return

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train test split
            X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, shuffle=False)

            # Ensemble model
            rf = RandomForestClassifier(n_estimators=100, max_depth=5)
            gb = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1)

            rf.fit(X_train, y_train)
            gb.fit(X_train, y_train)

            # Use both models
            self.models = {'rf': rf, 'gb': gb}
            self.last_training = datetime.now()

        except Exception as e:
            st.error(f"خطأ في تدريب النموذج: {str(e)}")

    def get_price_change(self):
        """Get price change with enhanced analysis"""
        try:
            btc = yf.Ticker(self.symbol)
            # تحديث الإطار الزمني ليشمل عدة فترات زمنية
            hist_1min = btc.history(period="5d", interval="1m")  # بيانات الدقيقة
            hist_15min = btc.history(period="5d", interval="15m")  # بيانات 15 دقيقة
            hist_1hour = btc.history(period="10d", interval="1h")  # بيانات الساعة
            hist_1day = btc.history(period="30d", interval="1d")  # بيانات اليوم

            if len(hist_1min) < 60:
                return 0

            # التأكد من وجود بيانات كافية
            if len(hist_1min) < 60:
                return 0
                
            # احتساب المؤشرات الفنية
            hist = self._calculate_indicators(hist_1min)

            # Train/update model
            self._train_model(hist)

            # التأكد من وجود بيانات كافية قبل حساب التغير
            try:
                current_price = hist['Close'].iloc[-1]
                # استخدم أقدم بيانات متاحة إذا كان عدد الصفوف أقل من 60
                idx = min(59, len(hist) - 2)
                hour_ago_price = hist['Close'].iloc[-idx-1]
                price_change = ((current_price - hour_ago_price) / hour_ago_price) * 100
            except (IndexError, KeyError):
                current_price = hist['Close'].iloc[-1] if not hist['Close'].empty else 0
                price_change = 0

            # تحليل اتجاه الشموع لفترات زمنية مختلفة
            candle_trends = {}
            
            # تحديد اتجاه شموع الدقيقة
            minute_candles = hist_1min.tail(5)  # آخر 5 شمعات
            candle_trends['1min'] = {
                'direction': 'صاعدة' if minute_candles['Close'].iloc[-1] > minute_candles['Open'].iloc[-1] else 'نازلة',
                'color': 'أخضر' if minute_candles['Close'].iloc[-1] > minute_candles['Open'].iloc[-1] else 'أحمر',
                'consecutive_count': self._count_consecutive_candles(minute_candles)
            }
            
            # تحديد اتجاه شموع 15 دقيقة
            m15_candles = hist_15min.tail(5)
            candle_trends['15min'] = {
                'direction': 'صاعدة' if m15_candles['Close'].iloc[-1] > m15_candles['Open'].iloc[-1] else 'نازلة',
                'color': 'أخضر' if m15_candles['Close'].iloc[-1] > m15_candles['Open'].iloc[-1] else 'أحمر',
                'consecutive_count': self._count_consecutive_candles(m15_candles)
            }
            
            # تحديد اتجاه شموع الساعة
            hour_candles = hist_1hour.tail(5)
            candle_trends['1hour'] = {
                'direction': 'صاعدة' if hour_candles['Close'].iloc[-1] > hour_candles['Open'].iloc[-1] else 'نازلة',
                'color': 'أخضر' if hour_candles['Close'].iloc[-1] > hour_candles['Open'].iloc[-1] else 'أحمر',
                'consecutive_count': self._count_consecutive_candles(hour_candles)
            }
            
            # تحديد اتجاه شموع اليوم
            day_candles = hist_1day.tail(5)
            candle_trends['1day'] = {
                'direction': 'صاعدة' if day_candles['Close'].iloc[-1] > day_candles['Open'].iloc[-1] else 'نازلة',
                'color': 'أخضر' if day_candles['Close'].iloc[-1] > day_candles['Open'].iloc[-1] else 'أحمر',
                'consecutive_count': self._count_consecutive_candles(day_candles)
            }

            # Store indicators for market state analysis
            self.technical_indicators = {
                'close': current_price,
                'sma_20': hist['SMA_20'].iloc[-1],
                'sma_50': hist['SMA_50'].iloc[-1],
                'sma_200': hist['SMA_200'].iloc[-1],
                'ema_12': hist['EMA_12'].iloc[-1],
                'rsi': hist['RSI'].iloc[-1],
                'macd': hist['MACD'].iloc[-1],
                'macd_signal': hist['Signal_Line'].iloc[-1],
                'macd_hist': hist['MACD_Hist'].iloc[-1],
                'adx': hist['ADX'].iloc[-1],
                'mfi': hist['MFI'].iloc[-1],
                'bb_upper': hist['BB_upper'].iloc[-1],
                'bb_lower': hist['BB_lower'].iloc[-1],
                'obv': hist['OBV'].iloc[-1],
                'trend_strength': hist['Trend_Strength'].iloc[-1],
                'volume': hist['Volume'].iloc[-1],
                'candle_trends': candle_trends
            }

            return price_change
        except Exception as e:
            st.error(f"خطأ في حساب التغير: {str(e)}")
            return 0

    def get_market_state(self):
        """Advanced market state analysis"""
        if not hasattr(self, 'technical_indicators'):
            return 'محايد'

        ti = self.technical_indicators

        # Enhanced market conditions analysis
        conditions = []

        # Trend analysis (35% weight)
        trend_score = 0
        if ti['close'] > ti['sma_20']:
            trend_score += 0.35
        if ti['close'] > ti['sma_50']:
            trend_score += 0.35
        if ti['close'] > ti['sma_200']:
            trend_score += 0.3

        conditions.append(trend_score)

        # Momentum indicators (35% weight)
        momentum_score = 0
        if ti['rsi'] > 70:
            momentum_score -= 0.4
        elif ti['rsi'] < 30:
            momentum_score += 0.4
        else:
            momentum_score += (ti['rsi'] - 50) / 100

        if ti['macd'] > ti['macd_signal']:
            momentum_score += 0.3
        else:
            momentum_score -= 0.3

        if ti['macd_hist'] > 0:
            momentum_score += 0.3
        else:
            momentum_score -= 0.3

        conditions.append(momentum_score)

        # Volume and volatility (30% weight)
        vol_score = 0
        if ti['close'] > ti['bb_upper']:
            vol_score -= 0.3
        elif ti['close'] < ti['bb_lower']:
            vol_score += 0.3

        if ti['adx'] > 25:  # Strong trend
            if ti['mfi'] > 80:
                vol_score -= 0.4  # Overbought
            elif ti['mfi'] < 20:
                vol_score += 0.4  # Oversold
            else:
                vol_score += 0.2  # Healthy trend

        conditions.append(vol_score)

        # Calculate final weighted market state
        weights = [0.35, 0.35, 0.30]  # Weights for trend, momentum, and volume
        avg_condition = sum(c * w for c, w in zip(conditions, weights))

        if avg_condition > 0.3:
            return 'صاعد'
        elif avg_condition < -0.3:
            return 'هابط'
        else:
            return 'محايد'

    def get_signal_confidence(self):
        """Calculate enhanced signal confidence"""
        if not hasattr(self, 'technical_indicators') or not self.models:
            return 0.5

        ti = self.technical_indicators
        features = np.array([[
            ti['rsi'],
            ti['adx'],
            ti['mfi'],
            ti['trend_strength'],
            ti['macd'],
            ti['macd_hist'],
            ti['obv']
        ]])

        # Scale features
        features_scaled = self.scaler.transform(features)

        # Get predictions from both models
        rf_prob = self.models['rf'].predict_proba(features_scaled)[0]
        gb_prob = self.models['gb'].predict_proba(features_scaled)[0]

        # Ensemble confidence
        confidence = (max(rf_prob) * 0.6 + max(gb_prob) * 0.4)  # Weighted average

        return confidence
    def _count_consecutive_candles(self, candles_data):
        """حساب عدد الشموع المتتالية في نفس الاتجاه"""
        if len(candles_data) < 2:
            return 1
            
        current_direction = 'up' if candles_data['Close'].iloc[-1] > candles_data['Open'].iloc[-1] else 'down'
        count = 1
        
        # Start from the second-to-last candle and go backwards
        for i in range(len(candles_data)-2, -1, -1):
            candle_dir = 'up' if candles_data['Close'].iloc[i] > candles_data['Open'].iloc[i] else 'down'
            if candle_dir == current_direction:
                count += 1
            else:
                break
                
        return count
