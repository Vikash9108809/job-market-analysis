import duckdb
import pandas as pd
import os

DB_PATH = "data/job_market.db"

def get_db_connection():
    """Establish a connection to the DuckDB database (local or MotherDuck cloud)."""
    # Check for MotherDuck token in environment variables or Streamlit secrets
    token = os.environ.get("MOTHERDUCK_TOKEN")
    if not token:
        try:
            import streamlit as st
            if "MOTHERDUCK_TOKEN" in st.secrets:
                token = st.secrets["MOTHERDUCK_TOKEN"]
        except Exception:
            pass

    if token:
        # Connect to MotherDuck cloud database 'job_market'
        return duckdb.connect(f"md:job_market?token={token}")

    # Fallback to local database file
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return duckdb.connect(DB_PATH)

def execute_query(query, params=None):
    """Execute a query and return a Pandas DataFrame."""
    conn = get_db_connection()
    try:
        if params:
            res = conn.execute(query, params).df()
        else:
            res = conn.execute(query).df()
        return res
    finally:
        conn.close()

def build_where_clause(filters):
    """
    Build a parameterized SQL WHERE clause based on dynamic dashboard filters.
    Returns: (where_clause_string, params_list)
    """
    conditions = []
    params = []

    if filters:
        if filters.get("country") and filters["country"] != "All":
            conditions.append("search_country = ?")
            params.append(filters["country"].lower())

        if filters.get("city") and filters["city"] != "All":
            conditions.append("search_city = ?")
            params.append(filters["city"].lower())

        if filters.get("job_type") and filters["job_type"] != "All":
            conditions.append("job_type = ?")
            params.append(filters["job_type"].lower())

        if filters.get("job_level") and filters["job_level"] != "All":
            conditions.append("job_level = ?")
            params.append(filters["job_level"].lower())

        if filters.get("skill_kw"):
            conditions.append("contains(job_skills, ?)")
            params.append(filters["skill_kw"].lower())

        if filters.get("title_kw"):
            conditions.append("contains(job_title, ?)")
            params.append(filters["title_kw"].lower())

        if filters.get("exact_title"):
            conditions.append("job_title = ?")
            params.append(filters["exact_title"].lower())

        if filters.get("location_kw"):
            conditions.append("contains(job_location, ?)")
            params.append(filters["location_kw"].lower())

    if conditions:
        return "WHERE " + " AND ".join(conditions), params
    return "", []

def get_unique_filter_options():
    """Fetch distinct filter values for the dashboard sidebar."""
    conn = get_db_connection()
    try:
        countries = [r[0] for r in conn.execute("SELECT DISTINCT search_country FROM cleaned_jobs WHERE search_country IS NOT NULL AND search_country != '' ORDER BY search_country").fetchall()]
        types = [r[0] for r in conn.execute("SELECT DISTINCT job_type FROM cleaned_jobs WHERE job_type IS NOT NULL AND job_type != '' ORDER BY job_type").fetchall()]
        levels = [r[0] for r in conn.execute("SELECT DISTINCT job_level FROM cleaned_jobs WHERE job_level IS NOT NULL AND job_level != '' ORDER BY job_level").fetchall()]
        
        # We fetch cities dynamically depending on country inside app.py or database.py
        return countries, types, levels
    except Exception:
        return [], [], []
    finally:
        conn.close()

def get_cities_for_country(country=None):
    """Fetch cities for a specific country."""
    conn = get_db_connection()
    try:
        if country and country != "All":
            query = "SELECT DISTINCT search_city FROM cleaned_jobs WHERE search_country = ? AND search_city IS NOT NULL AND search_city != '' ORDER BY search_city"
            cities = [r[0] for r in conn.execute(query, [country.lower()]).fetchall()]
        else:
            query = "SELECT DISTINCT search_city FROM cleaned_jobs WHERE search_city IS NOT NULL AND search_city != '' ORDER BY search_city"
            cities = [r[0] for r in conn.execute(query).fetchall()]
        return cities
    except Exception:
        return []
    finally:
        conn.close()

def get_total_row_count():
    """Get the total size of the cleaned jobs table."""
    conn = get_db_connection()
    try:
        res = conn.execute("SELECT COUNT(*) FROM cleaned_jobs").fetchone()
        return res[0] if res else 0
    except Exception:
        return 0
    finally:
        conn.close()

