import json
import os


dname = input('Directory name: ')

for fname in os.listdir(dname):
    if fname == '.DS_Store' : continue
    if not fname.endswith('.json') : continue
    fname_split_1 = fname.split('.json')[0]
    dt = fname_split_1.split('report_')[1] # Grab date from each file name
    fout = dname + '/report_data_' + dt

    fname = dname + '/' + fname

    with open(fname, 'r') as fhand:
        data = json.load(fhand)
        key_ct = int(len(data)/2)
        count = 1

        while True:
            header = data.get('header_' + str(count))
            content = data.get('content_' + str(count))

            if content.startswith('. '):
                content = content[2:]

            fname_out = fout + '_' + str(count) + '.txt'

            with open(fname_out, 'a') as f_output:
                f_output.write(header)
                f_output.write('\n')
                f_output.write(content)

            if count == key_ct : break
            count += 1
