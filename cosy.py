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
import copy

def add_sym( target, sym ):
    if sym and (sym['addr'] != 0 or sym['sym'] == 'vectors'):
        target.append(copy.deepcopy(sym))

def size_init():
    return {'t': 0, 'd': 0, 'b': 0, 'sum': 0}

def size_add( obj, sym ):
    obj[sym['type']] += sym['size']
    obj['sum'] += sym['size']

def print_shead():
    print("%-60s %7s %7s %7s %7s %7s" % ("module", "text", "data", "bss", "dec", "hex"))
    print("------------------------------------------------------------------------------------------")

def print_mod( name, size ):
    print("%-60s %7i %7i %7i %7i %7x" % (name, size['t'], size['d'], size['b'], size['sum'], size['sum']))

def print_sum( obj ):
    print("------------------------------------------------------------------------------------------")
    print_mod("SUM", obj)
    print("------------------------------------------------------------------------------------------")
    print ""

def print_size( obj ):
    print("   text    data     bss     dec     hex")
    print("%7i %7i %7i %7i %7x" % (obj['t'], obj['d'], obj['b'], obj['sum'], obj['sum']))

def print_tree( depth, tree ):
    print_shead()
    print_subtree(depth, tree, 0)
    print_sum(tree['size'])


def print_subtree( depth, tree, cur ):
    if depth:
        for t in tree:
            if t != 'size':
                ind = ""
                for i in range(0, cur):
                    ind += ".... "
                print_mod( ind + t, tree[t]['size'])
                print_subtree( depth - 1, tree[t], cur + 1)


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


    nm_out = []
    dump = subprocess.check_output(['nm', '--line-numbers', args.elf])
    for line in dump.splitlines():
        m = re.match("([0-9a-f]+) ([tbdTDB]) ([_a-zA-Z0-9]+)[ \t]+.+/RIOT/(.+)/([-_a-zA-Z0-9]+\.[ch]):(\d+)$", line)
        if m:
            nm_out.append({
                'sym': m.group(3),
                'path': m.group(4).split('/'),
                'file': m.group(5),
                'line': int(m.group(6)),
                'addr': int(m.group(1), 16),
                'type': m.group(2).lower(),
                'arcv': '',
                'obj': '',
                'size': -1,
                'alias': []
                })


    map_out = []
    cur_type = ''
    cur_sym = {}
    f = open(args.file, 'r')
    for line in f:

        if re.match("^\.text", line):
            cur_type = 't'
            continue

        if re.match("^\.(bss|stack)", line):
            cur_type = 'b'
            continue

        if re.match("^\.(relocate|data)", line):
            cur_type = 'd'
            continue

        if re.match("^OUTPUT.+", line):
            add_sym(map_out, cur_sym)
            break;


        if cur_type:
            # fill bytes?
            m = re.match("^ *\*fill\* +0x([0-9a-f]+) +0x([0-9a-f])+", line)
            if m:
                add_sym(map_out, cur_sym)
                cur_sym = {
                    'sym': 'fill',
                    'path': '',
                    'file': '',
                    'line': -1,
                    'addr': int(m.group(1), 16),
                    'type': cur_type,
                    'size': int(m.group(2), 16),
                    'arcv': '',
                    'obj': '',
                    'alias': []
                    }
                # map_out.append(copy.deepcopy(cur_sym))
                continue;

            # start of a new symbol
            m = re.match(" \.([a-z]+\.)?([-_\.A-Za-z0-9]+)", line)
            if m:
                # save last symbol
                add_sym(map_out, cur_sym)
                # reset current symbol
                cur_sym = {
                    'sym': m.group(2),
                    'path': '',
                    'file': '',
                    'line': -1,
                    'addr': 0,
                    'type': cur_type,
                    'size': -1,
                    'arcv': '',
                    'obj': '',
                    'alias': []
                    }

            # get size, addr and path of current symbol
            m = re.match(".+0x([0-9a-f]+) +0x([0-9a-f]+) (/.+)$", line)
            if m:
                cur_sym['addr'] = int(m.group(1), 16)
                cur_sym['size'] = int(m.group(2), 16)
                # get object and archive files
                me = re.match(".+/([-_a-zA-Z0-9]+\.a)\(([-_a-zA-Z0-9]+\.o)\)$", m.group(3))
                if me:
                    cur_sym['arcv'] = me.group(1)
                    cur_sym['obj'] = me.group(2)
                me = re.match(".+/([-_a-zA-Z0-9]+\.o)$", m.group(3))
                if me:
                    cur_sym['arcv'] = ''
                    cur_sym['obj'] = me.group(1)
                continue

            m = re.match(" +0x[0-9a-f]+ +([-_a-zA-Z0-9]+)$", line)
            if m:
                cur_sym['alias'].append(m.group(1))






    wp = []
    for sym in map_out:
        if not sym['path']:
            wp.append(sym)
    print("Without path: %i" % len(wp))


    # get paths from nm-dump output
    for nm in nm_out:
        for m in map_out:
            if (nm['addr'] & 0xfffffffe) == m['addr']:
                m['path'] = nm['path']

    # fill in some known paths
    for sym in map_out:
        if sym['arcv'] == 'libc_s.a':
            sym['path'] = ['newlib', 'libc']
        elif sym['arcv'] == 'libgcc.a':
            sym['path'] = ['newlib', 'libgcc']
        elif sym['sym'] == 'fill':
            sym['path'] = ['fill']

    # try to map .a and .o files to known paths
    otp = {}
    for sym in map_out:
        if sym['arcv'] and sym['path'] and sym['arcv'] not in otp:
            otp[sym['arcv']] = sym['path']
    for sym in map_out:
        if not sym['path'] and sym['arcv'] and sym['arcv'] in otp:
            sym['path'] = otp[sym['arcv']]

    wp = []
    for sym in map_out:
        if not sym['path']:
                wp.append(sym)
                # print("%30s: a:%s, o:%s" % (sym['sym'], sym['arcv'], sym['obj']))
    print("Without path: %i" % len(wp))




    # print sizes on archive file base
    sa = dict()
    sm = size_init()
    for sym in map_out:
        if sym['arcv']:
            k = sym['arcv']
        elif sym['obj']:
            k = sym['obj']
        else:
            k = sym['sym']

        if k not in sa:
            sa[k] = size_init()
        size_add(sa[k], sym)
        size_add(sm, sym)

    print_shead()
    for a in sorted(sa):
        print_mod(a, sa[a])
    print_sum(sm)



    # print sizes on module (riot folder) base
    sa = {'size': size_init()}
    for sym in map_out:
        size_add(sa['size'], sym)
        tmp = sa
        for d in sym['path']:
            if d not in tmp:
                tmp[d] = {'size': size_init()}
            size_add(tmp[d]['size'], sym)
            tmp = tmp[d]
        # add symbol as leaf
        if sym['sym'] not in tmp:
            tmp[sym['sym']] = {'size': size_init()}
        size_add(tmp[sym['sym']]['size'], sym)

    print_tree(10, sa)


    # print_shead()
    # for a in sorted(sa):
    #     print_mod(a, sa[a]['size'])
    #     for b in sorted(sa[a]):
    #         if b != 'size':
    #             print_mod(a + '/' + b, sa[a][b]['size'])
    #     print ""

    # print_sum(sm)






    res = {'t': 0, 'd': 0, 'b': 0, 'sum': 0}
    for sym in map_out:
        res[sym['type']] += sym['size']
        res['sum'] += sym['size']
    print_size(res)

    # DEGBUG: output size results
    print subprocess.check_output((args.p + 'size', args.elf)),
