import random

long_list= []
long_dict = {}

for i in range(100000):
    long_list.append(str(random.random()) + 'many str in list')
    long_dict[str(random.random())] = str(random.random()) + 'many str in dict'


