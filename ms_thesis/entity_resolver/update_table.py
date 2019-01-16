import sqlite3


tuple_number_input = input("List of tuple numbers that need to be updated, separated by semicolons: ")
column_name_input = input("Column name that needs to be updated: ")
value_input = input("Value that is to be added to the tuple(s): ")

tuple_numbers = tuple_number_input.split(';')

conn = sqlite3.connect('../../flu-tuples.db')
c = conn.cursor()

for tuple_no in tuple_numbers:
    before_update = c.execute('''SELECT * FROM epidemics WHERE `index`=?''', (tuple_no,))
    print('Before update: ', c.fetchone())

    update = c.execute('''
    UPDATE epidemics
    SET {} = ?
    WHERE `index` = ?
    '''.format(column_name_input), (value_input, tuple_no,))

    after_update = c.execute('''SELECT * FROM epidemics WHERE `index`=?''', (tuple_no,))
    print('After update: ', c.fetchone(), '\n')

commit = input("Commit changes? [y/n] ")

if commit == 'y':
    conn.commit()
    conn.close()
elif commit == 'n':
    conn.close()