import duckdb
import os

DB_PATH = "data/job_market.db"
os.makedirs("data/processed", exist_ok=True)

print("Connecting to DuckDB...")
conn = duckdb.connect(DB_PATH)

print("Calculating daily trends...")
daily_query = """
SELECT strftime(first_seen, '%Y-%m-%d') AS date, COUNT(*) AS job_count
FROM cleaned_jobs
WHERE first_seen IS NOT NULL
GROUP BY date
ORDER BY date;
"""
daily_jobs = conn.execute(daily_query).df()
daily_jobs.to_csv("data/processed/daily_job_trends.csv", index=False)

print("Calculating monthly trends...")
monthly_query = """
SELECT strftime(first_seen, '%Y-%m') AS month, COUNT(*) AS job_count
FROM cleaned_jobs
WHERE first_seen IS NOT NULL
GROUP BY month
ORDER BY month;
"""
monthly_jobs = conn.execute(monthly_query).df()
monthly_jobs.to_csv("data/processed/monthly_job_trends.csv", index=False)

print("Daily trend rows:", len(daily_jobs))
print(daily_jobs.head())

print("Monthly trend rows:", len(monthly_jobs))
print(monthly_jobs.head())

conn.close()
print("Saved trend data to daily_job_trends.csv and monthly_job_trends.csv")