import streamlit as st

def initialize_session_state():
    """Initialize session state variables"""
    if 'accuracy' not in st.session_state:
        st.session_state.accuracy = 98.0
    
    if 'total_signals' not in st.session_state:
        st.session_state.total_signals = 0
        
    if 'predictions' not in st.session_state:
        st.session_state.predictions = []
