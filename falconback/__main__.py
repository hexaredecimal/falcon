"""
Main
----

Command line interface.
"""
import argparse
import subprocess
from falconback import __version__ as version, interpreter, copyright
from falconback.coder import falcon_system_code
import os

try:
    input = raw_input
except NameError:
    pass


def parse_args():
    argparser = argparse.ArgumentParser()

    argparser.add_argument('-c', '--compile', action='store_true')
    argparser.add_argument('-f', '--verbose', action='store_true')
    argparser.add_argument('-t', '--transpile', action='store_true')
    argparser.add_argument('-v', '--version', action='store_true')
    argparser.add_argument('file', nargs='?')
    return argparser.parse_args()


def interpret_file(path, verbose=False, transpile=False, link=False):
    with open(path) as f:
        print("\033[92mReading: \033[94m{}\033[0m".format(path))
        res = "{}\n//{}Program start{}\n{}".format(falcon_system_code, "-" * 30, "-" * 30, interpreter.evaluate(f, verbose=verbose))

        file = ""
        objectFile = ""
        execFile = ""

        path = path.split('.')[0]
        file = path + ".cpp"
        objectFile = path + ".o"
        execFile = path 

        if transpile or link:
            print("\033[92mWriting: \033[94m{}\033[0m".format(file))
            with open(file, "w+") as fw:
                if res != None:
                    fw.write(res)
                fw.close()

        if link:
            print("\033[92mCreating object: \033[94m{}\033[0m".format(objectFile))
            os.system('g++ --std=c++20 -g -c {} -o {}'.format(file, objectFile))

            print("\033[92mlinking executable: \033[94m{}\033[0m".format(execFile))
            os.system('g++ --std=c++20 {} -o {}'.format(objectFile, execFile))

            os.system('rm {} {}'.format(file, objectFile))



class FalconFile:
    def __init__(self, s):
        self.name = 'FALCON REPL'
        self.buffer = s

    def read(self):
        return self.buffer

def repl():
    print('{}\n\nPress Ctrl+C to exit.'.format(copyright))
    env = interpreter.create_global_env()
    buf = ''
    try:
        while True:
            inp = input('>>> ' if not buf else '')
            if inp == '':             
                print(interpreter.evaluate_env(FalconFile(buf), env))
                buf = ''
            else:
                buf += '\n' + inp
    except KeyboardInterrupt:
        pass


def main():
    args = parse_args()

    if args.version:
        print(copyright)
        return 

    if args.file:
        interpret_file(args.file, args.verbose, args.transpile, args.compile)
    else:
        repl()

if __name__ == '__main__':
    main()
