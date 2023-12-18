# import pandas as pd

# tickers = pd.read_csv("tickers_pairs.csv")['Ticker'].tolist()

# print(tickers)

import time

def isprime(x):
    if x > 1:
        for i in range(2, x):
            if (x % i) == 0:
                return 0
        else:
            return x
    return 0

def main():
    lower = 9000000
    upper = 9010000
    primes = []
    objects = []
    start_time = time.time()

    for num in range(lower, upper + 1):
        x = isprime(num)
        objects.append(x)
        [primes.append(x) for x in objects if x > 0]
    print(len(primes))
    print("Total Time: ", time.time() - start_time)
        

main()