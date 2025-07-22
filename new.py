import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#Task one Data cleaning (pandas)
df=pd.read_csv('C:\\Users\Abdul Sattar\Downloads\weather_data.csv')

fill=df.fillna(0)
print(fill)

date=df['Date']=pd.to_datetime(df['Date'])
print(date)


print(df.head(5))
#one extra thing 
print(df.describe())

#Step 2: Data Analysis (Pandas + NumPy)
mean=np.mean(df['Temperature (°C)'])
print(f"Mean ={mean}")

max=np.max(df['Humidity (%)'])
print(f"Maximum Raning = {max}")

min=np.min(df['Humidity (%)'])
print(f"Minimum Raning={min}")

start_Date='2025-01-01'
ending_date='2025-02-01'

date=df[(df['Date'] > start_Date)  & (df['Date'] <ending_date )]
print(date)

#days=df['Date'].sum()
#print(f"Totel Days of Raning ={days}")

data = df.groupby(df['Date'].dt.month)['Temperature (°C)'].mean()
print(f'Values which in mean={data}')

Standered_deviations=np.std(df['Temperature (°C)'])
print(f"Standered_deviations {Standered_deviations}")

# use Numpy to:
max=np.max(df['Temperature (°C)'])
print(f"Maximum Temperature = {max}")

min=np.min(df['Temperature (°C)'])
print(f"Minimum Temperature ={min}")

#Step 3: Visualization (Matplotlib)
plt.subplot(1,3,1)
plt.plot(df['Date'],df['Temperature (°C)'],marker='*',color='Blue',mfc='r',mec='y',ms=20)
fonts={'family':'Times New Roman','size':20 , 'color':'red'}
plt.title("line ",fontdict=fonts)
plt.xlabel("Date",fontdict=fonts)
plt.ylabel("Temperature",fontdict=fonts)

plt.subplot(1,3,2)
plt.title("BAR",fontdict=fonts)
plt.xlabel("Date",fontdict=fonts)
plt.ylabel("Temperature",fontdict=fonts)
plt.bar(data.index, data.values, color='darkgreen')


plt.subplot(1,3,3)
plt.pie(data,autopct='%1.2f%%')
plt.title("PIE",fontdict=fonts)
plt.xlabel("Date",fontdict=fonts)
plt.ylabel("Temperature",fontdict=fonts)




plt.show()