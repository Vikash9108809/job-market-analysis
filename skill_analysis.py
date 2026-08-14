import duckdb
import os

DB_PATH = "data/job_market.db"
OUTPUT_PATH = "data/processed/top_skills.csv"

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

print("Connecting to DuckDB...")
conn = duckdb.connect(DB_PATH)

print("Extracting and counting top 30 skills...")
query = """
SELECT skill, COUNT(*) AS count
FROM (
    SELECT unnest(string_split(job_skills, ',')) AS skill
    FROM cleaned_jobs
)
WHERE skill != '' AND skill != 'nan'
GROUP BY skill
ORDER BY count DESC
LIMIT 30;
"""

df = conn.execute(query).df()
df.to_csv(OUTPUT_PATH, index=False)

print(df)
conn.close()
print("Saved top skills to:", OUTPUT_PATH)