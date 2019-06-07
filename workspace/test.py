import pickle

def test1():
    numRouters = 0
    links = []
    with open('10-16-5.txt', 'r') as f:
        numRouters = int(f.readline())
        for l in f:
            r1, r2 = l.split()
            links.append((int(r1),int(r2)))

    print("num routers " + str(numRouters))
    print("############")
    print(links)
    print("############")
