import time

def function1(x):
    return x*2

def function2(x):
    return x+2

def while_func(function):
    for i in range(5):
        s = function(i)
        print(s)
        time.sleep(1)

while_func(function1)
while_func(function2)
