import argparse

parser = argparse.ArgumentParser(description='Example')
parser.add_argument('--filename', type=str, default="input.txt", metavar='N',
                   help='input filename (default: input.txt)')
parser.add_argument('--iterations', type=int, default=1000, metavar='N',
                   help='iterations (default: 1000)')

args = parser.parse_args()
filename = args.filename
iterations = args.iterations
