import streamlit as st
from groq import Groq
import requests
import wikipedia
import pyjokes
import random
import math
import string
from datetime import datetime, date
import json
import time
import os
from dotenv import load_dotenv
load_dotenv()

# ================================
# API Keys — replace with yours!
# ================================
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
except:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# ================================
# Page Config
# ================================
st.set_page_config(
    page_title="ZEUS AI Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ================================
# Custom CSS — Dark Zeus Theme
# ================================
st.markdown("""
<style>
    .stApp {
        background: #0a0a0a;
    }
    .zeus-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-radius: 15px;
        border: 2px solid #ffd700;
        margin-bottom: 1rem;
    }
    .chat-user {
        background: #1a1a2e;
        border-left: 3px solid #ffd700;
        padding: 10px 15px;
        border-radius: 8px;
        margin: 5px 0;
        color: white;
    }
    .chat-zeus {
        background: #16213e;
        border-left: 3px solid #00ff88;
        padding: 10px 15px;
        border-radius: 8px;
        margin: 5px 0;
        color: white;
    }
    .feature-card {
        background: #1a1a2e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# ================================
# Initialize Session State
# ================================
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'notes' not in st.session_state:
    st.session_state.notes = []
if 'todos' not in st.session_state:
    st.session_state.todos = []
if 'zeus_name' not in st.session_state:
    st.session_state.zeus_name = "User"
if 'personality' not in st.session_state:
    st.session_state.personality = "Friendly"

# ================================
# Helper Functions
# ================================
def ask_zeus(prompt, system_prompt=None):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        if system_prompt is None:
            personality_prompts = {
                "Friendly": "You are ZEUS, a friendly and helpful AI assistant. Be warm and conversational.",
                "Professional": "You are ZEUS, a professional AI assistant. Be formal, precise and business-like.",
                "Sarcastic": "You are ZEUS, a witty and sarcastic AI assistant. Be funny but still helpful.",
                "Motivational": "You are ZEUS, a motivational AI coach. Be inspiring and encouraging!",
                "Teacher": "You are ZEUS, an educational AI teacher. Explain everything clearly with examples."
            }
            system_prompt = personality_prompts.get(
                st.session_state.personality,
                "You are ZEUS, a helpful AI assistant.")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error connecting to ZEUS brain: {str(e)}"

def get_weather(city):
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url, timeout=10).json()
        if not geo_response.get('results'):
            return f"City '{city}' not found! Try another name."

        lat = geo_response['results'][0]['latitude']
        lon = geo_response['results'][0]['longitude']
        city_name = geo_response['results'][0]['name']
        country = geo_response['results'][0].get('country', '')

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,"
            f"windspeed_10m,weathercode,precipitation"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
            f"&timezone=auto&forecast_days=3"
        )
        weather = requests.get(weather_url, timeout=10).json()
        current = weather['current']

        conditions = {
            0: "☀️ Clear Sky", 1: "🌤️ Mainly Clear",
            2: "⛅ Partly Cloudy", 3: "☁️ Overcast",
            45: "🌫️ Foggy", 48: "🌫️ Foggy",
            51: "🌦️ Light Drizzle", 61: "🌧️ Rain",
            71: "❄️ Snow", 80: "🌦️ Showers",
            95: "⛈️ Thunderstorm"
        }
        code = current.get('weathercode', 0)
        condition = conditions.get(code, "🌤️ Clear")

        return {
            'city': f"{city_name}, {country}",
            'temp': current['temperature_2m'],
            'humidity': current['relative_humidity_2m'],
            'wind': current['windspeed_10m'],
            'condition': condition,
            'forecast': weather['daily']
        }
    except Exception as e:
        return f"Weather error: {str(e)}"

def get_news(category="general", country="in"):
    try:
        # Free tier works better with everything endpoint
        url = f"https://newsapi.org/v2/top-headlines?language=en&category={category}&pageSize=5&apiKey={NEWS_API_KEY}"
        response = requests.get(url).json()
        if response.get('status') == 'ok':
            return response.get('articles', [])
        return []
    except:
        return []

def get_stock(symbol):
    try:
        import yfinance as yf
        stock = yf.Ticker(symbol)
        info = stock.fast_info
        return {
            'symbol': symbol.upper(),
            'price': round(info.last_price, 2),
            'change': round(info.last_price - info.previous_close, 2),
            'change_pct': round((info.last_price - info.previous_close) / info.previous_close * 100, 2)
        }
    except Exception as e:
        return None

def get_currency(amount, from_currency, to_currency):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
        response = requests.get(url).json()
        rate = response['rates'][to_currency.upper()]
        converted = amount * rate
        return round(converted, 2), round(rate, 4)
    except:
        return None, None

def generate_password(length=16, use_symbols=True):
    chars = string.ascii_letters + string.digits
    if use_symbols:
        chars += "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def calculate_age(birth_date):
    today = date.today()
    age = today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day))
    next_birthday = date(today.year, birth_date.month, birth_date.day)
    if next_birthday < today:
        next_birthday = date(today.year + 1, birth_date.month, birth_date.day)
    days_until = (next_birthday - today).days
    return age, days_until

# ================================
# SIDEBAR
# ================================
st.sidebar.markdown("## ⚡ ZEUS")
st.sidebar.markdown("*Zero Effort Universal System*")
st.sidebar.divider()

# User name
name = st.sidebar.text_input("Your name:", value=st.session_state.zeus_name)
if name != st.session_state.zeus_name:
    st.session_state.zeus_name = name

# Personality
personality = st.sidebar.selectbox("ZEUS Personality:",
    ["Friendly", "Professional", "Sarcastic", "Motivational", "Teacher"])
st.session_state.personality = personality

st.sidebar.divider()

page = st.sidebar.radio("Navigate:", [
    "⚡ Dashboard",
    "🤖 Chat with ZEUS",
    "🌤️ Weather",
    "📰 News",
    "📈 Stocks & Currency",
    "📝 Notes & Todo",
    "🛠️ Tools",
    "🎮 Fun Zone",
    "⏱️ Timers"
])

# ================================
# DASHBOARD
# ================================
if page == "⚡ Dashboard":
    st.markdown(f"""
    <div class="zeus-header">
        <h1 style="color: #ffd700; font-size: 50px; margin: 0;">⚡ ZEUS</h1>
        <p style="color: #888; margin: 5px 0;">Zero Effort Universal System</p>
        <p style="color: #ffd700;">Welcome back, {st.session_state.zeus_name}!</p>
    </div>
    """, unsafe_allow_html=True)

    # Quick stats
    now = datetime.now()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📅 Date", now.strftime("%d %b %Y"))
    with col2:
        st.metric("⏰ Time", now.strftime("%H:%M:%S"))
    with col3:
        st.metric("📝 Notes", len(st.session_state.notes))
    with col4:
        st.metric("✅ Todos", len(st.session_state.todos))

    # Auto refresh every second for live clock
    st.components.v1.html("""
    <script>
    setTimeout(function() {
        window.parent.location.reload();
    }, 60000);  // refresh every 60 seconds
    </script>
    """, height=0)

    # Quick weather
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🌤️ Quick Weather")
        city = st.text_input("City:", value="Mumbai", key="dash_city")
        if st.button("Get Weather ⚡"):
            weather = get_weather(city)
            if isinstance(weather, dict):
                st.success(f"**{weather['city']}**")
                st.metric("Temperature", f"{weather['temp']}°C")
                st.write(weather['condition'])
                st.write(f"💧 Humidity: {weather['humidity']}%")
                st.write(f"💨 Wind: {weather['wind']} km/h")

    with col2:
        st.subheader("📰 Quick News")
        if st.button("Get Top News ⚡"):
            articles = get_news()
            if articles:
                for a in articles[:3]:
                    st.markdown(f"• {a['title']}")
            else:
                st.warning("Add NewsAPI key to see news!")

    st.divider()

    # Quick chat
    st.subheader("⚡ Quick Ask ZEUS")
    quick_q = st.text_input("Ask anything...",
        placeholder="What is machine learning?")
    if st.button("Ask ZEUS ⚡", type="primary"):
        if quick_q:
            with st.spinner("ZEUS is thinking..."):
                answer = ask_zeus(quick_q)
            st.success(answer)

    st.divider()

    # Motivational quote
    if st.button("💪 Get Motivational Quote"):
        quote = ask_zeus("Give me one powerful motivational quote in 2 lines. Just the quote, no explanation.")
        st.info(f"⚡ {quote}")

# ================================
# CHAT WITH ZEUS
# ================================
elif page == "🤖 Chat with ZEUS":
    st.title("🤖 Chat with ZEUS")
    st.caption(f"Personality: {st.session_state.personality} | Chatting as: {st.session_state.zeus_name}")

    # Display chat history
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            st.markdown(f"""
            <div class="chat-user">
                👤 <b>{st.session_state.zeus_name}:</b> {msg['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-zeus">
                ⚡ <b>ZEUS:</b> {msg['content']}
            </div>
            """, unsafe_allow_html=True)

    # ================================
    # Voice Component — Full Auto Flow
    # ================================
    st.components.v1.html("""
<div style="padding: 15px; background: #1a1a2e;
            border-radius: 12px; border: 1px solid #333;">

    <div id="status" style="color: #888; font-size: 13px;
         margin-bottom: 10px; text-align: center;">
        Press mic → speak → text auto-copies → paste in box below!
    </div>

    <div style="text-align: center;">
        <button id="micBtn" onclick="toggleListening()" style="
            background: #ffd700; color: black;
            border: none; padding: 12px 25px;
            border-radius: 50px; font-size: 15px;
            font-weight: bold; cursor: pointer;">
            🎙️ Click to Speak
        </button>
        <button onclick="copyText()" style="
            background: #00ff88; color: black;
            border: none; padding: 12px 25px;
            border-radius: 50px; font-size: 15px;
            font-weight: bold; cursor: pointer;
            margin-left: 10px;">
            📋 Copy Text
        </button>
    </div>

    <div id="result-box" style="
        margin-top: 12px;
        background: #0d1117;
        border: 1px solid #ffd700;
        border-radius: 8px;
        padding: 10px;
        min-height: 40px;
        color: #ffd700;
        font-size: 14px;
        display: none;">
    </div>
</div>

<script>
let recognition = null;
let isListening = false;
let finalText = '';

function toggleListening() {
    if (isListening) {
        stopListening();
    } else {
        startListening();
    }
}

function startListening() {
    if (!('webkitSpeechRecognition' in window) &&
        !('SpeechRecognition' in window)) {
        document.getElementById('status').textContent =
            '❌ Use Chrome browser for voice!';
        return;
    }

    recognition = new (window.SpeechRecognition ||
                       window.webkitSpeechRecognition)();
    recognition.lang = 'en-IN';
    recognition.interimResults = true;
    recognition.continuous = false;
    isListening = true;

    const btn = document.getElementById('micBtn');
    btn.textContent = '🔴 Listening... (click to stop)';
    btn.style.background = '#ff4444';
    btn.style.color = 'white';
    document.getElementById('status').textContent =
        '🎙️ Speak now...';

    recognition.onresult = function(event) {
        let interim = '';
        finalText = '';
        for (let i = 0; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
                finalText += event.results[i][0].transcript;
            } else {
                interim += event.results[i][0].transcript;
            }
        }
        const box = document.getElementById('result-box');
        box.style.display = 'block';
        box.textContent = finalText || interim;
    };

    recognition.onend = function() {
        stopListening();
        if (finalText) {
            // Auto copy to clipboard
            navigator.clipboard.writeText(finalText).then(() => {
                document.getElementById('status').textContent =
                    '✅ Copied! Now press Ctrl+V in the text box below and click Send ⚡';
            }).catch(() => {
                document.getElementById('status').textContent =
                    '✅ Done! Manually copy text above and paste below.';
            });
        }
    };

    recognition.onerror = function(e) {
        document.getElementById('status').textContent =
            '❌ Error: ' + e.error;
        stopListening();
    };

    recognition.start();
}

function stopListening() {
    isListening = false;
    if (recognition) recognition.stop();
    const btn = document.getElementById('micBtn');
    btn.textContent = '🎙️ Click to Speak';
    btn.style.background = '#ffd700';
    btn.style.color = 'black';
}

function copyText() {
    const text = document.getElementById('result-box').textContent;
    if (text) {
        navigator.clipboard.writeText(text).then(() => {
            document.getElementById('status').textContent =
                '✅ Copied! Paste in box below with Ctrl+V';
        });
    }
}
</script>
""", height=180)
    # ================================
    # Text Input + Send
    # ================================
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input("Or type your message:",
            placeholder="Type here OR use voice button above...",
            key="chat_input",
            label_visibility="collapsed")
    with col2:
        send = st.button("Send ⚡", type="primary",
                          use_container_width=True)

    # Voice input from session state
    voice_input = st.session_state.get('voice_message', '')

    # Process either text or voice input
    final_input = user_input if send and user_input else ''

    if final_input:
        st.session_state.chat_history.append({
            'role': 'user',
            'content': final_input
        })

        messages = []
        for msg in st.session_state.chat_history[-10:]:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })

        with st.spinner("⚡ ZEUS is thinking..."):
            try:
                client = Groq(api_key=GROQ_API_KEY)
                personality_prompts = {
                    "Friendly": "You are ZEUS, a friendly helpful AI. Be warm and conversational.",
                    "Professional": "You are ZEUS, a professional AI. Be formal and precise.",
                    "Sarcastic": "You are ZEUS, witty and sarcastic but helpful.",
                    "Motivational": "You are ZEUS, a motivational coach. Be inspiring!",
                    "Teacher": "You are ZEUS, a teacher. Explain with examples."
                }
                system = personality_prompts.get(
                    st.session_state.personality,
                    "You are ZEUS, a helpful AI.")

                messages_with_system = [
                    {"role": "system", "content": system}
                ] + messages

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages_with_system,
                    max_tokens=1000
                )
                zeus_reply = response.choices[0].message.content
            except Exception as e:
                zeus_reply = f"Error: {str(e)}"

        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': zeus_reply
        })

        # Auto speak ZEUS reply
        safe_reply = zeus_reply.replace('`', '').replace('"', '').replace("'", '')[:300]
        st.components.v1.html(f"""
        <script>
        function speakZeus() {{
            window.speechSynthesis.cancel();
            const msg = new SpeechSynthesisUtterance("{safe_reply}");
            msg.rate = 0.95;
            msg.pitch = 1.0;
            msg.volume = 1.0;
            // Try to get a good voice
            const voices = window.speechSynthesis.getVoices();
            const preferred = voices.find(v =>
                v.name.includes('Google') ||
                v.name.includes('Natural') ||
                v.lang === 'en-US');
            if (preferred) msg.voice = preferred;
            window.speechSynthesis.speak(msg);
        }}
        // Small delay to ensure voices are loaded
        setTimeout(speakZeus, 500);
        </script>
        """, height=0)

        st.rerun()

    # ================================
    # Last ZEUS reply — Read aloud button
    # ================================
    if st.session_state.chat_history:
        last_msgs = [m for m in st.session_state.chat_history
                     if m['role'] == 'assistant']
        if last_msgs:
            last_reply = last_msgs[-1]['content']
            safe_last = last_reply.replace('`','').replace('"','').replace("'",'')[:300]

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔊 Read Last Reply"):
                    st.components.v1.html(f"""
                    <script>
                    window.speechSynthesis.cancel();
                    const msg = new SpeechSynthesisUtterance("{safe_last}");
                    msg.rate = 0.95;
                    const voices = window.speechSynthesis.getVoices();
                    const preferred = voices.find(v =>
                        v.name.includes('Google') || v.lang==='en-US');
                    if (preferred) msg.voice = preferred;
                    window.speechSynthesis.speak(msg);
                    </script>
                    """, height=0)
            with col2:
                if st.button("⏹️ Stop Speaking"):
                    st.components.v1.html("""
                    <script>
                    window.speechSynthesis.cancel();
                    </script>
                    """, height=0)
            with col3:
                if st.button("🗑️ Clear Chat"):
                    st.session_state.chat_history = []
                    st.rerun()

# ================================
# WEATHER PAGE
# ================================
elif page == "🌤️ Weather":
    st.title("🌤️ Weather — Powered by ZEUS")

    city = st.text_input("Enter city name:",
                          placeholder="Mumbai, Delhi, London...")

    if st.button("Get Weather ⚡", type="primary"):
        with st.spinner("Fetching weather..."):
            weather = get_weather(city)

        if isinstance(weather, dict):
            st.success(f"## {weather['condition']} {weather['city']}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🌡️ Temperature", f"{weather['temp']}°C")
            with col2:
                st.metric("💧 Humidity", f"{weather['humidity']}%")
            with col3:
                st.metric("💨 Wind Speed", f"{weather['wind']} km/h")

            st.divider()
            st.subheader("📅 3 Day Forecast")
            cols = st.columns(3)
            forecast = weather['forecast']
            for i, col in enumerate(cols):
                with col:
                    day = datetime.strptime(
                        forecast['time'][i], '%Y-%m-%d')
                    st.markdown(f"**{day.strftime('%A')}**")
                    st.metric("Max", f"{forecast['temperature_2m_max'][i]}°C")
                    st.metric("Min", f"{forecast['temperature_2m_min'][i]}°C")
                    st.write(f"🌧️ {forecast['precipitation_sum'][i]}mm")

            # ZEUS weather insight
            st.divider()
            if st.button("💬 Ask ZEUS about this weather"):
                insight = ask_zeus(
                    f"The weather in {weather['city']} is {weather['condition']}, "
                    f"{weather['temp']}°C, humidity {weather['humidity']}%. "
                    f"Give a fun 2 line weather commentary and what to wear!"
                )
                st.info(f"⚡ ZEUS says: {insight}")
        else:
            st.error(weather)

# ================================
# NEWS PAGE
# ================================
elif page == "📰 News":
    st.title("📰 Latest News — Powered by ZEUS")

    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Category:", [
            "general", "technology", "sports",
            "business", "entertainment", "health", "science"
        ])
    with col2:
        country = st.selectbox("Region:", ["us", "gb", "au"], 
        format_func=lambda x: {
            "us": "🇺🇸 USA",
            "gb": "🇬🇧 UK",
            "au": "🇦🇺 Australia"
        }[x])
    if st.button("Get News ⚡", type="primary"):
        with st.spinner("Fetching latest news..."):
            articles = get_news(category, country)

        if articles:
            for i, article in enumerate(articles):
                with st.expander(
                    f"📰 {article['title'][:80]}..."):
                    st.markdown(f"**{article['title']}**")
                    if article.get('description'):
                        st.write(article['description'])
                    if article.get('url'):
                        st.markdown(f"[Read full article]({article['url']})")
                    if article.get('publishedAt'):
                        st.caption(f"Published: {article['publishedAt'][:10]}")

                    if st.button(f"⚡ ZEUS Summary",
                                 key=f"news_{i}"):
                        summary = ask_zeus(
                            f"Summarize this news in 3 bullet points: "
                            f"{article['title']}. {article.get('description','')}"
                        )
                        st.info(summary)
        else:
            st.warning("No news found! Check your NewsAPI key.")

# ================================
# STOCKS & CURRENCY
# ================================
elif page == "📈 Stocks & Currency":
    st.title("📈 Stocks & Currency — Powered by ZEUS")

    tab1, tab2 = st.tabs(["📈 Stocks", "💱 Currency"])

    with tab1:
        st.subheader("Stock Price Checker")
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.text_input("Stock Symbol:",
                placeholder="AAPL, GOOGL, TSLA, RELIANCE.NS")
        with col2:
            if st.button("Get Price ⚡", type="primary"):
                with st.spinner("Fetching stock..."):
                    stock = get_stock(symbol)
                if stock:
                    color = "🟢" if stock['change'] >= 0 else "🔴"
                    st.metric(
                        f"{color} {stock['symbol']}",
                        f"${stock['price']}",
                        f"{stock['change']} ({stock['change_pct']}%)"
                    )
                    analysis = ask_zeus(
                        f"Give a very brief 2 line analysis of {symbol} stock "
                        f"at ${stock['price']} with {stock['change_pct']}% change today."
                    )
                    st.info(f"⚡ ZEUS: {analysis}")
                else:
                    st.error("Stock not found!")

        st.divider()
        st.subheader("📊 Popular Stocks")
        stocks = ["AAPL", "GOOGL", "MSFT", "TSLA", "META"]
        cols = st.columns(5)
        for i, s in enumerate(stocks):
            if cols[i].button(s):
                data = get_stock(s)
                if data:
                    color = "🟢" if data['change'] >= 0 else "🔴"
                    st.metric(f"{color} {s}",
                              f"${data['price']}",
                              f"{data['change_pct']}%")

    with tab2:
        st.subheader("Currency Converter")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            amount = st.number_input("Amount:", value=100.0)
        with col2:
            from_cur = st.selectbox("From:",
                ["USD", "INR", "EUR", "GBP", "JPY", "AUD"])
        with col3:
            to_cur = st.selectbox("To:",
                ["INR", "USD", "EUR", "GBP", "JPY", "AUD"])
        with col4:
            if st.button("Convert ⚡", type="primary"):
                result, rate = get_currency(amount, from_cur, to_cur)
                if result:
                    st.metric("Result",
                              f"{result} {to_cur}",
                              f"Rate: {rate}")
                else:
                    st.error("Conversion failed!")

# ================================
# NOTES & TODO
# ================================
elif page == "📝 Notes & Todo":
    st.title("📝 Notes & Todo — Powered by ZEUS")

    tab1, tab2 = st.tabs(["📝 Notes", "✅ Todo List"])

    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            note_title = st.text_input("Note title:")
            note_content = st.text_area("Note content:", height=150)
        with col2:
            st.write("")
            st.write("")
            if st.button("💾 Save Note", type="primary"):
                if note_title and note_content:
                    st.session_state.notes.append({
                        'title': note_title,
                        'content': note_content,
                        'time': datetime.now().strftime("%d %b %H:%M")
                    })
                    st.success("Note saved! ✅")
                    st.rerun()

            if st.button("⚡ AI Improve Note"):
                if note_content:
                    improved = ask_zeus(
                        f"Improve and expand this note, "
                        f"make it more detailed and well structured: {note_content}"
                    )
                    st.info(improved)

        st.divider()
        st.subheader(f"📚 My Notes ({len(st.session_state.notes)})")
        for i, note in enumerate(
                reversed(st.session_state.notes)):
            with st.expander(f"📝 {note['title']} — {note['time']}"):
                st.write(note['content'])
                if st.button("🗑️ Delete", key=f"del_note_{i}"):
                    st.session_state.notes.pop(
                        len(st.session_state.notes)-1-i)
                    st.rerun()

    with tab2:
        col1, col2 = st.columns([3, 1])
        with col1:
            todo_text = st.text_input("New task:",
                placeholder="Finish Python project...")
        with col2:
            priority = st.selectbox("Priority:",
                ["🔴 High", "🟡 Medium", "🟢 Low"])

        if st.button("➕ Add Task", type="primary"):
            if todo_text:
                st.session_state.todos.append({
                    'task': todo_text,
                    'priority': priority,
                    'done': False,
                    'time': datetime.now().strftime("%d %b")
                })
                st.rerun()

        st.divider()
        pending = [t for t in st.session_state.todos
                   if not t['done']]
        done = [t for t in st.session_state.todos if t['done']]

        st.subheader(f"⏳ Pending ({len(pending)})")
        for i, todo in enumerate(st.session_state.todos):
            if not todo['done']:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"{todo['priority']} {todo['task']}")
                with col2:
                    if st.button("✅", key=f"done_{i}"):
                        st.session_state.todos[i]['done'] = True
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"del_{i}"):
                        st.session_state.todos.pop(i)
                        st.rerun()

        if done:
            st.subheader(f"✅ Completed ({len(done)})")
            for todo in done:
                st.write(f"~~{todo['task']}~~")

        if st.button("⚡ ZEUS Task Suggestions"):
            pending_tasks = [t['task'] for t in pending]
            if pending_tasks:
                suggestion = ask_zeus(
                    f"I have these pending tasks: {pending_tasks}. "
                    f"Suggest the best order to complete them and why."
                )
                st.info(suggestion)

# ================================
# TOOLS PAGE
# ================================
elif page == "🛠️ Tools":
    st.title("🛠️ Tools — Powered by ZEUS")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔐 Password", "🔢 Calculator",
        "📅 Age", "💱 Translator", "📊 Summarizer"])

    with tab1:
        st.subheader("🔐 Password Generator")
        col1, col2, col3 = st.columns(3)
        with col1:
            pwd_length = st.slider("Length:", 8, 32, 16)
        with col2:
            use_symbols = st.checkbox("Include symbols", value=True)
        with col3:
            num_passwords = st.slider("How many:", 1, 5, 3)

        if st.button("Generate Passwords ⚡", type="primary"):
            st.subheader("Generated Passwords:")
            for i in range(num_passwords):
                pwd = generate_password(pwd_length, use_symbols)
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.code(pwd)
                with col2:
                    strength = "💪 Strong" if pwd_length >= 16 else "⚠️ Medium"
                    st.write(strength)

    with tab2:
        st.subheader("🔢 Smart Calculator")
        expression = st.text_input("Enter expression:",
            placeholder="2 + 2, sin(90), sqrt(144)...")

        if st.button("Calculate ⚡", type="primary"):
            try:
                safe_expr = expression.replace(
                    'sin', 'math.sin').replace(
                    'cos', 'math.cos').replace(
                    'sqrt', 'math.sqrt').replace(
                    'pi', 'math.pi')
                result = eval(safe_expr)
                st.success(f"**{expression} = {result}**")
            except:
                # Use AI for complex problems
                answer = ask_zeus(
                    f"Solve this math problem step by step: {expression}")
                st.info(f"⚡ ZEUS: {answer}")

    with tab3:
        st.subheader("📅 Age Calculator")
        birth_date = st.date_input("Date of birth:",
            min_value=date(1900, 1, 1),
            max_value=date.today())

        if st.button("Calculate Age ⚡", type="primary"):
            age, days_until_bday = calculate_age(birth_date)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎂 Age", f"{age} years")
            with col2:
                st.metric("📅 Days until birthday", days_until_bday)
            with col3:
                total_days = (date.today() - birth_date).days
                st.metric("📆 Days lived", f"{total_days:,}")

            bday_msg = ask_zeus(
                f"Someone is {age} years old with {days_until_bday} "
                f"days until birthday. Give a fun 1 line birthday message!"
            )
            st.info(f"⚡ ZEUS: {bday_msg}")

    with tab4:
        st.subheader("🌍 Language Translator")
        text_to_translate = st.text_area("Text to translate:", height=100)
        col1, col2 = st.columns(2)
        with col1:
            target_lang = st.selectbox("Translate to:", [
                "Hindi", "Marathi", "French", "Spanish",
                "Japanese", "German", "Arabic", "Chinese",
                "Portuguese", "Russian"
            ])

        if st.button("Translate ⚡", type="primary"):
            if text_to_translate:
                with st.spinner("Translating..."):
                    translated = ask_zeus(
                        f"Translate this text to {target_lang}. "
                        f"Return ONLY the translation, nothing else: "
                        f"{text_to_translate}"
                    )
                st.success(f"**{target_lang} translation:**")
                st.write(translated)

    with tab5:
        st.subheader("📊 AI Text Summarizer")
        text_to_summarize = st.text_area(
            "Paste text to summarize:", height=200,
            placeholder="Paste any article, email, or text here...")
        summary_style = st.selectbox("Summary style:", [
            "Bullet points", "One paragraph",
            "Key points only", "ELI5 (Explain Like I'm 5)"
        ])

        if st.button("Summarize ⚡", type="primary"):
            if text_to_summarize:
                with st.spinner("Summarizing..."):
                    summary = ask_zeus(
                        f"Summarize this text in {summary_style} format. "
                        f"Be concise and clear: {text_to_summarize}"
                    )
                st.success("**Summary:**")
                st.write(summary)

# ================================
# FUN ZONE
# ================================
elif page == "🎮 Fun Zone":
    st.title("🎮 Fun Zone — Powered by ZEUS")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "😂 Jokes", "🎲 Random Facts",
        "🎱 Magic 8 Ball", "🎨 Story Generator",
        "🎯 Decision Maker"])

    with tab1:
        st.subheader("😂 Joke Teller")
        joke_type = st.selectbox("Joke type:", [
            "Random", "Programming", "Dad Jokes",
            "AI Generated", "Puns"
        ])

        if st.button("Tell me a joke! 😂", type="primary"):
            if joke_type == "Programming":
                joke = pyjokes.get_joke(category='chuck')
                st.success(joke)
            elif joke_type == "AI Generated":
                joke = ask_zeus(
                    "Tell me one original funny joke. Just the joke!")
                st.success(joke)
            else:
                joke = pyjokes.get_joke()
                st.success(joke)

    with tab2:
        st.subheader("🎲 Random Facts")
        fact_category = st.selectbox("Category:", [
            "Science", "History", "Space", "Animals",
            "Technology", "India", "Sports", "Random"
        ])

        if st.button("Tell me a fact! 🤯", type="primary"):
            fact = ask_zeus(
                f"Tell me one mind-blowing, lesser-known fact about "
                f"{fact_category}. Just the fact in 2-3 sentences!")
            st.info(f"🤯 {fact}")

    with tab3:
        st.subheader("🎱 Magic 8 Ball")
        question = st.text_input("Ask your yes/no question:",
            placeholder="Will I get the job?")

        if st.button("Ask the Magic 8 Ball 🎱", type="primary"):
            if question:
                responses = [
                    "⚡ It is certain!", "⚡ Definitely yes!",
                    "🌟 Signs point to yes", "🤔 Ask again later",
                    "⚠️ Cannot predict now", "❌ Don't count on it",
                    "🔮 My sources say no", "💫 Without a doubt!",
                    "⚡ ZEUS says... YES!", "🌪️ The thunder says NO!"
                ]
                answer = random.choice(responses)
                st.success(f"**{answer}**")

                zeus_take = ask_zeus(
                    f"Someone asked: '{question}'. "
                    f"Give a funny and mystical 1 line response!"
                )
                st.info(f"⚡ ZEUS adds: {zeus_take}")

    with tab4:
        st.subheader("🎨 Story Generator")
        col1, col2 = st.columns(2)
        with col1:
            story_topic = st.text_input("Story topic:",
                placeholder="A ninja who codes...")
            story_genre = st.selectbox("Genre:", [
                "Adventure", "Horror", "Comedy",
                "Romance", "Sci-Fi", "Mystery"
            ])
        with col2:
            story_length = st.selectbox("Length:", [
                "Short (1 paragraph)", "Medium (3 paragraphs)",
                "Long (5 paragraphs)"
            ])
            story_style = st.selectbox("Style:", [
                "Normal", "Poetic", "Suspenseful", "Funny"
            ])

        if st.button("Generate Story ⚡", type="primary"):
            if story_topic:
                with st.spinner("ZEUS is writing..."):
                    story = ask_zeus(
                        f"Write a {story_length} {story_genre} story "
                        f"about: {story_topic}. "
                        f"Style: {story_style}. Make it engaging!"
                    )
                st.write(story)

    with tab5:
        st.subheader("🎯 Decision Maker")
        decision_type = st.selectbox("Type:", [
            "Coin Flip", "Dice Roll",
            "Pick from options", "AI Decision"
        ])

        if decision_type == "Coin Flip":
            if st.button("Flip Coin 🪙", type="primary"):
                result = random.choice(["🪙 HEADS!", "🪙 TAILS!"])
                st.success(f"## {result}")

        elif decision_type == "Dice Roll":
            sides = st.selectbox("Dice sides:", [4, 6, 8, 10, 12, 20])
            if st.button(f"Roll D{sides} 🎲", type="primary"):
                result = random.randint(1, sides)
                st.success(f"## 🎲 You rolled: {result}")

        elif decision_type == "Pick from options":
            options_text = st.text_area(
                "Enter options (one per line):",
                placeholder="Pizza\nBurger\nSushi")
            if st.button("Pick one! ⚡", type="primary"):
                if options_text:
                    options = [o.strip() for o in
                               options_text.split('\n') if o.strip()]
                    if options:
                        choice = random.choice(options)
                        st.success(f"## ⚡ ZEUS picks: **{choice}**")

        elif decision_type == "AI Decision":
            dilemma = st.text_area("Describe your dilemma:",
                placeholder="Should I take job A or job B?")
            if st.button("ZEUS decides! ⚡", type="primary"):
                if dilemma:
                    decision = ask_zeus(
                        f"Help me decide: {dilemma}. "
                        f"Give a clear recommendation with brief reason."
                    )
                    st.info(f"⚡ ZEUS recommends: {decision}")

# ================================
# TIMERS PAGE
# ================================
elif page == "⏱️ Timers":
    st.title("⏱️ Timers — Powered by ZEUS")

    tab1, tab2 = st.tabs(["⏱️ Countdown Timer", "🍅 Pomodoro"])

    with tab1:
        st.subheader("⏱️ Countdown Timer")
        col1, col2, col3 = st.columns(3)
        with col1:
            hours = st.number_input("Hours:", 0, 23, 0)
        with col2:
            minutes = st.number_input("Minutes:", 0, 59, 5)
        with col3:
            seconds = st.number_input("Seconds:", 0, 59, 0)

        total_seconds = hours*3600 + minutes*60 + seconds

        if st.button("▶️ Start Timer", type="primary"):
            st.components.v1.html(f"""
            <div style="text-align: center; padding: 20px;">
                <div id="timer" style="
                    font-size: 60px;
                    font-weight: bold;
                    color: #ffd700;
                    font-family: monospace;
                    background: #1a1a2e;
                    padding: 20px 40px;
                    border-radius: 15px;
                    border: 2px solid #ffd700;
                    display: inline-block;">
                    {hours:02d}:{minutes:02d}:{seconds:02d}
                </div>
                <br><br>
                <button onclick="pauseTimer()" style="
                    background: #ffd700; color: black;
                    border: none; padding: 10px 25px;
                    border-radius: 25px; font-size: 16px;
                    font-weight: bold; cursor: pointer;
                    margin: 5px;">
                    ⏸️ Pause
                </button>
                <button onclick="resetTimer()" style="
                    background: #ff4444; color: white;
                    border: none; padding: 10px 25px;
                    border-radius: 25px; font-size: 16px;
                    font-weight: bold; cursor: pointer;
                    margin: 5px;">
                    🔄 Reset
                </button>
            </div>

            <script>
            let remaining = {total_seconds};
            let paused = false;
            let interval = null;

            function updateDisplay() {{
                const h = Math.floor(remaining / 3600);
                const m = Math.floor((remaining % 3600) / 60);
                const s = remaining % 60;
                document.getElementById('timer').textContent =
                    String(h).padStart(2,'0') + ':' +
                    String(m).padStart(2,'0') + ':' +
                    String(s).padStart(2,'0');
            }}

            function pauseTimer() {{
                paused = !paused;
                document.querySelector('button').textContent =
                    paused ? '▶️ Resume' : '⏸️ Pause';
            }}

            function resetTimer() {{
                remaining = {total_seconds};
                paused = false;
                updateDisplay();
            }}

            interval = setInterval(() => {{
                if (!paused && remaining > 0) {{
                    remaining--;
                    updateDisplay();
                }} else if (remaining === 0) {{
                    clearInterval(interval);
                    document.getElementById('timer').textContent = "⏰ TIME'S UP!";
                    document.getElementById('timer').style.color = '#ff4444';
                    new Audio('https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3').play();
                }}
            }}, 1000);
            </script>
            """, height=200)

    with tab2:
        st.subheader("🍅 Pomodoro Timer")
        st.write("Work 25 minutes → Break 5 minutes → Repeat!")

        col1, col2 = st.columns(2)
        with col1:
            work_time = st.slider("Work time (min):", 15, 60, 25)
        with col2:
            break_time = st.slider("Break time (min):", 3, 15, 5)

        st.components.v1.html(f"""
        <div style="text-align: center; padding: 20px;">
            <div id="pomodoro-label" style="
                color: #ffd700; font-size: 20px;
                margin-bottom: 10px; font-weight: bold;">
                🍅 Work Time
            </div>
            <div id="pomodoro-timer" style="
                font-size: 70px;
                font-weight: bold;
                color: #ffd700;
                font-family: monospace;
                background: #1a1a2e;
                padding: 20px 40px;
                border-radius: 15px;
                border: 2px solid #ffd700;
                display: inline-block;">
                {work_time:02d}:00
            </div>
            <br><br>
            <button id="startBtn" onclick="startPomodoro()" style="
                background: #00ff88; color: black;
                border: none; padding: 12px 30px;
                border-radius: 25px; font-size: 16px;
                font-weight: bold; cursor: pointer;
                margin: 5px;">
                ▶️ Start
            </button>
            <button onclick="resetPomodoro()" style="
                background: #ff4444; color: white;
                border: none; padding: 12px 30px;
                border-radius: 25px; font-size: 16px;
                font-weight: bold; cursor: pointer;
                margin: 5px;">
                🔄 Reset
            </button>
            <div id="session-count" style="
                color: #888; margin-top: 15px; font-size: 14px;">
                Sessions completed: 0
            </div>
        </div>

        <script>
        let workSecs = {work_time} * 60;
        let breakSecs = {break_time} * 60;
        let remaining = workSecs;
        let isWorking = true;
        let running = false;
        let sessions = 0;
        let interval = null;

        function updateDisplay() {{
            const m = Math.floor(remaining / 60);
            const s = remaining % 60;
            document.getElementById('pomodoro-timer').textContent =
                String(m).padStart(2,'0') + ':' +
                String(s).padStart(2,'0');
        }}

        function startPomodoro() {{
            if (running) {{
                running = false;
                clearInterval(interval);
                document.getElementById('startBtn').textContent = '▶️ Resume';
                return;
            }}
            running = true;
            document.getElementById('startBtn').textContent = '⏸️ Pause';

            interval = setInterval(() => {{
                if (remaining > 0) {{
                    remaining--;
                    updateDisplay();
                }} else {{
                    if (isWorking) {{
                        sessions++;
                        document.getElementById('session-count').textContent =
                            'Sessions completed: ' + sessions;
                        isWorking = false;
                        remaining = breakSecs;
                        document.getElementById('pomodoro-label').textContent =
                            '☕ Break Time!';
                        document.getElementById('pomodoro-timer').style.color = '#00ff88';
                        document.getElementById('pomodoro-timer').style.borderColor = '#00ff88';
                    }} else {{
                        isWorking = true;
                        remaining = workSecs;
                        document.getElementById('pomodoro-label').textContent =
                            '🍅 Work Time';
                        document.getElementById('pomodoro-timer').style.color = '#ffd700';
                        document.getElementById('pomodoro-timer').style.borderColor = '#ffd700';
                    }}
                    updateDisplay();
                }}
            }}, 1000);
        }}

        function resetPomodoro() {{
            clearInterval(interval);
            running = false;
            isWorking = true;
            remaining = workSecs;
            sessions = 0;
            document.getElementById('startBtn').textContent = '▶️ Start';
            document.getElementById('pomodoro-label').textContent = '🍅 Work Time';
            document.getElementById('pomodoro-timer').style.color = '#ffd700';
            document.getElementById('session-count').textContent =
                'Sessions completed: 0';
            updateDisplay();
        }}
        </script>
        """, height=300)