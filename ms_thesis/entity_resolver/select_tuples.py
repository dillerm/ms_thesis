"""
Randomly selects a specified number of tuples from a specified database.
"""

import sqlite3
import random
import pandas as pd
from datetime import datetime


tuple_number_input = input("Number of tuples to be randomly selected: ")
db_input = input("Database to select tuples from: ")
table_input = input("Table to select tuples from: ")

conn = sqlite3.connect(db_input)
c = conn.cursor()

query = c.execute("""select * from {}""".format(table_input))
column_names = [d[0] for d in query.description]
rows = query.fetchall()

selected_tuples = random.sample(rows, int(tuple_number_input))
selected_tuples_df = pd.DataFrame.from_records(selected_tuples, columns=column_names)

today = datetime.today().strftime("%Y-%m-%d")
filename = "../../data/entity_resolver_output/selected-unmatched-tuples-{}.csv".format(today)

selected_tuples_df.to_csv(filename, index=False)