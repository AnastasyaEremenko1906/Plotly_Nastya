import psycopg2
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from PIL import Image
import datetime
from dateutil import relativedelta
from datetime import date


# 1. Считываю исходный df

df = pd.read_excel("https://github.com/AnastasyaEremenko1906/Plotly_Nastya/blob/6aa8fa2c071cd9900b4347df1ff6c56cd428d553/output.xlsx?raw=True")
df['volume'] = df['volume'].astype('int')
# 2. Перевожу даты в дататайп, считаю длит-ть перекачки + смотрю, была ли перекачка в одном и том же месяце

adding_columns = df.copy()
adding_columns["start_pump"] = pd.to_datetime(adding_columns["start_pump"])
adding_columns["end_pump"] = pd.to_datetime(adding_columns["end_pump"])
adding_columns['pump_days'] = adding_columns.apply(
    lambda row: relativedelta.relativedelta(row['end_pump'], row['start_pump']).days, axis=1)
adding_columns['pump_days'] = adding_columns['pump_days'] + 1
adding_columns['delta_month'] = adding_columns['end_pump'].dt.month - adding_columns['start_pump'].dt.month
# 3. Создаю 2 датафрейма:где перекачка велась в одном и том же месяце (df_month_true) и в разных

df_month_false = adding_columns[adding_columns['delta_month'] == 1]
df_month_true = adding_columns[adding_columns['delta_month'] == 0]
# 3.1 Создаю две копии, работаю с НЕСОВПАДАЮЩИМИ месяцами (delta_month = 1)

table_same = df_month_true.copy()
table_not_same = df_month_false.copy()
# 3.2 Добавляю 2 столбца: сколько дней качали в первом месяце (starting_day) и сколько во втором (ending_day)

table_not_same['ending_day'] = table_not_same['end_pump'].dt.day
table_not_same['starting_day'] = table_not_same['pump_days'] - table_not_same['ending_day']
# 3.3 Добавляю 2 столбца: сколько газа качали в первом месяце (starting_day) и сколько во втором (ending_day)
table_not_same['volume_end'] = table_not_same['volume'] * table_not_same['ending_day'] / table_not_same['pump_days']
table_not_same['volume_start'] = table_not_same['volume'] * table_not_same['starting_day'] / table_not_same['pump_days']
table_not_same = table_not_same.astype({'volume_end': 'int', 'volume_start': 'int'})
# 3.4 Создаю df, где провожу группировку по месяцам

df_not_same = table_not_same.copy()
df_not_same['start_pump'] = df_not_same['start_pump'].dt.month
df_not_same['end_pump'] = df_not_same['end_pump'].dt.month

df_not_same_start = df_not_same.groupby('start_pump', as_index=False) \
    .agg({'volume_start': 'sum'}) \
    .rename(columns={"start_pump": "month_number", "volume_start": "volume"})
df_not_same_finish = df_not_same.groupby('end_pump', as_index=False) \
    .agg({'volume_end': 'sum'}) \
    .rename(columns={"end_pump": "month_number", "volume_end": "volume"})
# 3.5 Создаю итоговый df для перекачек, идущих в нескольких месяцах

df_not_same_union = pd.merge(df_not_same_finish, df_not_same_start, how="outer") \
    .groupby("month_number", as_index=False) \
    .agg({"volume": "sum"})
# 4 Работаю с СОВПАДАЮЩИМИ месяцами

df_same_union = table_same.copy()
df_same_union['start_pump'] = df_same_union['start_pump'].dt.month
df_same_union = df_same_union.groupby("start_pump", as_index=False) \
    .agg({"volume": "sum"}) \
    .rename(columns={"start_pump": "month_number"})
# 5.1 Свожу всё в один df. На выходе объем перекачек по месяцам

df_total = pd.merge(df_not_same_union, df_same_union, how="outer") \
    .groupby("month_number", as_index=False) \
    .agg({"volume": "sum"}) \
    .sort_values(["month_number"]) \
    .astype({'month_number': 'str'})
# 5.2 Делаю свою сортировку, сортирую по месяцам

month_id = [str(i) for i in range(1, 13)]
sorter = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь',
          'Декабрь']
index_to_month = {index: month for index, month in zip(month_id, sorter)}
month_literals = [index_to_month[i] for i in index_to_month]
df_total['month_number'] = df_total['month_number'].replace(index_to_month)
# 6 Строю графики
fig = go.Figure(
    data=[go.Bar(x=df_total['month_number'], y=df_total['volume'])],
    layout_title_text="Распределение объёма по месяцам"
)
st.plotly_chart(fig)
