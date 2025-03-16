from datetime import datetime
import streamlit as st
import numpy as np

class SignalGenerator:
    def __init__(self):
        self.confidence_threshold = 0.2
        self.max_signals_per_day = 5
        self.signals_today = []
        self.success_rate_threshold = 0.98  # 98% success rate requirement

    def generate_signal(self, current_price, sentiment, market_state, price_analyzer, elliott_analyzer=None):
        """Generate high-accuracy trading signals with Elliott Wave support"""
        now = datetime.now()

        # Clean old signals
        self.signals_today = [s for s in self.signals_today 
                            if (now - s['timestamp']).total_seconds() < 24*3600]

        # Check daily signal limit
        if len(self.signals_today) >= self.max_signals_per_day:
            return {
                "action": "انتظار",
                "target_price": current_price,
                "stop_loss": current_price,
                "reason": "تم الوصول للحد الأقصى من التوصيات اليومية",
                "confidence": 0,
                "timestamp": now
            }

        # Get ML model confidence
        ml_confidence = price_analyzer.get_signal_confidence()

        # Get Elliott Wave data if analyzer is provided
        elliott_data = None
        elliott_prediction = None
        if elliott_analyzer:
            elliott_data = elliott_analyzer.get_current_wave_state()
            elliott_prediction = elliott_analyzer.get_wave_prediction()

        # Calculate overall confidence with Elliott Wave insights
        confidence = self._calculate_confidence(
            sentiment, 
            market_state, 
            ml_confidence, 
            price_analyzer,
            elliott_data
        )

        # Generate signal only if confidence meets our high threshold
        if confidence > self.success_rate_threshold:
            # Calculate optimal entry points and targets with Elliott Waves
            action, target_price, stop_loss, reason = self._calculate_optimal_levels(
                current_price, 
                sentiment, 
                market_state, 
                price_analyzer,
                elliott_data,
                elliott_prediction
            )
        else:
            action = "انتظار"
            target_price = current_price
            stop_loss = current_price
            reason = f"مستوى الثقة ({confidence:.1%}) أقل من المطلوب ({self.success_rate_threshold:.1%})"

        signal = {
            "action": action,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "reason": reason,
            "confidence": confidence,
            "timestamp": now,
            "market_state": market_state
        }

        # Store signal if it's actionable
        if action != "انتظار":
            self.signals_today.append(signal)

        return signal

    def _calculate_confidence(self, sentiment, market_state, ml_confidence, price_analyzer, elliott_data=None):
        """Calculate enhanced signal confidence with Elliott Wave insights"""
        if not hasattr(price_analyzer, 'technical_indicators'):
            return 0

        ti = price_analyzer.technical_indicators

        # Enhanced weights for different factors with Elliott Wave addition
        weights = {
            'ml_model': 0.30,       # Machine learning prediction
            'sentiment': 0.10,       # News sentiment
            'technicals': 0.30,      # Technical indicators
            'market_state': 0.10,    # Overall market state
            'elliott_wave': 0.20     # Elliott Wave analysis
        }

        # Calculate technical confidence based on trend confirmation
        technical_confidence = 0
        if market_state == 'صاعد':
            if ti['rsi'] > 50 and ti['macd'] > ti['macd_signal']:
                technical_confidence += 0.5
            if ti['close'] > ti['sma_20'] and ti['trend_strength'] > 0.6:
                technical_confidence += 0.5
        elif market_state == 'هابط':
            if ti['rsi'] < 50 and ti['macd'] < ti['macd_signal']:
                technical_confidence += 0.5
            if ti['close'] < ti['sma_20'] and ti['trend_strength'] < 0.4:
                technical_confidence += 0.5

        # Calculate market state confidence
        market_confidence = {
            'صاعد': 0.9 if sentiment > 0 else 0.3,
            'هابط': 0.9 if sentiment < 0 else 0.3,
            'محايد': 0.5
        }[market_state]

        # Calculate Elliott Wave confidence if data is available
        elliott_confidence = 0.5  # Default neutral
        if elliott_data:
            # Get base confidence from Elliott analysis
            elliott_confidence = elliott_data.get('confidence', 0.5)

            # Boost confidence if current wave aligns with market state
            if (market_state == 'صاعد' and elliott_data.get('next_move') == 'صاعد') or \
               (market_state == 'هابط' and elliott_data.get('next_move') == 'هابط'):
                elliott_confidence *= 1.2

            # Significant confidence boost for strong wave patterns
            if elliott_data.get('current_phase') == 'موجة 3':
                elliott_confidence *= 1.3  # Wave 3 is the strongest
            elif elliott_data.get('current_phase') == 'موجة 5':
                elliott_confidence *= 1.1  # Wave 5 is also strong

            # Cap elliott confidence at 1.0
            elliott_confidence = min(elliott_confidence, 1.0)

        # Combine all factors with enhanced weighting
        confidence = (
            weights['ml_model'] * ml_confidence +
            weights['sentiment'] * abs(sentiment) +
            weights['technicals'] * technical_confidence +
            weights['market_state'] * market_confidence +
            weights['elliott_wave'] * elliott_confidence
        )

        # Add trend strength bonus
        if ti['trend_strength'] > 0.7:
            confidence *= 1.1
        elif ti['trend_strength'] < 0.3:
            confidence *= 0.9

        # Add volume confirmation
        if ti['adx'] > 25:  # Strong trend
            confidence *= 1.1
        if 20 <= ti['rsi'] <= 80:  # Healthy RSI
            confidence *= 1.05

        # Add Elliott Wave pattern confirmation bonus
        if elliott_data and elliott_data.get('confidence', 0) > 0.6:
            confidence *= 1.1  # High confidence Elliott pattern

        return min(confidence, 1.0)  # Cap at 100%

    def _calculate_optimal_levels(self, current_price, sentiment, market_state, price_analyzer, elliott_data=None, elliott_prediction=None):
        """Calculate optimal entry, target, and stop-loss levels with dynamic calculations and Elliott Wave insights"""
        ti = price_analyzer.technical_indicators

        # تحسين آلية اتخاذ القرارات: إعطاء إشارة بناءً على اتجاه السوق وحده، مع الأخذ بالاعتبار المشاعر كعامل إضافي
        if market_state == 'صاعد':
            action = "شراء"
            # زيادة الثقة إذا كانت المشاعر إيجابية
            confidence_bonus = 0.1 if sentiment > 0 else 0

            # Calculate dynamic profit target based on multiple factors
            volatility = (ti['bb_upper'] - ti['bb_lower']) / current_price
            # تحقق من وجود مؤشر ATR واستخدام قيمة افتراضية إذا كان غير موجود
            atr_percent = max(0.005, ti.get('ATR', 0.005) / current_price)  # Ensure minimum ATR
            base_target = max(0.03, min(0.1, volatility * 2))  # 3-10% base range

            # Adjust target based on trend strength
            if ti['trend_strength'] > 0.7:
                base_target *= 1.2
            elif ti['trend_strength'] < 0.3:
                base_target *= 0.8

            # Tighter stop loss for higher confidence trades
            stop_loss_pct = min(0.015, atr_percent * 1.5)  # Maximum 1.5%
            if ti['adx'] > 25:  # Strong trend
                stop_loss_pct *= 0.8  # Tighter stop loss

            # Apply Elliott Wave insights to target if available
            if elliott_prediction and elliott_prediction['prediction'] == 'صاعد':
                # Adjust target based on Elliott Wave prediction
                elliott_target = elliott_prediction['wave_target']
                elliott_target_pct = (elliott_target / current_price) - 1

                # Use Elliott target if it's more aggressive than our base target
                if elliott_target_pct > base_target:
                    target_price = round(elliott_target, 2)
                    base_target = elliott_target_pct
                else:
                    target_price = round(current_price * (1 + base_target), 2)
            else:
                target_price = round(current_price * (1 + base_target), 2)

            # Adjust stop loss based on Elliott Wave phase if available
            if elliott_data and elliott_data.get('current_phase') == 'موجة 3':
                # Looser stop loss during strong Wave 3
                stop_loss_pct *= 1.2
            elif elliott_data and elliott_data.get('current_phase') in ['موجة 5', 'موجة C']:
                # Tighter stop loss during Wave 5 or C (near trend exhaustion)
                stop_loss_pct *= 0.8

            stop_loss = round(current_price * (1 - stop_loss_pct), 2)

            # Safety check - target and stop loss must be different from current price
            if abs(target_price - current_price) < 1:
                target_price = current_price + max(1, current_price * 0.01)
            if abs(stop_loss - current_price) < 1:
                stop_loss = current_price - max(1, current_price * 0.01)

            # Add Elliott Wave information to reason if available
            elliott_info = ""
            if elliott_data:
                elliott_info = f" | موجة إليوت: {elliott_data.get('current_phase', 'غير محدد')}"

            reason = f"إشارة شراء قوية ⬆️: السوق صاعد | RSI={ti['rsi']:.1f} | ADX={ti['adx']:.1f}{elliott_info}"

        elif market_state == 'هابط':
            action = "بيع"
            # زيادة الثقة إذا كانت المشاعر سلبية
            confidence_bonus = 0.1 if sentiment < 0 else 0

            # Calculate dynamic profit target
            volatility = (ti['bb_upper'] - ti['bb_lower']) / current_price
            # تحقق من وجود مؤشر ATR واستخدام قيمة افتراضية إذا كان غير موجود
            atr_percent = max(0.005, ti.get('ATR', 0.005) / current_price)  # Ensure minimum ATR
            base_target = max(0.03, min(0.1, volatility * 2))

            # Adjust target based on trend strength
            if ti['trend_strength'] < 0.3:
                base_target *= 1.2
            elif ti['trend_strength'] > 0.7:
                base_target *= 0.8

            # Tighter stop loss for higher confidence trades
            stop_loss_pct = min(0.015, atr_percent * 1.5)
            if ti['adx'] > 25:  # Strong trend
                stop_loss_pct *= 0.8

            # Apply Elliott Wave insights to target if available
            if elliott_prediction and elliott_prediction['prediction'] == 'هابط':
                # Adjust target based on Elliott Wave prediction
                elliott_target = elliott_prediction['wave_target']
                elliott_target_pct = 1 - (elliott_target / current_price)

                # Use Elliott target if it's more aggressive than our base target
                if elliott_target_pct > base_target:
                    target_price = round(elliott_target, 2)
                    base_target = elliott_target_pct
                else:
                    target_price = round(current_price * (1 - base_target), 2)
            else:
                target_price = round(current_price * (1 - base_target), 2)

            # Adjust stop loss based on Elliott Wave phase if available
            if elliott_data and elliott_data.get('current_phase') == 'موجة 3':
                # Looser stop loss during strong Wave 3
                stop_loss_pct *= 1.2
            elif elliott_data and elliott_data.get('current_phase') in ['موجة 5', 'موجة C']:
                # Tighter stop loss during Wave 5 or C (near trend exhaustion)
                stop_loss_pct *= 0.8

            stop_loss = round(current_price * (1 + stop_loss_pct), 2)

            # Safety check - target and stop loss must be different from current price
            if abs(target_price - current_price) < 1:
                target_price = current_price - max(1, current_price * 0.01)
            if abs(stop_loss - current_price) < 1:
                stop_loss = current_price + max(1, current_price * 0.01)

            # Add Elliott Wave information to reason if available
            elliott_info = ""
            if elliott_data:
                elliott_info = f" | موجة إليوت: {elliott_data.get('current_phase', 'غير محدد')}"

            reason = f"إشارة بيع قوية ⬇️: السوق هابط | RSI={ti['rsi']:.1f} | ADX={ti['adx']:.1f}{elliott_info}"

        else:
            action = "انتظار"
            target_price = round(current_price * 1.03, 2)  # Sample target 3% up
            stop_loss = round(current_price * 0.97, 2)    # Sample stop loss 3% down
            reason = "في انتظار تأكيد اتجاه السوق"

        return action, target_price, stop_loss, reason