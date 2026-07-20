# 🧠 AI-Powered Financial Sentiment Command Center

## 📌 Project Overview
This project is an advanced Data Engineering and Business Intelligence pipeline. It combines live cryptocurrency market data with real-time news headlines, feeding them into a **local Large Language Model (LLM)** to generate an automated sentiment score. The data is stored in a relational PostgreSQL database and visualized in Power BI via a live DirectQuery connection.

## 🏗️ Architecture & Tech Stack
* **Data Sources:** CoinGecko API (Prices) & NewsAPI (Headlines).
* **AI Engine:** Ollama running `llama3.2:3b` locally for strict JSON-formatted sentiment classification.
* **Data Pipeline:** Python (`requests` for API extraction, `psycopg2` for database loading).
* **Storage:** PostgreSQL (Configured in a WSL environment).
* **BI Tool:** Power BI Desktop (DirectQuery for real-time dashboard updates).

## 📊 Dashboard Features
* **Hype Matrix (Scatter Plot):** Correlates 24h price action against the AI sentiment score, perfectly dividing the market into 4 analytical quadrants (Momentum, Bubble, Panic Selloff, Undervalued).
* **Live News Ticker:** A conditionally formatted table showing the exact headlines driving the AI's scoring engine.
* **Real-time KPIs:** High-level metrics tracking the overall portfolio average price and average sentiment.

## 🚀 How to Run the Project
1. Install **PostgreSQL** inside WSL and configure it to accept external connections.
2. Install **Ollama** inside WSL and pull the `llama3.2:3b` model.
3. Get a free API key from **NewsAPI.org**.
4. Run the Python ETL script (`financial_sentiment_pipeline.py`) to begin the extraction and AI scoring loop.
5. Connect **Power BI** to the WSL PostgreSQL instance via DirectQuery and construct the visuals.
