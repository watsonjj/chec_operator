import argparse
from time import sleep
from os.path import splitext, join, exists
from os import remove


def main():
    description = 'Compare different pedestal techniques'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-f', '--file', dest='input_path', action='store',
                        required=True, help='path to the TIO run file')
    parser.add_argument('-T', '--time', dest='time', action='store',
                        type=float, default=0.1,
                        help='time to wait between line writes')

    args = parser.parse_args()

    ip = args.input_path
    op = splitext(ip)[0] + "_sim.txt"
    if exists(op):
        remove(op)

    with open(op, 'w+') as output:
        print("Writing to: {}".format(op))
        with open(ip, 'r') as file:
            while True:
                line = file.readline()
                output.write(line)
                print("Wrote line: {}".format(line))
                sleep(args.time)


if __name__ == '__main__':
    main()
