
open('output', 'w').close()
def log(*args, **kwargs):
    print(*args, **kwargs)
    with open('output', 'a+') as f:
        try:
            s = ' '.join(args) + '\n'
        except:
            s = ' '.join(str(args[0])) + '\n'
        f.write(s)
