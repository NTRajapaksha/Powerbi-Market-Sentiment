import time
import requests
import psycopg2
from datetime import datetime
import json

# ==========================================
# ⚙️ CONFIGURATION (ACTION REQUIRED)
# ==========================================
# 1. Paste your free key from NewsAPI.org here
NEWS_API_KEY = '066eef15ddbb42a19e8130287f19b8c7' 

# 2. The local AI model we will use
OLLAMA_MODEL = 'llama3.2:3b'

# 3. PostgreSQL Database config (matching your setup from Project 4)
DB_CONFIG = {
    'dbname': 'financial_dashboard_db',
    'user': 'postgres',
    'password': 'password',
    'host': 'localhost',
    'port': '5432'
}

# We will track 3 assets to stay well under the NewsAPI free tier limits (100 requests/day)
ASSETS = ['bitcoin', 'ethereum', 'solana']

# ==========================================
# 🛠️ DATABASE SETUP
# ==========================================
def setup_database():
    """Connects to PostgreSQL, creates the database if needed, and builds our two tables."""
    print("Checking database setup...")
    try:
        # Connect to default postgres database to create our specific project database
        conn = psycopg2.connect(dbname='postgres', user=DB_CONFIG['user'], password=DB_CONFIG['password'], host=DB_CONFIG['host'], port=DB_CONFIG['port'])
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_CONFIG['dbname']}'")
        if not cursor.fetchone():
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['dbname']}")
            print(f"Created new database: {DB_CONFIG['dbname']}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error checking database: {e}")
        exit(1)

    # Now connect to the actual database and create the tables
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Table 1: Live Prices
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_prices (
            id SERIAL PRIMARY KEY,
            asset VARCHAR(50),
            timestamp TIMESTAMP,
            price REAL,
            change_pct REAL
        )
    ''')
    
    # Table 2: Live Sentiment
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_sentiment (
            id SERIAL PRIMARY KEY,
            asset VARCHAR(50),
            timestamp TIMESTAMP,
            headline TEXT,
            sentiment_label VARCHAR(20),
            sentiment_score REAL
        )
    ''')
    conn.commit()
    conn.close()
    print("Database tables are ready!")

# ==========================================
# 🧠 AI SENTIMENT ANALYSIS (OLLAMA)
# ==========================================
def analyze_sentiment_with_ai(headline):
    """Sends the headline to your local Ollama AI model to ask for a sentiment score."""
    prompt = f"""
    Analyze the financial sentiment of this news headline: "{headline}"
    Reply ONLY with a single JSON object containing two keys:
    "label": either "Positive", "Negative", or "Neutral"
    "score": a number from -1.0 (very negative) to 1.0 (very positive). Neutral is 0.0.
    Do not output any other text, just the JSON.
    """
    
    # This is the default port where Ollama runs locally on your machine
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json" # Forces the AI to reply in clean JSON format
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        # Extract the AI's response text and parse it as JSON
        ai_response = response.json()['response']
        result = json.loads(ai_response)
        
        label = result.get('label', 'Neutral')
        score = float(result.get('score', 0.0))
        return label, score
        
    except Exception as e:
        # If the AI fails (or Ollama isn't running), default to Neutral
        print(f"   [!] AI Error on headline: {e}")
        return "Neutral", 0.0

# ==========================================
# 🔄 MAIN DATA PIPELINE
# ==========================================
def fetch_and_store_data():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 1. Fetch Prices from CoinGecko
    print(f"\n[{current_time}] Pulling Live Prices...")
    price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(ASSETS)}&vs_currencies=usd&include_24hr_change=true"
    try:
        price_res = requests.get(price_url).json()
        for asset in ASSETS:
            price = price_res.get(asset, {}).get('usd', 0)
            change = price_res.get(asset, {}).get('usd_24h_change', 0)
            
            cursor.execute("INSERT INTO live_prices (asset, timestamp, price, change_pct) VALUES (%s, %s, %s, %s)",
                           (asset.capitalize(), current_time, price, change))
            print(f" -> {asset.capitalize()}: ${price} ({round(change,2)}%)")
    except Exception as e:
        print(f"Price pull failed: {e}")

    # 2. Fetch News and Analyze Sentiment
    print(f"\n[{current_time}] Pulling News & Running AI Analysis...")
    if NEWS_API_KEY == 'YOUR_NEWS_API_KEY_HERE':
        print(" -> [SKIPPED] You haven't added your NewsAPI key yet!")
    else:
        for asset in ASSETS:
            # Get the top 3 most recent articles for the asset
            news_url = f"https://newsapi.org/v2/everything?q={asset}&sortBy=publishedAt&pageSize=3&language=en&apiKey={NEWS_API_KEY}"
            try:
                news_res = requests.get(news_url).json()
                articles = news_res.get('articles', [])
                
                for article in articles:
                    headline = article.get('title', '')
                    if not headline or '[Removed]' in headline: continue
                    
                    # Check if we already have this headline in the database to avoid duplicates
                    cursor.execute("SELECT 1 FROM live_sentiment WHERE asset = %s AND headline = %s", (asset.capitalize(), headline))
                    if cursor.fetchone():
                        continue # Skip to the next article if we already scored this one
                    
                    # Pass the headline to our local AI
                    label, score = analyze_sentiment_with_ai(headline)
                    
                    cursor.execute("INSERT INTO live_sentiment (asset, timestamp, headline, sentiment_label, sentiment_score) VALUES (%s, %s, %s, %s, %s)",
                                   (asset.capitalize(), current_time, headline, label, score))
                    
                    print(f" -> [{label}] ({score}) | {headline[:60]}...")
            except Exception as e:
                print(f"News pull failed for {asset}: {e}")
                
    conn.commit()
    conn.close()
    print("Database updated.")

def main():
    print("Starting Financial Sentiment Pipeline...")
    setup_database()
    
    try:
        while True:
            fetch_and_store_data()
            print("\nWaiting 15 minutes before the next pull to respect free API limits...")
            # NewsAPI free tier allows 100 requests per day. 
            # 3 assets * 4 pulls per hour (every 15 mins) * 24 = 288 requests (Wait, that's too much!)
            # Let's pull every 60 minutes instead for a safe continuous run.
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\nPipeline stopped by user.")

if __name__ == "__main__":
    main()
