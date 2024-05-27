


from inspect import signature

def f(a:int,b:str):
    print(a,b)

sg  = signature(f)





print(sg.parameters)

fg()