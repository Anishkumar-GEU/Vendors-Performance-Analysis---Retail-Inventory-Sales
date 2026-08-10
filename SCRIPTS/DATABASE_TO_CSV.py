import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="inventory"
)

query = "SELECT * FROM vendor_sales_summary"

df = pd.read_sql(query, conn)

df.to_csv(
    "vendor_sales_summary.csv",
    index=False,
    encoding="utf-8-sig"
)

conn.close()

print("CSV file created successfully.")