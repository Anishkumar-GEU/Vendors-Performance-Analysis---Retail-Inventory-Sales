import pandas as pd
import os

from sqlalchemy import create_engine,text
from sqlalchemy.engine import URL

import logging
import time

logging.basicConfig(
    filename="logs/ingestion_db.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s -%(message)s",
    filemode="a"
)


MYSQL_USER = "root"
MYSQL_PASSWORD = "password"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
DATABASE_NAME = "inventory"

CSV_FOLDER = "C:\\Users\\anish\\OneDrive\\Desktop\\Vendor_Performance_Data_Analysis"

# Creating an engine without selecting any database.

server_url = URL.create(
    drivername= "mysql+pymysql",
    username= MYSQL_USER,
    password=MYSQL_PASSWORD,
    host= MYSQL_HOST,
    port=MYSQL_PORT
)
server_engine = create_engine(server_url)

# Creating the database if the data base is not exist.
with server_engine.connect() as connection:
    connection.execute(
        text(
            f"""
                    CREATE DATABASE IF NOT EXISTS `{DATABASE_NAME}`
                    CHARACTER SET utf8mb4
                    COLLATE utf8mb4_unicode_ci
                    """
        )
    )
    connection.commit()
print(f" Database {DATABASE_NAME} created successfully.")


# Creating another engine to connect with the database.
database_url = URL.create(
    drivername="mysql+pymysql",
        username=MYSQL_USER,
        password=MYSQL_PASSWORD,
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        database=DATABASE_NAME
)

engine = create_engine(database_url)

# Function to create a valid Mysql table name.
def create_table_name(filename):
    table_name = os.path.splitext(filename)[0]
    table_name = table_name.lower().strip()

    return table_name


# Find and ingest all csv files after modifying the file names according to the table name
start = time.time()
csv_files=[
    file 
    for file in os.listdir(CSV_FOLDER)
    if file.lower().endswith(".csv")
]

if not csv_files:
    logging.info("No csv files found in the folder")
else:
    logging.info(f"{len(csv_files)} CSV files found.\n")

    for filename in csv_files:
        file_path = os.path.join(CSV_FOLDER, filename)
        table_name = create_table_name(filename)

        try:
            df = pd.read_csv(file_path)

            # clean column names
            df.columns = (
                df.columns
                .str.strip()
                .str.lower()
                .str.replace(r"[^a-z0-9]+","_",regex=True)
                .str.replace(r"_+","_",regex=True)
                .str.strip("_")
            )

            # insert the data frame into mysql database 
            df.to_sql(
                name= table_name,
                con= engine,
                if_exists="replace",
                index=False,
                chunksize=1000,
                method="multi"
            )
            logging.info(
                f"Loaded: {filename} -> {table_name}"
                f"({len(df):,}rows) in database"
            )
        except Exception as error:
            logging.info(f"Failed to load {filename}")
            logging.info(f"Error : {error}\n")



# Closing the database connection
engine.dispose()
server_engine.dispose()
end = time.time()
total_time = (end-start)/60
logging.info("\n CSV ingestion process completed.")
logging.info(f"Total Time Taken: {total_time} minutes")
