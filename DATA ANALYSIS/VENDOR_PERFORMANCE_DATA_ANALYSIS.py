import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from scipy.stats import ttest_ind
import scipy.stats as stats

from sqlalchemy import create_engine,text
from sqlalchemy.engine import URL
from IPython.display import display


import logging
import time

warnings.filterwarnings('ignore')

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

# fetching vendor summary data.
# df = pd.read_sql_query("select * from vendor_sales_summary",engine)

# summary statistics
# print(df.describe().T) 

# Distribution plots for Numerical Columns
# numerical_cols = df.select_dtypes(include=np.number).columns

# plt.figure(figsize=(15,10))
# for i, col in enumerate(numerical_cols):
#     plt.subplot(4,4,i+1) # adjust grid layout as needed
#     sns.histplot(df[col], kde=True, bins=30)
#     plt.title(col)
# plt.tight_layout()
# # plt.show()


# # box plot
# plt.figure(figsize=(15,10))
# for i,col in enumerate(numerical_cols):
#     plt.subplot(4,4,i+1)
#     sns.boxplot(y=df[col])
#     plt.title(col)
# plt.tight_layout()
# plt.show() 

# we have insights in the report according to these plots.


# let's filter the data by removing inconsistencies.
df = pd.read_sql_query(
    '''
    SELECT * FROM vendor_sales_summary 
    WHERE grossprofit > 0 
    AND profitmargin > 0 
    AND totalsalesquantity>0
''', engine
)

# Distribution plots for Numerical Columns
# numerical_cols = df.select_dtypes(include=np.number).columns

# plt.figure(figsize=(15,10))
# for i, col in enumerate(numerical_cols):
#     plt.subplot(4,4,i+1) # adjust grid layout as needed
#     sns.histplot(df[col], kde=True, bins=30)
#     plt.title(col)
# plt.tight_layout()



# box plot
# plt.figure(figsize=(15,10))
# for i,col in enumerate(numerical_cols):
#     plt.subplot(4,4,i+1)
#     sns.boxplot(y=df[col])
#     plt.title(col)
# plt.tight_layout()

# Count plots for Categorial colums.

# categorial_cols = ['vendorname','description']

# plt.figure(figsize=(12,5))
# for i , col in enumerate(categorial_cols):
#     plt.subplot(1,2,i+1)
#     sns.countplot(y=df[col], order=df[col].value_counts().index[:10]) # top 10 categories
#     plt.title(f"Count plot of {col}")
# plt.tight_layout()


# Correlation heatmap
# plt.figure(figsize=(12,8))
# correlation_matrix = df[numerical_cols].corr()
# sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap= "coolwarm", linewidths=0.5)
# plt.title("correlation heatmap")
# plt.show()

# we have correlation insights in the report












#function for dollars value formatting
def format_dollars(value):
    if value>= 1_000_000:
        return f"{value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value/ 1_000:.2f}K"
    else :
        return str(value)




# ----------------------DATA ANALYSIS

# Question 1 :- identify brand that needs promotional or pricing adjustments which exhibit lower sales performance but higher profit margins.

brand_performance = df.groupby('description').agg({
    'totalsalesdollars':'sum',
    'profitmargin':'mean'
}).reset_index()
low_sales_threshold = brand_performance['totalsalesdollars'].quantile(0.15)

high_margin_threshold = brand_performance['profitmargin'].quantile(0.85)

# filter brands with low sales but high profit margins
target_brand = brand_performance[
    (brand_performance['totalsalesdollars']<= low_sales_threshold) & 
    (brand_performance['profitmargin']>= high_margin_threshold)
] 
print("brand with low sales but high profit margins:")
display(target_brand.sort_values('totalsalesdollars'))
#scatter plot
brand_performance = brand_performance[brand_performance['totalsalesdollars']<1000] # just for better visulization 
plt.figure(figsize=(10,6))
sns.scatterplot(data=brand_performance , x='totalsalesdollars' , y='profitmargin' , color="blue" , label = "All Brands" , alpha = 0.2)
sns.scatterplot(data=target_brand , x='totalsalesdollars' , y='profitmargin' , color="red" , label="Target Brands")

plt.axhline(high_margin_threshold, linestyle = '--', color="black", label="High Margin Threshold")
plt.axvline(low_sales_threshold, linestyle = '--', color="black", label="Low Sales Threshold")

plt.xlabel("Total Sales($)")
plt.ylabel("Profit Margin(%)")
plt.title("Brands for Promotional or Pricing Adjustments")
plt.legend()
plt.grid(True)
plt.show()


# Question 2 :- Which vendors and brands demonstrate the highest sales performance?

# top vendors and brands by sales performance
top_vendors  =  df.groupby("vendorname")['totalsalesdollars'].sum().nlargest(10)
top_brands  =  df.groupby("description")['totalsalesdollars'].sum().nlargest(10)
print(top_brands.apply(lambda x : format_dollars(x)))
print(top_vendors.apply(lambda x : format_dollars(x)))

