import duckdb
import os
import time

DB_PATH = "data/job_market.db"
RAW_PATH = "data/raw/linkedin_job_postings.csv"
SKILLS_PATH = "data/raw/job_skills.csv"
OUTPUT_PATH = "data/processed/jobs_cleaned.parquet"

os.makedirs("data/processed", exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

print("Connecting to DuckDB...")
conn = duckdb.connect(DB_PATH)

start_time = time.time()

# Clean and load directly into a table
print("Cleaning and loading data into table 'cleaned_jobs'...")
conn.execute("DROP TABLE IF EXISTS cleaned_jobs;")

# We read both CSV files directly using DuckDB's CSV reader, join them, deduplicate, and store them.
# We also select and clean only the required columns.
conn.execute(f"""
CREATE TABLE cleaned_jobs AS
WITH postings_cleaned AS (
    SELECT 
        TRIM(LOWER(COALESCE(job_link, ''))) AS job_link,
        TRIM(LOWER(COALESCE(job_title, ''))) AS job_title,
        TRIM(LOWER(COALESCE(company, ''))) AS company,
        TRIM(LOWER(COALESCE(job_location, ''))) AS job_location,
        try_cast(first_seen AS TIMESTAMP) AS first_seen,
        TRIM(LOWER(COALESCE(search_city, ''))) AS search_city,
        TRIM(LOWER(COALESCE(search_country, ''))) AS search_country,
        TRIM(LOWER(COALESCE(search_position, ''))) AS search_position,
        TRIM(LOWER(COALESCE(job_level, ''))) AS job_level,
        TRIM(LOWER(COALESCE(job_type, ''))) AS job_type,
        ROW_NUMBER() OVER (PARTITION BY job_link ORDER BY first_seen DESC) AS rn
    FROM read_csv_auto('{RAW_PATH}', all_varchar=True)
),
skills_cleaned AS (
    SELECT 
        TRIM(LOWER(COALESCE(job_link, ''))) AS job_link,
        TRIM(LOWER(COALESCE(job_skills, ''))) AS job_skills
    FROM read_csv_auto('{SKILLS_PATH}', all_varchar=True)
)
SELECT 
    p.job_link,
    p.job_title,
    p.company,
    p.job_location,
    p.first_seen,
    p.search_city,
    p.search_country,
    p.search_position,
    p.job_level,
    p.job_type,
    COALESCE(s.job_skills, '') AS job_skills
FROM postings_cleaned p
LEFT JOIN skills_cleaned s ON p.job_link = s.job_link
WHERE p.rn = 1 AND p.first_seen IS NOT NULL;
""")

print("Creating indexes on columns frequently used for filtering...")
conn.execute("CREATE INDEX IF NOT EXISTS idx_job_link ON cleaned_jobs (job_link);")
conn.execute("CREATE INDEX IF NOT EXISTS idx_search_country ON cleaned_jobs (search_country);")
conn.execute("CREATE INDEX IF NOT EXISTS idx_search_city ON cleaned_jobs (search_city);")
conn.execute("CREATE INDEX IF NOT EXISTS idx_job_type ON cleaned_jobs (job_type);")
conn.execute("CREATE INDEX IF NOT EXISTS idx_job_level ON cleaned_jobs (job_level);")

print("Saving cleaned data to Parquet for backwards compatibility...")
conn.execute(f"COPY cleaned_jobs TO '{OUTPUT_PATH}' (FORMAT PARQUET);")

# Count rows
res = conn.execute("SELECT COUNT(*) FROM cleaned_jobs;").fetchone()
num_rows = res[0] if res else 0

conn.close()

elapsed = time.time() - start_time
print(f"Preprocessing completed in {elapsed:.2f} seconds.")
print("Total rows loaded:", num_rows)
print("Saved to database:", DB_PATH)
print("Saved to Parquet:", OUTPUT_PATH)