def get_kpis(filters):
    """Retrieve key metrics: total jobs, companies, locations, unique titles, and unique skills."""
    where_clause, params = build_where_clause(filters)
    
    # 1. General counts
    query_general = f"""
    SELECT 
        COUNT(*) AS total_jobs,
        COUNT(DISTINCT company) AS total_companies,
        COUNT(DISTINCT job_location) AS total_locations,
        COUNT(DISTINCT job_title) AS unique_titles
    FROM cleaned_jobs
    {where_clause}
    """
    
    # 2. Total unique skills count
    query_skills = f"""
    SELECT COUNT(DISTINCT TRIM(LOWER(skill))) AS total_skills
    FROM (
        SELECT unnest(string_split(job_skills, ',')) AS skill
        FROM cleaned_jobs
        {where_clause}
    )
    WHERE skill != '' AND skill != 'nan'
    """
    
    # 3. Date range
    query_dates = f"""
    SELECT MIN(first_seen) AS min_date, MAX(first_seen) AS max_date
    FROM cleaned_jobs
    {where_clause}
    """
    
    conn = get_db_connection()
    try:
        gen_res = conn.execute(query_general, params).fetchone()
        skills_res = conn.execute(query_skills, params).fetchone()
        dates_res = conn.execute(query_dates, params).fetchone()
        
        return {
            "total_jobs": gen_res[0] if gen_res else 0,
            "total_companies": gen_res[1] if gen_res else 0,
            "total_locations": gen_res[2] if gen_res else 0,
            "unique_titles": gen_res[3] if gen_res else 0,
            "total_skills": skills_res[0] if skills_res else 0,
            "min_date": dates_res[0] if dates_res else None,
            "max_date": dates_res[1] if dates_res else None
        }
    finally:
        conn.close()

def get_market_insights(filters):
    """Fetch top records for the dashboard insights box."""
    where_clause, params = build_where_clause(filters)
    conn = get_db_connection()
    try:
        # Top Job Title
        q_title = f"SELECT job_title, COUNT(*) as c FROM cleaned_jobs {where_clause} GROUP BY job_title ORDER BY c DESC LIMIT 1"
        r_title = conn.execute(q_title, params).fetchone()
        top_title = r_title[0].title() if r_title else "N/A"
        
        # Top Skill
        q_skill = f"""
        SELECT skill, COUNT(*) as c 
        FROM (SELECT unnest(string_split(job_skills, ',')) AS skill FROM cleaned_jobs {where_clause}) 
        WHERE skill != '' AND skill != 'nan'
        GROUP BY skill 
        ORDER BY c DESC 
        LIMIT 1
        """
        r_skill = conn.execute(q_skill, params).fetchone()
        top_skill = r_skill[0].title() if r_skill else "N/A"
        
        # Top Location (City + Country)
        q_loc = f"SELECT search_city, search_country, COUNT(*) as c FROM cleaned_jobs {where_clause} GROUP BY search_city, search_country ORDER BY c DESC LIMIT 1"
        r_loc = conn.execute(q_loc, params).fetchone()
        if r_loc:
            top_location = f"{r_loc[0].title()}, {r_loc[1].title()}"
        else:
            top_location = "N/A"
            
        # Top Job Type
        q_type = f"SELECT job_type, COUNT(*) as c FROM cleaned_jobs {where_clause} GROUP BY job_type ORDER BY c DESC LIMIT 1"
        r_type = conn.execute(q_type, params).fetchone()
        top_type = r_type[0].title() if r_type else "N/A"
        
        # Top Job Level
        q_level = f"SELECT job_level, COUNT(*) as c FROM cleaned_jobs {where_clause} GROUP BY job_level ORDER BY c DESC LIMIT 1"
        r_level = conn.execute(q_level, params).fetchone()
        top_level = r_level[0].title() if r_level else "N/A"
        
        return {
            "top_title": top_title,
            "top_skill": top_skill,
            "top_location": top_location,
            "top_type": top_type,
            "top_level": top_level
        }
    finally:
        conn.close()