# plot for top_vendors
plt.figure(figsize=(15,5))
plt.subplot(1,2,1)
ax1=sns.barplot(y=top_vendors.index, x=top_vendors.values, palette="Blues_r")
plt.title("Top 10 vendors by sales")

for bar in ax1.patches:
    ax1.text(bar.get_width() + (bar.get_width()*.02),
             bar.get_y() + bar.get_height() / 2,
             format_dollars(bar.get_width()),
             ha='left', va='center', fontsize=10, color='black')
# plot for top brands
plt.subplot(1,2,2)
ax2 = sns.barplot(y=top_brands.index.astype(str), x=top_brands.values, palette= "Reds_r")
plt.title("Top 10 Brands by Sales")

for bar in ax2.patches:
    ax2.text(bar.get_width() + (bar.get_width()*.02),
             bar.get_y() + bar.get_height() / 2,
             format_dollars(bar.get_width()),
             ha='left', va='center', fontsize=10, color='black')
plt.tight_layout()
plt.show()


# Problem 3 :- Which vendors contribute the most to total purchase dollars?
vendor_performance = df.groupby('vendorname').agg({
    'totalpurchasedollars':'sum',
    'grossprofit':'sum',
    'totalsalesdollars':'sum'
}).reset_index()
vendor_performance['purchasecontribution%'] = vendor_performance['totalpurchasedollars']/ vendor_performance['totalpurchasedollars'].sum()*100
vendor_performance = round(vendor_performance.sort_values('purchasecontribution%', ascending=False),2)

top_vendors = vendor_performance.head(10)
top_vendors['totalsalesdollars'] = top_vendors['totalsalesdollars'].apply(format_dollars)
top_vendors['totalpurchasedollars'] = top_vendors['totalpurchasedollars'].apply(format_dollars)
top_vendors['grossprofit'] = top_vendors['grossprofit'].apply(format_dollars)

top_vendors['cumulativecontribution%']= top_vendors['purchasecontribution%'].cumsum()

# cumulative plot
fig,ax1=plt.subplots(figsize=(10,6))
# bar plot for contribution
sns.barplot(x= top_vendors['vendorname'], y=top_vendors['purchasecontribution%'], palette="mako" , ax =ax1)

for i,value in enumerate(top_vendors['purchasecontribution%']):
    ax1.text(i,value-1,str(value)+'%',ha='center',fontsize=10, color='white')

# line plot for cumulative contribution
ax2 = ax1.twinx()
ax2.plot(top_vendors['vendorname'], top_vendors['cumulativecontribution%'], color ='red' , marker='o', linestyle='dashed', label='cumulative_contribution')
ax1.set_xticklabels(top_vendors['vendorname'],rotation=90)
ax1.set_ylabel('purchase contribution %', color='blue')
ax2.set_ylabel('cumulative contribution %', color='red')
ax1.set_xlabel('vendors')
ax1.set_title('Pareto Chart: Vendor Contribution to Total Purchases')

ax2.axhline(y=100, color='gray', linestyle='dashed', alpha=0.7)
ax2.legend(loc='upper right')




# Problem 4 :- How much of total procurement is dependent on the top vendors?
print(
    f"Total Purchase Contribution of top 10 vendors is {round(top_vendors['purchasecontribution%'].sum(),2)}%"
)
vendors = list(top_vendors['vendorname'].values)
purchase_contribution = list(top_vendors['purchasecontribution%'].values)
total_contribution = sum(purchase_contribution)
remaining_contribution = 100-total_contribution

#append "other vendors" category
vendors.append("other vendors")
purchase_contribution.append(remaining_contribution)


#donut chart
fig,ax=plt.subplots(figsize=(8,8))
wedges, texts, autotexts = ax.pie(purchase_contribution, labels=vendors,autopct='%1.1f%%', startangle=140, pctdistance=0.85, colors=plt.cm.Paired.colors)

# Draw a white circle in the centre to create a "donut" effect
centre_circle = plt.Circle((0,0), 0.70, fc='white')
fig.gca().add_artist(centre_circle)

# Add total contribution annotation in the center
plt.text(0,0,f"Top 10 Total:\n{total_contribution:.2f}%", fontsize=14, fontweight='bold', ha='center', va='center')
plt.title("Top 10 Vendor's Purchase Contribution (%)")
plt.show()


# Does purchasing in bulk reduce the unit price, and what is the optimal purchase volume for cost savings?
df['unitpurchaseprice']=df['totalpurchasedollars']/df['totalpurchasequantity']
df['ordersize'] = pd.qcut(df['totalpurchasequantity'], q=3, labels=['small','medium','large'])
print(df.groupby('ordersize')[['unitpurchaseprice']].mean())

