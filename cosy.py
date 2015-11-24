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


    f = open(args.file, 'r')

    l = 0

    root = {'name': 'RIOT', 't': 0, 'd': 0, 'b': 0, 'children': []}

    mem_t = dict()
    mem_t['target'] = 0
    mem_t['sum'] = 0
    mem_t['fill'] = 0

    mem_b = dict()
    mem_b['target'] = 0
    mem_b['sum'] = 0
    mem_b['fill'] = 0

    mem_d = dict()
    mem_d['target'] = 0
    mem_d['sum'] = 0
    mem_d['fill'] = 0

    state = ''

    cur_symbol = ''
    cur_size = 0
    cur_path = ''
    sym_names = []

    mem = {}

    for line in f:

        m = re.match("^\.text +0x[0-9a-f]+ +0x([0-9a-f]+)", line)
        if m:
            mem = root['t']
            continue

        m = re.match("^\.bss +0x[0-9a-f]+ +0x([0-9a-f]+)", line)
        if m:
            mem = root['b']
            continue

        m = re.match("^\.stack +0x[0-9a-f]+ +0x([0-9a-f]+)", line)
        if m:
            mem = root['b']
            continue

        m = re.match("^\.(relocate|data) +0x[0-9a-f]+ +0x([0-9a-f]+)", line)
        if m:
            mem = root['d']
            continue


        m = re.match("^\.[a-z0-9]+", line)
        if m:
            mem = {}
            continue


        if mem:
            m = re.match("^ *\*fill\* +0x[0-9a-z]+ +0x([0-9a-z])+", line)
            if m:
                mem += int(m.group(1), 16)

            m = re.match(" (\.[-_\.A-Za-z0-9]+)", line)
            if m:
                if sym_names:
                    print "FOUND:" + cur_symbol + " (" + str(cur_size) + ") " + cur_path
                    print sym_names
                    sym_names = []

                cur_symbol = m.group(1)



            m = re.match(".+0x[0-9a-f]+ +0x([0-9a-f]+) (/.+)$", line)
            if m:
                cur_size = int(m.group(1), 16)
                mem += int(m.group(1), 16)
                cur_path = m.group(2)
                continue

            m = re.match(" +0x[0-9a-f]+ +([-_a-zA-Z0-9]+)$", line)
            if m:
                sym_names.append(m.group(1))



    print("text - text: %i, data: %i, bss: %i" % (root['t'], root['d'], root['b']))
    print ""

    # DEGBUG: output size results
    print subprocess.check_output((args.p + 'size', args.elf)),
