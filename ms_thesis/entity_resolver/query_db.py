import sqlite3


#select_db_input = input("Select database to query: ")
column_names_input = input("Print column names? [y/n] ")

conn = sqlite3.connect("../../flu-tuples.db")
c = conn.cursor()

q = c.execute('''select * from epidemics''')
rows = q.fetchall()
print("Number of rows in table: ", len(rows))

if column_names_input == "y":
    column_names = [d[0] for d in q.description]
    print("Column names: ", ", ".join(column_names))

query_input = input("Input query: ")

query = c.execute("""{}""".format(query_input))
result = query.fetchall()

for row in result:
    print(row)