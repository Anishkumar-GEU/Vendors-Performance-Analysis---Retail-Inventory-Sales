import pandas as pd
from sqlalchemy import create_engine,text
from sqlalchemy.engine import URL
from IPython.display import display
import numpy as np

import logging
import time


# logging basic config.
logging.basicConfig(
    filename="logs/get_vendor_summary.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s -%(message)s",
    filemode="a"
)

MYSQL_USER = "root"
MYSQL_PASSWORD = "password"
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
DATABASE_NAME = "inventory"

# Creating engine to connect with the database.
database_url = URL.create(
    drivername="mysql+pymysql",
        username=MYSQL_USER,
        password=MYSQL_PASSWORD,
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        database=DATABASE_NAME
)

engine = create_engine(database_url)

tables = pd.read_sql("SHOW TABLES FROM inventory;", engine)
# print(tables.columns)

# Let's see the data of all the tables.
for table in tables['Tables_in_inventory']:
    print("_"*50,f"{table}","_"*50)
    print("Count of records: ", pd.read_sql(f"select count(*) as count from {table}",engine)['count'].values[0])
    display(pd.read_sql(f"select * from {table} limit 5",engine))


# Considering vendor number 4466.
purchases = pd.read_sql("select * from purchases where vendornumber = 4466 ",engine)
print(purchases)

purchase_prices = pd.read_sql_query("select * from purchase_prices where vendornumber = 4466", engine)
print(purchase_prices)

vendor_invoice = pd.read_sql_query("select * from vendor_invoice where vendornumber = 4466", engine)
print(vendor_invoice)

sales = pd.read_sql_query("select * from sales where vendorno = 4466", engine)
print(sales)


print(purchases.groupby(['brand','purchaseprice'])[['quantity','dollars']].sum())
print(sales.groupby('brand')[['salesdollars','salesprice','salesquantity']].sum())




#  Freight summary table
freight_summary = pd.read_sql_query("select vendornumber, SUM(freight) as FreightCost from vendor_invoice group by vendornumber",engine)
print(freight_summary)


# -- Price summary table
print(pd.read_sql_query(
    """
    SELECT 
    p.vendornumber,
    p.vendorname,
    p.brand,
    p.purchaseprice,
    pp.volume,
    pp.price as ActualPrice,
    SUM(p.Quantity) as TotalPurchaseQuantity,
    SUM(p.Dollars) as TotalPurchaseDollars
    FROM purchases p
    JOIN purchase_prices pp
    ON p.brand = pp.brand
    WHERE p.purchaseprice>0
    GROUP BY p.vendornumber, p.vendorname, p.brand,p.purchaseprice,pp.volume,pp.price
    ORDER BY TotalPurchaseDollars
    """, engine
))


# -- Sales summary table.
print(
    pd.read_sql_query(
        """
SELECT vendorno,
brand,
SUM(salesdollars) AS TotalSalesDollars,
SUM(salesprice) AS TotalSalesPrice,
SUM(salesquantity) AS TotalSalesQuantity,
SUM(excisetax) AS TotalExciseTax
FROM sales
GROUP BY vendorno, brand
ORDER BY TotalSalesDollars
""", engine
    )
)


# -------------------------------------TIME TAKING APPROACH------------------------------------------------
# start= time.time()
# final_table = pd.read_sql_query("""
# SELECT
# pp.vendornumber,
# pp.brand,
# pp.price AS ActualPrice,
# pp.purchaseprice,
# SUM(s.salesquantity) AS TotalSalesQuantity,
# SUM(s.salesdollars) AS TotalSalesDollars,
# SUM(s.salesprice) AS TotalSalesPrice,
# SUM(s.excisetax) AS TotalExciseTax,
# SUM(vi.quantity) AS TotalPurchaseQuantity,
# SUM(vi.dollars) AS TotalPurchaseDollars,
# SUM(vi.freight) AS TotalFreightCost

# FROM purchase_prices pp 
# JOIN sales s
#     ON pp.vendornumber=s.vendorno AND pp.brand = s.brand
# JOIN vendor_invoice vi
#     ON pp.vendornumber = vi.vendornumber
# GROUP BY pp.vendornumber, pp.brand,pp.price,pp.purchaseprice
# """,engine)
# end = time.time()

vendor_sales_summary = pd.read_sql_query("""
WITH freightsummary AS (
    SELECT vendornumber, SUM(freight) AS freightcost
    FROM vendor_invoice 
    GROUP BY vendornumber
),
purchasesummary AS(
    SELECT 
    p.vendornumber,
    p.vendorname,
    p.brand,
    p.description,
    p.purchaseprice,
    pp.price as actualprice,
    pp.volume,
    SUM(p.quantity) AS totalpurchasequantity,
    SUM(p.dollars) AS totalpurchasedollars
    FROM purchases p JOIN purchase_prices pp
    ON p.brand=pp.brand
    WHERE p.purchaseprice>0
    GROUP BY p.vendornumber,p.vendorname,p.brand,p.description,p.purchaseprice,pp.price,pp.volume
),
salessummary AS( 
    SELECT 
    vendorno,
    brand,
    SUM(salesquantity) as totalsalesquantity,
    SUM(salesdollars) as totalsalesdollars,
    SUM(salesprice) AS totalsalesprice,
    SUM(excisetax) as totalexcisetax
    FROM sales
    GROUP BY vendorno, brand
)

SELECT 
    ps.vendornumber,
    ps.vendorname,
    ps.brand,
    ps.description,
    ps.purchaseprice,
    ps.actualprice,
    ps.volume,
    ps.totalpurchasequantity,
    ps.totalpurchasedollars,
    ss.totalsalesquantity,
    ss.totalsalesdollars,
    ss.totalsalesprice,
    ss.totalexcisetax,
    fs.freightcost
FROM purchasesummary ps 
LEFT JOIN salessummary ss
    ON ps.vendornumber= ss.vendorno
    AND ps.brand = ss.brand
LEFT JOIN freightsummary fs
    ON ps.vendornumber = fs.vendornumber
ORDER BY ps.totalpurchasedollars DESC

""",engine)


vendor_sales_summary['volume'] = vendor_sales_summary['volume'].astype('float64')
vendor_sales_summary.fillna(0,inplace=True)
vendor_sales_summary['vendorname']=vendor_sales_summary['vendorname'].str.strip()


# creating new measures.
vendor_sales_summary['grossprofit'] = vendor_sales_summary['totalsalesdollars']-vendor_sales_summary['totalpurchasedollars']

vendor_sales_summary['profitmargin'] = (vendor_sales_summary['grossprofit'] / vendor_sales_summary['totalsalesdollars']) * 100 

vendor_sales_summary['stockturnover'] = vendor_sales_summary['totalsalesquantity'] / vendor_sales_summary['totalpurchasequantity']

vendor_sales_summary['salestopurchaseratio'] = vendor_sales_summary['totalsalesdollars'] / vendor_sales_summary['totalpurchasedollars']

#Handle infinity created due to division by zero.
vendor_sales_summary.replace([np.inf, -np.inf], 0, inplace=True)

# Inserting into Mysql.
start = time.time()
vendor_sales_summary.to_sql(
    name='vendor_sales_summary',
    con=engine,
    if_exists='replace',
    index=False
)
end = time.time()
total_time = (end-start)/60
logging.info("vendor_sales_summary table created successfully.")
logging.info(f"Total Time Taken: {total_time} minutes")
