import sqlite3
import pandas as pd


data_input = input("Location of csv file: ")
column_labels_input = input("Labels for columns in csv file (separate by comma and a space): ")

labels = column_labels_input.split(", ")
df = pd.read_csv(data_input, names=labels)

db_name_input = input("Name for SQLite3 database: ")
conn = sqlite3.connect(db_name_input)
c = conn.cursor()

table_name_input = input("Name for table: ")
df.to_sql(table_name_input, conn)