def get_job_posting_trend(filters, granularity="Daily"):
    """Get count of job postings grouped by day or month."""
    where_clause, params = build_where_clause(filters)
    
    if granularity == "Daily":
        date_expr = "strftime(first_seen, '%Y-%m-%d')"
    else:
        date_expr = "strftime(first_seen, '%Y-%m')"
        
    query = f"""
    SELECT {date_expr} AS period, COUNT(*) AS count
    FROM cleaned_jobs
    {where_clause}
    GROUP BY period
    ORDER BY period
    """
    return execute_query(query, params)

def get_top_job_titles(filters, limit=10):
    """Retrieve top job titles by posting count."""
    where_clause, params = build_where_clause(filters)
    query = f"""
    SELECT job_title, COUNT(*) AS count
    FROM cleaned_jobs
    {where_clause}
    GROUP BY job_title
    ORDER BY count DESC
    LIMIT {limit}
    """
    df = execute_query(query, params)
    if not df.empty:
        df["job_title"] = df["job_title"].str.title()
    return df

def get_top_hiring_companies(filters, limit=15):
    """Retrieve top hiring companies by posting count."""
    where_clause, params = build_where_clause(filters)
    query = f"""
    SELECT company, COUNT(*) AS count
    FROM cleaned_jobs
    {where_clause}
    GROUP BY company
    ORDER BY count DESC
    LIMIT {limit}
    """
    df = execute_query(query, params)
    if not df.empty:
        df["company"] = df["company"].str.title()
    return df

def get_job_type_distribution(filters, limit=8):
    """Get the distribution of job types."""
    where_clause, params = build_where_clause(filters)
    query = f"""
    SELECT job_type AS type, COUNT(*) AS count
    FROM cleaned_jobs
    {where_clause}
    GROUP BY job_type
    ORDER BY count DESC
    LIMIT {limit}
    """
    df = execute_query(query, params)
    if not df.empty:
        df["type"] = df["type"].str.title()
    return df

def get_job_level_distribution(filters, limit=10):
    """Get the distribution of job levels."""
    where_clause, params = build_where_clause(filters)
    query = f"""
    SELECT job_level AS level, COUNT(*) AS count
    FROM cleaned_jobs
    {where_clause}
    GROUP BY job_level
    ORDER BY count DESC
    LIMIT {limit}
    """
    df = execute_query(query, params)
    if not df.empty:
        df["level"] = df["level"].str.title()
    return df

def get_role_vs_type(filters, limit=10):
    """Get job role breakdown by employment type for top roles."""
    where_clause, params = build_where_clause(filters)
    
    # We use a subquery to find top roles under active filters
    query = f"""
    WITH top_roles AS (
        SELECT job_title
        FROM cleaned_jobs
        {where_clause}
        GROUP BY job_title
        ORDER BY COUNT(*) DESC
        LIMIT {limit}
    )
    SELECT job_title, job_type, COUNT(*) AS count
    FROM cleaned_jobs
    {where_clause} {"AND" if where_clause else "WHERE"} job_title IN (SELECT job_title FROM top_roles)
    GROUP BY job_title, job_type
    ORDER BY job_title, count DESC
    """
    df = execute_query(query, params + params)
    if not df.empty:
        df["job_title"] = df["job_title"].str.title()
        df["job_type"] = df["job_type"].str.title()
    return df

def get_level_vs_type(filters):
    """Get experience level breakdown mapped against employment types."""
    where_clause, params = build_where_clause(filters)
    query = f"""
    SELECT job_level, job_type, COUNT(*) AS count
    FROM cleaned_jobs
    {where_clause}
    GROUP BY job_level, job_type
    ORDER BY job_level, count DESC
    """
    df = execute_query(query, params)
    if not df.empty:
        df["job_level"] = df["job_level"].str.title()
        df["job_type"] = df["job_type"].str.title()
    return df

