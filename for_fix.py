import psycopg2
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from PIL import Image
import datetime
from datetime import date


# 1. Считываю исходный df
df = pd.read_excel('output.xlsx')
df['volume'] = df['volume'].astype('int')

# 2. Делаю доп. расчеты (в тч длит-ть перекачки)
adding_columns = df.copy()
adding_columns['pump_days'] = adding_columns['end_pump'] - adding_columns['start_pump']
adding_columns['pump_days'] = adding_columns['pump_days'].dt.days.tolist()
adding_columns['pump_days'] = adding_columns['pump_days'] + 1

# 2.1 Добавляю 2 столбца: месяц начала перекачки/окончания перекачки
month_start, month_end = [], []
list_of_start = ([i for i in adding_columns['start_pump']])
for i in list_of_start:
    month_start.append(i.strftime("%B"))
adding_columns['month_start'] = month_start

list_of_end = ([i for i in adding_columns['end_pump']])
for i in list_of_end:
    month_end.append(i.strftime("%B"))
adding_columns['month_end'] = month_end

# 2.2 Добавляю проверку: перекачка шла в течение одного и того же месяца?
adding_columns['is_same_month'] = (adding_columns['month_start'] == adding_columns['month_end'])

# 3. Создаю 2 датафрейма:где перекачка велась в одном и том же месяце и в разных
df_month_false = adding_columns[adding_columns['is_same_month'] == False]
df_month_true = adding_columns[adding_columns['is_same_month'] == True]

# 3.1 Создаю две копии, работаю с НЕСОВПАДАЮЩИМИ месяцами (is_same_month = False)
table_same = df_month_true.copy()
table_not_same = df_month_false.copy()

# 3.2 Добавляю 2 столбца: сколько дней качали в первом месяце (starting_day) и сколько во втором (ending_day)
ending_day = []
list_of_days = ([i for i in table_not_same['end_pump']])
for i in list_of_days:
    ending_day.append(i.strftime("%d"))
table_not_same['ending_day'] = ending_day
table_not_same['ending_day'] = table_not_same['ending_day'].astype('int')
table_not_same['starting_day'] = table_not_same['pump_days'] - table_not_same['ending_day']

# 3.3 Добавляю 2 столбца: сколько газа качали в первом месяце (starting_day) и сколько во втором (ending_day)
table_not_same['volume_end'] = table_not_same['volume'] * table_not_same['ending_day'] / table_not_same['pump_days']
table_not_same['volume_end'] = table_not_same['volume_end'].astype('int')
table_not_same['volume_start'] = table_not_same['volume'] * table_not_same['starting_day'] / table_not_same['pump_days']
table_not_same['volume_start'] = table_not_same['volume_start'].astype('int')

# 3.4 Создаю df, где провожу группировку по месяцам
df_not_same = table_not_same.copy()
df_not_same_start = df_not_same.groupby('month_start', as_index=False) \
    .agg({'volume_start': 'sum'}) \
    .rename(columns={"month_start": "month_number"}) \
    .rename(columns={"volume_start": "volume"})
df_not_same_finish = df_not_same.groupby('month_end', as_index=False) \
    .agg({'volume_end': 'sum'}) \
    .rename(columns={"month_end": "month_number"}) \
    .rename(columns={"volume_end": "volume"})

# 3.5 Создаю итоговый df для перекачек, идущих в нескольких месяцах
df_not_same_union = pd.merge(df_not_same_finish, df_not_same_start, how="outer") \
    .groupby("month_number", as_index=False) \
    .agg({"volume": "sum"})

# 4 Работаю с СОВПАДАЮЩИМИ месяцами
df_same_union = table_same.groupby("month_start", as_index=False) \
    .agg({"volume": "sum"}) \
    .rename(columns={"month_start": "month_number"})


#5 Свожу всё в один df. На выходе объем перекачек по месяцам

sorter = ['Январь', 'Февраль', 'Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']

df_total = pd.merge(df_not_same_union, df_same_union, how="outer") \
    .groupby("month_number", as_index=False) \
    .agg({"volume": "sum"})

df_total.month_number = df_total.month_number.astype("category")
df_total.month_number.cat.set_categories(sorter, inplace=True)
df_total = df_total.sort_values(["month_number"])

st.table(df_total)
# 6 Строю графики
fig = go.Figure(
    data=[go.Bar(x=df_total['month_number'], y=df_total['volume'])],
    layout_title_text="Распределение объёма по месяцам"
)

st.plotly_chart(fig)