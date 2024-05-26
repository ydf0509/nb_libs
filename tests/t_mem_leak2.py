import random

class A():
    def __init__(self):
        self.long_list= []
        self.long_dict = {}

a = A()

for i in range(100000):
    a.long_list.append(str(random.random()) + 'many str in list')
    a.long_dict[str(random.random())] = str(random.random()) + 'many str in dict'


