import seaborn as sns
import matplotlib.pyplot as plt

df = sns.load_dataset("titanic")
plt.subplot(1, 4, 1)
sns.barplot(x='who', y='age', data=df, color='darkgreen', hue='sex', palette='spring', ci=False, saturation=0.9)

plt.subplot(1, 4, 2)
sns.lineplot(x='who', y='age', data=df, color='darkgreen', hue='sex', palette='spring')

plt.subplot(1, 4, 3)
sns.stripplot(x='who', y='age', data=df, hue='sex', palette='spring', dodge=True, alpha=0.6)
plt.title("Stripplot")

plt.subplot(1, 4, 4)
sns.pairplot(df[['age', 'fare', 'pclass', 'sex']], hue='sex', diag_kind='kde')

plt.show()
