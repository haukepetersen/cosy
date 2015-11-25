#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Copyright (C) 2015  Hauke Petersen <dev@haukepetersen.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
from os import path
import argparse
import re
import subprocess

if __name__ == "__main__":
    # Define some command line args
    p = argparse.ArgumentParser()
    p.add_argument("file", default="test.map", nargs="?", help="MAP file")
    p.add_argument("elf", default="test.elf", nargs="?", help="ELF file")
    p.add_argument("-p", default="", help="Toolchain prefix, e.g. arm-none-eabi-")
    args = p.parse_args()

    # Test if file exisists
    if not path.isfile(args.file):
        sys.exit("Error: ELF file '" + args.file + "' does not exist")


    symbols = {}

    dump = subprocess.check_output([
        'nm',
        '--line-numbers',
        args.elf])

    for line in dump.splitlines():
        m = re.match("([0-9a-f]+) ([tbdTDB]) ([_a-zA-Z0-9]+)[ \t]+.+/(RIOT/.+):(\d+)$", line)
        if m:
            symbols[m.group(3)] = {
                'type': m.group(2).lower(),
                'addr': m.group(1),
                'line': int(m.group(5)),
                'size': 0,
                'path': m.group(4),
            }






    targets = {'t': 0, 'd': 0, 'b': 0}

    cur_type = ''
    cur_sect = ''
    cur_addr = 0
    cur_size = 0
    cur_obj = ''
    cur_arc = ''
    cur_alias = []

    f = open(args.file, 'r')
    for line in f:

        m = re.match("^\.text +0x[0-9a-f]+ +0x([0-9a-f]+)", line)
        if m:
            targets['t'] += int(m.group(1), 16)
            cur_type = 't'
            continue

        m = re.match("^\.bss +0x[0-9a-f]+ +0x([0-9a-f]+)", line)
        if m:
            targets['b'] += int(m.group(1), 16)
            cur_type = 'b'
            continue

        m = re.match("^\.stack +0x[0-9a-f]+ +0x([0-9a-f]+)", line)
        if m:
            targets['b'] += int(m.group(1), 16)
            cur_type = 'b'
            continue

        m = re.match("^\.(relocate|data) +0x[0-9a-f]+ +0x([0-9a-f]+)", line)
        if m:
            targets['d'] += int(m.group(2), 16)
            cur_type = 'd'
            continue

        m = re.match("^\.[a-z0-9]+", line)
        if m:
            cur_type = ''
            continue


        if cur_type:
            # fill bytes?
            m = re.match("^ *\*fill\* +0x[0-9a-f]+ +0x([0-9a-f])+", line)
            if m:
                if "fill_" + cur_type in symbols:
                    symbols["fill_" + cur_type]['size'] += int(m.group(1), 16)
                else:
                    symbols["fill_" + cur_type] = {'size': int(m.group(1), 16), 'type': cur_type}
                continue

            # start of a new symbol
            m = re.match(" (\.[-_\.A-Za-z0-9]+)", line)
            if m:

                # process last symbol
                if cur_sect:
                    if len(cur_alias) == 1:
                        name = cur_alias[0]
                        print "NAME " + name
                    else:
                        print "there are " + str(len(cur_alias)) + " aliases for " + cur_sect

                    sym = re.match(".*\.([-_a-zA-Z0-9]+)", cur_sect)
                    if sym:
                        if sym.group(1) not in symbols:
                            print sym.group(1) + " is new!"
                        # else:
                            # print "--- found " + sym.group(1) + " size: " + str(cur_size)
                            # print "----      " + symbols[sym.group(1)]['path']
                    else:
                        print("ERROR ERROR")

                    # for sym in sym_names:
                    #     # print sym
                    #     if sym in symbols:
                    #         print "+++ found " + sym
                    cur_alias = []

                cur_sect = m.group(1)

            m = re.match(".+0x([0-9a-f]+) +0x([0-9a-f]+) (/.+)$", line)
            if m:
                cur_addr = int(m.group(1), 16)
                cur_size = int(m.group(2), 16)
                cur_arc = m.group(3)
                continue

            m = re.match(" +0x[0-9a-f]+ +([-_a-zA-Z0-9]+)$", line)
            if m:
                cur_alias.append(m.group(1))

    res = {'t': 0, 'd': 0, 'b': 0, 'sum': 0}

    for key in symbols:
        res[symbols[key]['type']] += symbols[key]['size']
        res['sum'] += symbols[key]['size']

    print("targets:")
    print("text: %i, data: %i, bss: %i" % (targets['t'], targets['d'], targets['b']))
    print("restuls:")
    print("text: %i, data: %i, bss: %i, sum: %i" % (res['t'], res['d'], res['b'], res['sum']))


    # DEGBUG: output size results
    print subprocess.check_output((args.p + 'size', args.elf)),
