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
# import subprocess


# class Anasize():

#     def __init__(self, elf_file, prefix):
#         self.elf = elf_file
#         self.prefix = prefix
#         self.obj = dict()

#     def parseFile(self):
#         dump = subprocess.check_output([
#             'nm',
#             '--radix=d',
#             '--print-size',
#             '--line-numbers',
#             # '--size-sort',
#             '-C',
#             self.elf])

#         text = 0
#         data = 0
#         bss = 0

#         for line in dump.splitlines():
#             # print 'line ' + str(i) + ': ' + line
#             # i += 1

#             if re.search(' [tT] ', line):
#                 # print 'hit ' + line

#                 res = re.match('\d+ (\d+)', line)
#                 if (res):
#                     print 'hit ' + line
#                     if re.search('interrupt', line):
#                         print "VECTOR " + line
#                     text += int(res.group(1))
#                 else:
#                     # print("PPP " + line)
#                     res = re.match('\d+$', line)
#                     if (res):
#                         print("empty line match")

#             if re.search(' [dD] ', line):
#                 # print 'hit ' + line
#                 res = re.match('\d+ (\d+)', line)
#                 if (res):
#                     data += int(res.group(1))

#             if re.search(' [bB] ', line):
#                 # print 'hit ' + line
#                 res = re.match('\d+ (\d+)', line)
#                 if (res):
#                     # if (int(res.group(1)) % 4):
#                         # bss += 2
#                         # print("BSS SYM < 4" + line)

#                     bss += int(res.group(1))


#         dec = text + data + bss
#         print("   text    data     bss     dec     hex filename")
#         print("%7i %7i %7i %7i %7x %s" % (text, data, bss, dec, dec, self.elf))

#         sizedump = subprocess.check_output((self.prefix + 'size', self.elf))
#         print '\n' + sizedump





if __name__ == "__main__":
    # Define some command line args
    p = argparse.ArgumentParser()
    p.add_argument("file", default="test.elf", nargs="?", help="ELF file to analyze")
    p.add_argument("-p", default="", help="Toolchain prefix, e.g. arm-none-eabi-")
    args = p.parse_args()

    # Test if file exisists
    if not path.isfile(args.file):
        sys.exit("Error: ELF file '" + args.file + "' does not exist")

    f = open(args.file, 'r')

    l = 0
    for line in f:

        if re.search("^ \.vectors", line):
            print line

        m = re.match(' *\.text\.([\._-a-zA-Z0-9]+)', line)
        if m:
            print("%s" % line)
            l += 1

    print(args.file + " contains %i lines" % l)

    # Analyze ELF file
    # ana = Anasize(args.file, args.p)
    # ana.parseFile()
