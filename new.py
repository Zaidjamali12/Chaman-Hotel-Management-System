import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

#task 1: Read the CSV file
df=pd.read_csv("C:\\Users\Abdul Sattar\Downloads\sales_data.csv")
print(df.head(5))
print(df['Units Sold'].sum())

# task 2 colum cleanup
df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
print(df.columns)

# task 3:average total revenue.
print(df['total_revenue'].mean())

#task4:product lowest and highest price
print("Minimum and Maximum Unit Price:")
print(df['unit_price'].min())
print(df['unit_price'].max())

#task4:product lowest and highest price
highest_Prodcut = df.loc[df['unit_price'].idxmax()]
lowest_Product = df.loc[df['unit_price'].idxmin()]
print("Highest Priced Product:")
print(highest_Prodcut['product'], "with price:", highest_Prodcut['unit_price'])
print("Lowest Priced Product:")
print(lowest_Product['product'], "with price:", lowest_Product['unit_price'])

#Task 6: Bar chart of total revenue by region
df.groupby('region')['total_revenue'].sum().plot(kind='bar', color='skyblue')
plt.title('Total Revenue by Region')    
plt.xlabel('Region')
plt.ylabel('Total Revenue')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Task 7: Pie chart of units sold by product
df.groupby('product')['units_sold'].sum().plot(kind='pie', autopct='%1.1f%%', startangle=140)
plt.title('Units Sold by Product')
plt.ylabel('')
plt.tight_layout()
plt.show()

# Task 8: Line chart of total revenue over timex
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)
df['total_revenue'].resample('M').sum().plot(kind='line', marker='o', color='orange')
plt.title('Total Revenue Over Time')
plt.xlabel('Date')
plt.ylabel('Total Revenue')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
# Task 9:Correlation heatmap using seaborn

