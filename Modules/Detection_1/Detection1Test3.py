import argparse

parse = argparse.ArgumentParser()
parse.add_argument('--a', type=int, default=10)
parse.add_argument('--b', type=int, default=11)
parse.add_argument('--c', type=int, default=12)

args = parse.parse_args()

print(args)
if __name__ == '__main__':
    print('sdfsdfsdfgdf')
