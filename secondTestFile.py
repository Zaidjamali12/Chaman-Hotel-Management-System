import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as date

df=pd.read_csv('C:\\Users\Abdul Sattar\Downloads\sales_data.csv')
df['Date']=pd.to_datetime(df['Date'])
# i have Chacked its null values, there are no value which have value
print(df.isnull().sum())
data=df.groupby(['Product','Total Revenue'])['Total Revenue'].sum().sort_values(ascending=False)
print(data)
sorteds=df.sort_values(by='Total Revenue' , ascending=False)
print(sorteds)
print(df.head(5))


#Part 2:
Find_mean=np.mean(df['Units Sold'])
print(f'Mean ={Find_mean}')

Standered_deviations=np.std(df['Units Sold'])
print('Standered_deviations',Standered_deviations)

df['Price']=df['Units Sold'] *0.9
print(df)