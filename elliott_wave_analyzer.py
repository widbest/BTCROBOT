
import numpy as np
import pandas as pd
from datetime import datetime
import streamlit as st
import yfinance as yf
from scipy.signal import find_peaks

class ElliottWaveAnalyzer:
    def __init__(self):
        self.symbol = "BTC-USD"
        self.wave_data = None
        self.last_analysis = None
        self.current_wave = None
        
    def analyze_waves(self, period="3mo", interval="1d"):
        """Identify Elliott Wave patterns in the price data"""
        try:
            # Get historical data
            btc = yf.Ticker(self.symbol)
            hist = btc.history(period=period, interval=interval)
            
            if len(hist) < 30:
                return None
                
            # Use closing prices for wave analysis
            prices = hist['Close'].values
            dates = hist.index
            
            # Find significant peaks and troughs مع معالجة الأخطاء المحتملة
            try:
                # استخدم مستوى بروز متغير بناءً على تقلب السوق
                prominence_factor = max(0.3, min(0.7, np.std(prices)/np.mean(prices)))
                peaks, _ = find_peaks(prices, prominence=np.std(prices)*prominence_factor)
                troughs, _ = find_peaks(-prices, prominence=np.std(prices)*prominence_factor)
                
                # التأكد من وجود نقاط كافية
                if len(peaks) < 2 or len(troughs) < 2:
                    # جرب باستخدام مستوى بروز أقل
                    peaks, _ = find_peaks(prices, prominence=np.std(prices)*0.25)
                    troughs, _ = find_peaks(-prices, prominence=np.std(prices)*0.25)
            except Exception as e:
                print(f"خطأ في تحديد القمم والقيعان: {str(e)}")
                # استخدم طريقة بديلة بسيطة
                peaks = [i for i in range(1, len(prices)-1) if prices[i] > prices[i-1] and prices[i] > prices[i+1]]
                troughs = [i for i in range(1, len(prices)-1) if prices[i] < prices[i-1] and prices[i] < prices[i+1]]
            
            # Combine and sort all pivot points
            pivots = []
            for peak in peaks:
                pivots.append({'index': peak, 'price': prices[peak], 'type': 'peak', 'date': dates[peak]})
            for trough in troughs:
                pivots.append({'index': trough, 'price': prices[trough], 'type': 'trough', 'date': dates[trough]})
                
            # Sort by index
            pivots = sorted(pivots, key=lambda x: x['index'])
            
            if len(pivots) < 5:
                return None
                
            # Identify Elliott Wave pattern (simplified)
            wave_pattern = self._identify_wave_pattern(pivots, prices)
            
            # Store analysis result
            self.wave_data = wave_pattern
            self.last_analysis = datetime.now()
            
            return wave_pattern
            
        except Exception as e:
            st.error(f"خطأ في تحليل موجات إليوت: {str(e)}")
            return None
    
    def _identify_wave_pattern(self, pivots, prices):
        """Identify the current Elliott Wave pattern"""
        # We need at least 9 pivot points for a complete cycle
        if len(pivots) < 5:
            return {'current_phase': 'غير محدد', 'confidence': 0, 'next_move': 'غير محدد'}
            
        # Get recent pivots (last 9 or fewer)
        recent_pivots = pivots[-9:] if len(pivots) >= 9 else pivots
        
        # Calculate price changes between pivots
        changes = []
        for i in range(1, len(recent_pivots)):
            prev = recent_pivots[i-1]['price']
            curr = recent_pivots[i]['price']
            changes.append((curr - prev) / prev)
        
        # Determine wave counts and current phase
        # This is a simplified implementation
        if len(changes) >= 8:
            # Check if we have a complete 5-3 wave pattern
            if (changes[0] > 0 and changes[2] > 0 and changes[4] > 0 and
                changes[1] < 0 and changes[3] < 0 and
                changes[5] < 0 and changes[7] < 0 and changes[6] > 0):
                
                # We have a complete cycle, determine next
                if recent_pivots[-1]['type'] == 'trough':
                    return {
                        'current_phase': 'اكتمال الدورة',
                        'confidence': 0.8,
                        'next_move': 'صاعد',
                        'current_wave': 'بداية موجة 1 جديدة',
                        'pattern': 'اكتمال موجات إليوت'
                    }
                else:
                    return {
                        'current_phase': 'نهاية الموجة C',
                        'confidence': 0.7,
                        'next_move': 'هابط',
                        'current_wave': 'نهاية موجة تصحيحية',
                        'pattern': 'اكتمال موجات إليوت'
                    }
        
        # Analyze partial patterns if we don't have a complete cycle
        if len(changes) >= 4:
            # Check for impulse wave pattern (5 waves)
            if changes[-4] > 0 and changes[-2] > 0 and changes[-1] < 0 and changes[-3] < 0:
                # Likely in wave 5 or finished impulse
                if recent_pivots[-1]['type'] == 'peak':
                    return {
                        'current_phase': 'موجة 5',
                        'confidence': 0.7,
                        'next_move': 'هابط',
                        'current_wave': 'نهاية موجة دافعة',
                        'pattern': 'موجة دافعة'
                    }
                else:
                    return {
                        'current_phase': 'موجة A',
                        'confidence': 0.6,
                        'next_move': 'هابط',
                        'current_wave': 'بداية موجة تصحيحية',
                        'pattern': 'بداية تصحيح'
                    }
            
            # Check for corrective wave pattern (3 waves)
            if changes[-3] < 0 and changes[-2] > 0 and changes[-1] < 0:
                return {
                    'current_phase': 'موجة C',
                    'confidence': 0.65,
                    'next_move': 'صاعد',
                    'current_wave': 'نهاية موجة تصحيحية',
                    'pattern': 'موجة تصحيحية'
                }
        
        # If we have at least 2 changes, try to make a determination
        if len(changes) >= 2:
            if changes[-2] > 0 and changes[-1] < 0:
                if recent_pivots[-2]['type'] == 'peak':
                    return {
                        'current_phase': 'موجة 2 أو موجة B',
                        'confidence': 0.5,
                        'next_move': 'صاعد',
                        'current_wave': 'في موجة تصحيحية',
                        'pattern': 'تصحيح داخلي'
                    }
            if changes[-2] < 0 and changes[-1] > 0:
                return {
                    'current_phase': 'موجة 3 أو C',
                    'confidence': 0.5,
                    'next_move': 'صاعد',
                    'current_wave': 'في موجة دافعة',
                    'pattern': 'بداية موجة دافعة'
                }
        
        # Default if pattern unclear
        last_change = (prices[-1] - prices[-2]) / prices[-2] if len(prices) > 1 else 0
        
        return {
            'current_phase': 'غير محدد',
            'confidence': 0.3,
            'next_move': 'صاعد' if last_change > 0 else 'هابط',
            'current_wave': 'غير محدد',
            'pattern': 'نمط غير واضح'
        }
    
    def get_current_wave_state(self):
        """Get the current Elliott Wave state"""
        if not self.wave_data:
            self.analyze_waves()
            
        return self.wave_data
    
    def get_wave_prediction(self):
        """Get predictive insights based on current wave position"""
        if not self.wave_data:
            self.analyze_waves()
            
        if not self.wave_data:
            return {
                'prediction': 'غير محدد',
                'confidence': 0,
                'target_move': 0,
                'wave_target': 0
            }
            
        # Get current price
        try:
            btc = yf.Ticker(self.symbol)
            current_price = btc.info['regularMarketPrice']
            
            # Make prediction based on wave pattern
            if self.wave_data['current_phase'] == 'موجة 3':
                # Wave 3 is typically the strongest
                target_move = 0.15  # 15% move
                direction = 1 if self.wave_data['next_move'] == 'صاعد' else -1
                confidence = 0.75
                
            elif self.wave_data['current_phase'] == 'موجة 5':
                # Wave 5 could extend but nearing completion
                target_move = 0.08  # 8% move
                direction = 1 if self.wave_data['next_move'] == 'صاعد' else -1
                confidence = 0.6
                
            elif self.wave_data['current_phase'] == 'موجة C':
                # End of corrective wave
                target_move = 0.05  # 5% move
                direction = 1  # Usually up after wave C completes
                confidence = 0.7
                
            else:
                # Default modest prediction
                target_move = 0.05
                direction = 1 if self.wave_data['next_move'] == 'صاعد' else -1
                confidence = self.wave_data['confidence'] * 0.8
            
            wave_target = current_price * (1 + direction * target_move)
            
            return {
                'prediction': self.wave_data['next_move'],
                'confidence': confidence,
                'target_move': target_move * direction,
                'wave_target': wave_target
            }
            
        except Exception as e:
            st.error(f"خطأ في توقع موجات إليوت: {str(e)}")
            return {
                'prediction': 'غير محدد',
                'confidence': 0,
                'target_move': 0,
                'wave_target': 0
            }
