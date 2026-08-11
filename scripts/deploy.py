import os
import glob
import snowflake.connector

conn = snowflake.connector.connect(
    account=os.environ["ACCOUNT"],
    user=os.environ["USER"],
    password=os.environ["PASSWORD"],
    database=os.environ["DATABASE"] 
)

cur = conn.cursor()

# Get deployed scripts
cur.execute("""
SELECT SCRIPT_NAME
FROM DEPLOYMENT_HISTORY
WHERE STATUS='SUCCESS'
""")

deployed = {row[0] for row in cur.fetchall()}

# Read repository SQL files
files = sorted(glob.glob("sql/*.sql"))

for file in files:

    script_name = os.path.basename(file)

    if script_name in deployed:
        print(f"Skipping {script_name}")
        continue

    print(f"Executing {script_name}")

    with open(file) as f:
        sql = f.read()

    try:

        cur.execute(sql)

        cur.execute("""
        INSERT INTO DEPLOYMENT_HISTORY
        (SCRIPT_NAME,
         DEPLOYED_AT,
         DEPLOYED_BY,
         STATUS)

        VALUES
        (%s,
         CURRENT_TIMESTAMP(),
         CURRENT_USER(),
         'SUCCESS')
        """,(script_name,))

        conn.commit()

        print(f"{script_name} deployed successfully")

    except Exception as e:

        conn.rollback()

        cur.execute("""
        INSERT INTO DEPLOYMENT_HISTORY
        (SCRIPT_NAME,
         DEPLOYED_AT,
         DEPLOYED_BY,
         STATUS)

        VALUES
        (%s,
         CURRENT_TIMESTAMP(),
         CURRENT_USER(),
         'FAILED')
        """,(script_name,))

        conn.commit()

        raise e

cur.close()
conn.close()
