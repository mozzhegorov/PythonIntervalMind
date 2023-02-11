def decarator(func):
    print('in')
    def wrapper(a, b):
        return func(a, b)
    print('out')
    return wrapper


@decarator
def printing(a, b):
    print(a, b)
    
if __name__ == '__main__':
    printing(2, 5)