import os
import sys
import argparse
import cppimport

def cpp_run():
    parser = argparse.ArgumentParser(description='Run a C++ file with cppimport')
    parser.add_argument('filename', help = 'The file to run.')
    parser.add_argument('--verbose', '-v', action = 'store_true', help = 'Tell me everything!')
    args = parser.parse_args()

    if args.verbose:
        cppimport.set_quiet(False)

    filename = args.filename

    filedir = os.path.dirname(filename)
    sys.path.append(filedir)

    filebasename = os.path.basename(filename)
    module_name, file_extension = os.path.splitext(filebasename)

    module = cppimport.imp(module_name)

    if args.verbose:
        print("Launching!")
    module.main()

if __name__ == '__main__':
    cpp_run()
