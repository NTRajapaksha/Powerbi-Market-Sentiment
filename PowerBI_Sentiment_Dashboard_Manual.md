# 🚀 Project 6: Live Financial Market Sentiment Dashboard

This manual explains exactly *why* we are doing each step so you can speak to this project confidently in a BI Engineering interview.

## 🧠 Step 1: Set Up Local AI (Ollama)
*Why we do this:* Enterprise companies don't like sending sensitive financial data to public APIs like ChatGPT due to data privacy. Running a "Local LLM" (Large Language Model) on your own hardware proves you know how to build secure, private AI pipelines.

1. **Install Ollama:** If using Windows Subsystem for Linux (WSL), make sure you run Ollama within your WSL environment.
2. **Download the Model:** Open your terminal (WSL) and type:
   ```bash
   ollama pull llama3.2:3b
   ```
   *Why this model?* Llama 3.2 is Meta's newest, highly efficient model. It's small enough to run fast on a laptop, but smart enough to understand complex financial terminology. The `:3b` tag ensures you get the exact version our script expects.

## 📰 Step 2: Get your Free NewsAPI Key
*Why we do this:* To perform sentiment analysis, we need raw text data (news). NewsAPI provides a standardized JSON feed of global headlines, which is a classic Data Engineering ingestion task.

1. Go to [NewsAPI.org](https://newsapi.org/) and click **Get API Key**.
2. Create an account and copy the long string of letters/numbers.
3. Open `financial_sentiment_pipeline.py` in a text editor.
4. Replace `'YOUR_NEWS_API_KEY_HERE'` on **Line 9** with your actual key. Save the file.

## ⚙️ Step 3: Run the Pipeline
*Why we do this:* This script acts as your ETL (Extract, Transform, Load) engine. It *Extracts* from two APIs, *Transforms* the raw text into structured sentiment scores using AI, and *Loads* it into a relational SQL database.

1. Open your terminal in the `bi` folder.
2. Run the script:
   ```bash
   python financial_sentiment_pipeline.py
   ```
3. Watch the terminal. You will see it pull the prices, then read the news, ask your local AI for a score, and push it all to PostgreSQL! Leave it running in the background. *(Note: It runs every 60 minutes so you don't exhaust your 100 free NewsAPI requests for the day).*

---

## 🛠️ Step 4: Configure WSL Network for Power BI
*Why we do this:* By default, PostgreSQL inside WSL will refuse external connections from Windows apps (like Power BI). We must explicitly allow Windows to "talk" to the WSL database.

1. Open your WSL terminal and run these three commands to open the Postgres network port:
   ```bash
   sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/*/main/postgresql.conf
   echo "host all all 0.0.0.0/0 md5" | sudo tee -a /etc/postgresql/*/main/pg_hba.conf
   sudo service postgresql restart
   ```
2. Find your WSL IP address by running `hostname -I`. Copy the first IP address that appears (e.g., `172.25.x.x`). You will need this for Power BI!

---

## 📊 Step 5: Build the Dashboard in Power BI

Now we connect to our database and visualize the correlation between the AI's sentiment score and the actual market price.

### Connection & Modeling
*Why DirectQuery?* DirectQuery means Power BI doesn't import a static copy of the data. Every time a user clicks a filter, Power BI sends a live SQL query to PostgreSQL, ensuring the manager always sees the most up-to-date market reaction.

1. Open **Power BI Desktop**.
2. **Get Data > PostgreSQL database**.
   - Server: Paste your **WSL IP Address** here (e.g., `172.25.x.x`) | Database: `financial_dashboard_db`
   - Select **DirectQuery**.
   - Credentials: `postgres` / `password`.
   - *Note:* If Power BI throws a Certificate Validation Error, click OK, go to **File > Options and settings > Data source settings**, select your IP, click **Edit Permissions**, and UNCHECK "Encrypt connections".
3. Check **both** tables (`live_prices` and `live_sentiment`) and click **Load**.
4. **Data Modeling:** Go to the Model View (the third icon on the far left). Drag the `asset` column from `live_prices` and drop it onto the `asset` column in `live_sentiment` to create a relationship.

### Building the Visuals

**1. The Scatter Plot (The Crown Jewel)**
*Why this visual?* A scatter plot lets us find anomalies. If a coin has high positive sentiment but the price is crashing, that's a buying opportunity.
- Add a **Scatter Chart** visual.
- **Values:** `asset`
- **X-Axis:** `change_pct` (from `live_prices`). Set to Average.
- **Y-Axis:** `sentiment_score` (from `live_sentiment`). Set to Average.
- *Insight:* Coins in the top-right are riding a hype wave. Coins in the bottom-right have good news but falling prices.

**2. Live News Ticker (Table)**
*Why this visual?* The manager needs to read the actual headlines that are driving the AI's score.
- Add a **Table** visual.
- Add columns: `timestamp`, `asset`, `headline`, `sentiment_label`, `sentiment_score`.
- Sort by `timestamp` descending so the freshest news is on top.
- **Conditional Formatting:** Right click `sentiment_label` in the visualization pane > Conditional Formatting > Background Color. Make "Positive" green and "Negative" red.

**3. Price & Sentiment KPIs**
- Create **Card** visuals for the Average Price and the Average Sentiment Score, sliced by an Asset dropdown filter.

### Enable the Live Sync
- Click the empty canvas > Format Page pane > Page Refresh > Turn ON (set to every 5 minutes).

You have now built a full-stack, AI-powered financial dashboard!