def get_role_vs_level(filters, limit=10):
    """Get job role breakdown by experience level for top roles."""
    where_clause, params = build_where_clause(filters)
    query = f"""
    WITH top_roles AS (
        SELECT job_title
        FROM cleaned_jobs
        {where_clause}
        GROUP BY job_title
        ORDER BY COUNT(*) DESC
        LIMIT {limit}
    )
    SELECT job_title, job_level, COUNT(*) AS count
    FROM cleaned_jobs
    {where_clause} {"AND" if where_clause else "WHERE"} job_title IN (SELECT job_title FROM top_roles)
    GROUP BY job_title, job_level
    ORDER BY job_title, count DESC
    """
    df = execute_query(query, params + params)
    if not df.empty:
        df["job_title"] = df["job_title"].str.title()
        df["job_level"] = df["job_level"].str.title()
    return df

def get_skills_count_distribution(filters):
    """Calculate the distribution of the number of skills required per job."""
    where_clause, params = build_where_clause(filters)
    query = f"""
    SELECT 
        CASE WHEN job_skills = '' THEN 0 ELSE len(string_split(job_skills, ',')) END AS skill_count,
        COUNT(*) AS job_count
    FROM cleaned_jobs
    {where_clause}
    GROUP BY skill_count
    ORDER BY skill_count
    """
    return execute_query(query, params)

def get_top_skills_filtered(filters, limit=20):
    """Extract and aggregate top skills from job descriptions."""
    where_clause, params = build_where_clause(filters)
    query = f"""
    SELECT skill, COUNT(*) AS count
    FROM (
        SELECT unnest(string_split(job_skills, ',')) AS skill
        FROM cleaned_jobs
        {where_clause}
    )
    WHERE skill != '' AND skill != 'nan'
    GROUP BY skill
    ORDER BY count DESC
    LIMIT {limit}
    """
    df = execute_query(query, params)
    if not df.empty:
        df["skill_name"] = df["skill"].str.title()
    return df

def get_skill_role_heatmap(filters):
    """Build cross-tabulation data of Skills vs Job Roles."""
    where_clause, params = build_where_clause(filters)
    
    conn = get_db_connection()
    try:
        # 1. Fetch top 10 job titles
        q_titles = f"SELECT job_title FROM cleaned_jobs {where_clause} GROUP BY job_title ORDER BY COUNT(*) DESC LIMIT 10"
        top_roles = [r[0] for r in conn.execute(q_titles, params).fetchall()]
        if not top_roles:
            return None
            
        # 2. Fetch top 15 skills in these roles
        # We need to construct parameters for IN clause
        role_placeholders = ",".join(["?"] * len(top_roles))
        q_skills = f"""
        SELECT skill, COUNT(*) AS count
        FROM (
            SELECT unnest(string_split(job_skills, ',')) AS skill
            FROM cleaned_jobs
            {where_clause} {"AND" if where_clause else "WHERE"} job_title IN ({role_placeholders})
        )
        WHERE skill != '' AND skill != 'nan'
        GROUP BY skill
        ORDER BY count DESC
        LIMIT 15
        """
        
        # Combine parameters
        skills_params = params + top_roles
        top_skills = [r[0] for r in conn.execute(q_skills, skills_params).fetchall()]
        if not top_skills:
            return None
            
        # 3. Query counts of these skills within these roles
        skills_placeholders = ",".join(["?"] * len(top_skills))
        q_matrix = f"""
        SELECT job_title, skill, COUNT(*) AS count
        FROM (
            SELECT job_title, unnest(string_split(job_skills, ',')) AS skill
            FROM cleaned_jobs
            {where_clause} {"AND" if where_clause else "WHERE"} job_title IN ({role_placeholders})
        )
        WHERE skill IN ({skills_placeholders})
        GROUP BY job_title, skill
        """
        matrix_params = params + top_roles + top_skills
        matrix_df = conn.execute(q_matrix, matrix_params).df()
        
        # 4. Fetch total job count per title to calculate percentage
        q_totals = f"""
        SELECT job_title, COUNT(*) AS total
        FROM cleaned_jobs
        {where_clause} {"AND" if where_clause else "WHERE"} job_title IN ({role_placeholders})
        GROUP BY job_title
        """
        totals_params = params + top_roles
        totals_df = conn.execute(q_totals, totals_params).df()
        
        # Calculate percentages
        merged = matrix_df.merge(totals_df, on="job_title")
        merged["percentage"] = (merged["count"] / merged["total"] * 100).round(1)
        
        # Pivot the data
        pivot_df = merged.pivot(index="job_title", columns="skill", values="percentage").fillna(0)
        
        # Reorder rows and columns to match descending order of role count and skill count
        # For readability, format titles
        pivot_df.index = [r.title() for r in pivot_df.index]
        pivot_df.columns = [s.title() for s in pivot_df.columns]
        
        return pivot_df
    except Exception as e:
        print("Error generating heatmap:", e)
        return None
    finally:
        conn.close()

