#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import sys
import os
from os import path
import argparse
import subprocess
import re
import time
import json

import frontend_server


if __name__ == "__main__":
    # Define some command line args
    p = argparse.ArgumentParser()
    p.add_argument("appdir", default="../RIOT/examples/hello-world", nargs="?", help="Full path to application dir")
    p.add_argument("-b", action="store_true", help="Rebuild all for boards")
    args = p.parse_args()

    base = path.normpath(args.appdir)
    app = path.basename(base);
    data = {'app': app, 'boards': []}

    if not path.isdir(base):
        sys.exit("Error: target application folder '" + app + "' not found")

    # collect information on available boards
    boards = subprocess.check_output(('make', 'info-boards-supported'), cwd=base).replace('\n', '').split(' ')

    for board in boards:
        elffile = base + "/bin/" + board + "/" + app + ".elf"

        if args.b:
            os.environ['BOARD'] = board
            start = time.time() * 1000
            subprocess.call(('make', '-B', 'clean', 'all'), cwd=base, )
            buildtime = (time.time() * 1000) - start
        else:
            buildtime = 0

        if path.isfile(elffile):
            size = subprocess.check_output(('size', elffile))

            m = re.search("^ *(\d+)[ \t]+(\d+)[ \t]+(\d+)", size, re.MULTILINE)
            if m:
                data['boards'].append({
                    'board': board,
                    'buildtime': buildtime,
                    't': m.group(1),
                    'd': m.group(2),
                    'b':m.group(3)
                    })

    # export results to json file
    with open("root/sizes.json", 'w') as f:
        json.dump(data, f, indent = 4)

    frontend_server.run('root', 12345, 'apphis.html')
