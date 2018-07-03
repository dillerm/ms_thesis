# Randomly selects x number of reports to be used for training datasets and y number of reports to be used for testing datasets

import os
import random


f_lst = list()

dname = input('Directory name: ')
x = input('Number of reports for training datasets: ')
y = input('Number of reports for testing datasets: ')

for fname in os.listdir(dname):
    f_lst.append(fname)

training_dsets = random.sample(f_lst, int(x))

for dset in training_dsets:
    f_lst.remove(dset)

test_dsets = random.sample(f_lst, int(y))

print(training_dsets)
print(test_dsets)