def get_location_demand_map(filters):
    """Retrieve Country-wise job posting counts."""
    where_clause, params = build_where_clause(filters)
    query = f"""
    SELECT search_country AS country, COUNT(*) AS count
    FROM cleaned_jobs
    {where_clause}
    GROUP BY search_country
    ORDER BY count DESC
    """
    df = execute_query(query, params)
    if not df.empty:
        df["country_name"] = df["country"].str.title()
    return df

def get_top_countries(filters, limit=15):
    """Retrieve top search countries."""
    where_clause, params = build_where_clause(filters)
    query = f"""
    SELECT search_country AS country, COUNT(*) AS count
    FROM cleaned_jobs
    {where_clause}
    GROUP BY search_country
    ORDER BY count DESC
    LIMIT {limit}
    """
    df = execute_query(query, params)
    if not df.empty:
        df["country"] = df["country"].str.title()
    return df

def get_top_cities(filters, limit=15):
    """Retrieve top search cities."""
    where_clause, params = build_where_clause(filters)
    query = f"""
    SELECT search_city AS city, COUNT(*) AS count
    FROM cleaned_jobs
    {where_clause}
    GROUP BY search_city
    ORDER BY count DESC
    LIMIT {limit}
    """
    df = execute_query(query, params)
    if not df.empty:
        df["city"] = df["city"].str.title()
    return df

def get_top_locations(filters, limit=25):
    """Retrieve top job locations."""
    where_clause, params = build_where_clause(filters)
    query = f"""
    SELECT job_location AS location, COUNT(*) AS count
    FROM cleaned_jobs
    {where_clause}
    GROUP BY job_location
    ORDER BY count DESC
    LIMIT {limit}
    """
    df = execute_query(query, params)
    if not df.empty:
        df["location"] = df["location"].str.title()
    return df

def search_jobs(filters, limit=200):
    """Search for jobs based on dynamic filters."""
    where_clause, params = build_where_clause(filters)
    query = f"""
    SELECT job_title, company, job_location, job_type, job_level, job_skills, job_link
    FROM cleaned_jobs
    {where_clause}
    LIMIT {limit}
    """
    return execute_query(query, params)

def get_recommendations_sql(skills, limit=200):
    """Get job recommendations based on skill overlap directly in SQL."""
    if not skills:
        return pd.DataFrame()
    skills_lower = [s.strip().lower() for s in skills if s.strip()]
    if not skills_lower:
        return pd.DataFrame()
        
    contains_clause = " OR ".join(["contains(job_skills, ?)" for _ in skills_lower])
    
    query = f"""
    SELECT 
        job_title, 
        company, 
        job_location, 
        job_skills, 
        job_type, 
        job_level, 
        job_link,
        (len(list_intersect(list_transform(string_split(job_skills, ','), x -> trim(lower(x))), ?)) * 1.0 / {len(skills_lower)}) AS match_score
    FROM cleaned_jobs
    WHERE ({contains_clause})
      AND len(list_intersect(list_transform(string_split(job_skills, ','), x -> trim(lower(x))), ?)) > 0
    ORDER BY match_score DESC, first_seen DESC
    LIMIT ?
    """
    
    # Align parameters with placeholder positions:
    # 1. SELECT list_intersect: skills_lower (list)
    # 2. contains_clause: each skill (strings)
    # 3. WHERE list_intersect: skills_lower (list)
    # 4. LIMIT: limit (int)
    params = [skills_lower] + skills_lower + [skills_lower, limit]
    
    df = execute_query(query, params)
    if not df.empty:
        df["job_title"] = df["job_title"].str.title()
        df["company"] = df["company"].str.title()
        df["job_location"] = df["job_location"].str.title()
        df["job_skills"] = df["job_skills"].str.upper()
        df["job_type"] = df["job_type"].str.title()
        df["job_level"] = df["job_level"].str.title()
    return df
