import os
import random


f_lst = list()

dname = input('Directory name: ')

for fname in os.listdir(dname):
    f_lst.append(fname)

training_dsets = random.sample(f_lst, 20)

for dset in training_dsets:
    f_lst.remove(dset)

test_dsets = random.sample(f_lst, 5)

print(training_dsets)
print(test_dsets)