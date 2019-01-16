import os


dname = input('Directory name: ')

for fname in os.listdir(dname):
    if fname == '.DS_Store' : continue
    if not fname.endswith('.txt') : continue
    fname_split_1 = fname.split('.txt')[0]
    fout = dname + '/' + fname_split_1 + '.ann'

    open(fout, 'a').close()