plt.figure(figsize=(10,6))
sns.boxplot(data=df,x='ordersize',y='unitpurchaseprice',palette='Set2')
plt.title("Impact of Bulk Purchasing on Unit Price")
plt.xlabel("Order Size")
plt.ylabel("Average Unit Purchase Price")
plt.show()


# Problem 5 :- Which vendors have low inventory turnover, indicating excess stock and slow-moving products?
print(df[df['stockturnover']<1].groupby('vendorname')[['stockturnover']].mean().sort_values('stockturnover',ascending=True).head(10))


# Problem 6 :- How much capital is locked in unsold inventory per vendor, and which vendors contribute the most to it?
df['unsoldinventoryvalue']=(df['totalpurchasequantity']-df['totalsalesquantity'])*df['purchaseprice']
print('Total Unsold Capital:', format_dollars(df['unsoldinventoryvalue'].sum()))
# Aggregate Capital locked per vendor
inventory_value_per_vendor = df.groupby('vendorname')['unsoldinventoryvalue'].sum().reset_index()

# sort vendors with the highest locked capital.
inventory_value_per_vendor = inventory_value_per_vendor.sort_values(by='unsoldinventoryvalue', ascending = False)
inventory_value_per_vendor['unsoldinventoryvalue'] = inventory_value_per_vendor['unsoldinventoryvalue'].apply(format_dollars)
print(inventory_value_per_vendor.head(10))



# Problem 7:- What is the 95% confidence intervals for profit margins of top-performing and low-performing vendors.
top_threshold = df['totalsalesdollars'].quantile(0.75)
low_threshold = df['totalsalesdollars'].quantile(0.25)

top_vendors = df[df['totalsalesdollars']>= top_threshold]['profitmargin'].dropna()
low_vendors = df[df['totalsalesdollars']<= low_threshold]['profitmargin'].dropna()

# function for confidence interval
def confidence_interval(data, confidence=0.95):
    mean_val = np.mean(data)
    std_err = np.std(data, ddof=1)/np.sqrt(len(data)) # standard error
    t_critical = stats.t.ppf((1+confidence)/2, df= len(data)-1)
    margin_of_error = t_critical * std_err
    return mean_val, mean_val- margin_of_error, mean_val + margin_of_error

top_mean, top_lower, top_upper = confidence_interval(top_vendors)
low_mean, low_lower, low_upper = confidence_interval(low_vendors)

print(f"Top Vendors 95% CI : ({top_lower:.2f}, {top_upper:.2f}), Mean: {top_mean:.2f}")
print(f"low Vendors 95% CI : ({low_lower:.2f}, {low_upper:.2f}), Mean: {low_mean:.2f}")

plt.figure(figsize=(12,6))

# Top vendors plot
sns.histplot(top_vendors, kde=True, color="blue", bins = 30, alpha=0.5, label = "Top Vendors")
plt.axvline(top_lower,color="blue", linestyle='--', label=f"Top Lower: {top_lower:.2f}")
plt.axvline(top_upper,color="blue", linestyle='--', label=f"Top Upper: {top_upper:.2f}")
plt.axvline(top_mean,color="blue", linestyle='--', label=f"Top Mean: {top_mean:.2f}")

# Low vendors plot
sns.histplot(low_vendors, kde=True, color="red", bins = 30, alpha=0.5, label = "Low Vendors")
plt.axvline(low_lower,color="red", linestyle='--', label=f"Low Lower: {low_lower:.2f}")
plt.axvline(low_upper,color="red", linestyle='--', label=f"Low Upper: {low_upper:.2f}")
plt.axvline(low_mean,color="red", linestyle='--', label=f"Low Mean: {low_mean:.2f}")

# Finalize plot
plt.title("Confidence Interval Comparison: Top vs. Low Vendors (Profit Margin)")
plt.xlabel("Profit Margin (%)")
plt.ylabel("Frequency")
plt.legend()
plt.grid(True)
plt.show()


# Hypothesis testing
# Problem 8:- Is there a significant difference in profit margins between top-performing and low-performing vendors?
top_threshold = df['totalsalesdollars'].quantile(0.75)
low_threshold = df['totalsalesdollars'].quantile(0.25)

top_vendors = df[df['totalsalesdollars']>= top_threshold]['profitmargin'].dropna()
low_vendors = df[df['totalsalesdollars']<= low_threshold]['profitmargin'].dropna()

# Perform two - sample T-test
t_stat, p_value = ttest_ind(top_vendors, low_vendors, equal_var = False)

#Print results
print(f"T-Statistics: {t_stat:.4f}, P-Value: {p_value:.4f}")
if p_value < 0.5:
    print("Reject H0: There is a significant difference in profit margins between top and low-performing vendors.")
else:
    print("Fail to Reject H0: No significant difference in profit margins.")


