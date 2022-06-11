#!/usr/bin/env python3
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
from pathlib import Path
import argparse
import re
import subprocess
import copy
import json

import frontend_server

ROOT = path.join(Path(path.abspath(__file__)).parent, "root")


def add_sym(target, sym):
    if sym and (sym['addr'] != 0 or sym['sym'] == 'vectors'):
        target.append(copy.deepcopy(sym))


def size_init():
    return {'t': 0, 'd': 0, 'b': 0, 'sum': 0}


def size_add(obj, sym):
    obj[sym['type']] += sym['size']
    obj['sum'] += sym['size']


def print_shead():
    print("%-60s %7s %7s %7s %7s %7s" % ("module", "text", "data", "bss", "dec", "hex"))
    print("------------------------------------------------------------------------------------------")


def print_mod(name, size):
    print("%-60s %7i %7i %7i %7i %7x" % (name, size['t'], size['d'], size['b'], size['sum'], size['sum']))


def print_sum(obj):
    print("------------------------------------------------------------------------------------------")
    print_mod("SUM", obj)
    print("------------------------------------------------------------------------------------------")
    print("")


def print_size(obj):
    print("   text    data     bss     dec     hex")
    print("%7i %7i %7i %7i %7x" % (obj['t'], obj['d'], obj['b'], obj['sum'], obj['sum']))


def print_tree(depth, tree):
    print_shead()
    print_subtree(depth, tree, 0)
    print_sum(tree['size'])


def print_subtree(depth, tree, cur):
    if depth:
        for t in tree:
            if t != 'size':
                ind = ""
                for i in range(0, cur):
                    ind += ".... "
                print_mod(ind + t, tree[t]['size'])
                print_subtree(depth - 1, tree[t], cur + 1)


def get_csvhead():
    return "%s,%s,%s,%s,%s\n" % ("module", "text", "data", "bss", "dec")


def get_csvmod(name, size):
    return "%s,%i,%i,%i,%i\n" % (name, size['t'], size['d'], size['b'],
                                 size['sum'])

def dump_modules(symtable):
    sa = dict()
    sm = size_init()
    for sym in symtable:
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


def dump_table(symtable):
    # print sizes on module (riot folder) base
    sa = {'size': size_init()}
    for sym in symtable:
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


def write_csv(symtable, csv):
    sa = dict()
    for sym in symtable:
        if sym['arcv']:
            k = sym['arcv']
        elif sym['obj']:
            k = sym['obj']
        else:
            k = sym['sym']
        if k not in sa:
            sa[k] = size_init()
        size_add(sa[k], sym)
    csv.write(get_csvhead())
    for a in sorted(sa):
        csv.write(get_csvmod(a, sa[a]))


def parse_elffile(elffile, prefix, appdir, riot_base=None):
    res = []
    dump = subprocess.check_output([prefix + 'nm', '--line-numbers', elffile])

    appdir = appdir.strip("/")
    rbase = ["riotbuild/riotproject"]
    if riot_base:
        rbase.append(riot_base.strip("/"))
    else:
        rbase.append("RIOT")
        rbase.append("riotbuild/riotbase")
    riot_base = "|".join([f'{p}/build|{p}' for p in rbase])

    c = re.compile(r"(?P<addr>[0-9a-f]+) "
                   r"(?P<type>[tbdTDB]) "
                   r"(?P<sym>[0-9a-zA-Z_$.]+)\s+"
                   r"(.+/)?"
                   r"("
                   r"{appdir}|"
                   r"{riot_base}|"
                   r".cargo/registry/src/[^/]+|"
                   r".cargo/git/checkouts|"
                   r"/rustc/[0-9a-f]+/?/library|"
                   r"ip-over-ble_experiments|"  # HACK...
                   r"{appdir}/.*bin/pkg"
                   r")/"
                   r"(?P<path>.+)/"
                   r"(?P<file>[0-9a-zA-Z_-]+\.(c|h|rs)):"
                   r"(?P<line>\d+)$".format(riot_base=riot_base,
                                            appdir=appdir))
    for line in dump.splitlines():
        m = c.match(line.decode("utf-8"))
        if m:
            d = {'arcv': '', 'obj': '', 'size': -1, 'alias': []}
            d.update(m.groupdict())
            d['path'] = d['path'].split(path.sep)
            d['line'] = int(d['line'])
            d['addr'] = int(d['addr'], 16)
            d['type'] = d['type'].lower()
            res.append(d)
    return res


def parse_mapfile(mapfile):
    res = []
    cur_type = ''
    cur_sym = {}
    with open(mapfile, 'r') as f:
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

            # if re.match("^\..+", line):
            if re.match("^OUTPUT.+", line):
                add_sym(res, cur_sym)
                cur_type = ''
                # continue
                break

            if cur_type:
                # fill bytes?
                m = re.match("^ *\*fill\* +0x([0-9a-f]+) +0x([0-9a-f])+", line)
                if m:
                    add_sym(res, cur_sym)
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
                    continue

                # start of a new symbol
                m = re.match(" \.([a-z]+\.)?([-_\.A-Za-z0-9$.]+)", line)
                if m:
                    # save last symbol
                    add_sym(res, cur_sym)
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
    return res


def symboljoin(symtable, nm_out):
    # get paths from nm-dump output
    for nm in nm_out:
        if nm["sym"] == "_gnrc_ipv6_nib.str1.1":
            print("NM", nm)
        for m in symtable:
            if (nm['addr'] & 0xfffffffe) == (m['addr'] & 0xfffffffe):
                m['path'] = nm['path']

    # fill in some known paths
    for sym in symtable:
        if sym['arcv'] == 'libc_s.a' or sym['arcv'] == 'libc_nano.a' or sym['arcv'] == 'libm.a':
            sym['path'] = ['newlib', 'libc']
        elif sym['arcv'] == 'libgcc.a':
            sym['path'] = ['newlib', 'libgcc']
        elif sym['obj'] == 'syscalls.o':
            sym['path'] = ['sys', 'syscalls']
        elif sym['sym'] == 'fill':
            sym['path'] = ['fill']

    # try to map .a and .o files to known paths
    otp = {}
    for sym in symtable:
        if sym['arcv'] and sym['path'] and sym['arcv'] not in otp:
            otp[sym['arcv']] = sym['path']
    for sym in symtable:
        if not sym['path'] and sym['arcv'] and sym['arcv'] in otp:
            sym['path'] = otp[sym['arcv']]

    # deduct paths for string objects by matching base names
    for m in symtable:
        if not m["path"] and ".str" in m["sym"]:
            basesym = m["sym"].split(".")[0]
            for nm in nm_out:
                if nm["sym"] == basesym and m["obj"].split(".")[0] == nm["file"].split(".")[0]:
                    m["path"] = nm["path"]


    # Hack?! for all symbols that we were not able to match so far, we match
    # the name of their object file against the known C files and use their
    # path
    for m in symtable:
        if not m["path"]:
            objbase = ".".join(m["obj"].split(".")[:-1])
            for nm in nm_out:
                if objbase == ".".join(nm["file"].split(".")[:-1]):
                    if not "include" in nm["path"]:
                        m["path"] = nm["path"]
                        break


def check_completeness(symbols):
    wp = []
    for sym in symbols:
        if not sym['path']:
            wp.append(sym)
            sym['path'] = ['unspecified']
            print(sym)
    if len(wp) > 0:
        print("Warning: %i symbols could not be matched to a path" % (len(wp)))
        print("Your output will be incomplete!")


if __name__ == "__main__":
    # Define some command line args
    p = argparse.ArgumentParser()
    p.add_argument("appdir", default="../RIOT/examples/hello-world", nargs="?", help="Full path to application dir")
    p.add_argument("board", default="iotlab-m3", nargs="?", help="BOARD to analyze")
    p.add_argument("elf_file", default="", nargs="?", help="ELF file")
    p.add_argument("map_file", default="", nargs="?", help="MAP file")
    p.add_argument("--riot-base", "-r", default=None, help="RIOT base")
    p.add_argument("-p", default="", help="Toolchain prefix, e.g. arm-none-eabi-")
    p.add_argument("-m", action="store_true", help="Dump module sizes to STDIO")
    p.add_argument("-v", action="store_true", help="Dump symbol sizes to STDIO")
    p.add_argument("-c", type=argparse.FileType('w'),
                   help="Write module sizes to cvs file")
    p.add_argument("-d", action="store_true", help="Don't run as web server")
    p.add_argument("--port", default="12345", help="Webserver port", type=int)
    args = p.parse_args()

    # extract path to elf and map file
    base = path.normpath(args.appdir)
    app = path.basename(base)
    if args.elf_file:
        elffile = args.elf_file
    else:
        elffile = base + "/bin/" + args.board + "/" + app + ".elf"
    if args.map_file:
        mapfile = args.map_file
    else:
        mapfile = base + "/bin/" + args.board + "/" + app + ".map"

    # Test if file exisists
    if not path.isfile(elffile):
        sys.exit("Error: ELF file '" + elffile + "' does not exist")
    if not path.isfile(mapfile):
        sys.exit("Error: MAP file '" + mapfile + "' does not exist")

    # get c-file names, addresses and paths from elf file
    nm_out = parse_elffile(elffile, args.p, path.abspath(base),
                           args.riot_base)
    # get symbol sizes and addresses archive and object files from map file
    symtable = parse_mapfile(mapfile)
    # join them into one symbol table
    symboljoin(symtable, nm_out)
    # check if the path for all symbols is set
    check_completeness(symtable)

    # dump symbols to STDIO if verbose option is set
    if args.v or args.m:
        dump_modules(symtable)
    if args.v:
        dump_table(symtable)
    if args.c:
        write_csv(symtable, args.c)

    # export results to json file
    data = {'app': app, 'board': args.board, 'symbols': symtable}
    with open(path.join(ROOT, "symbols.json"), 'w') as f:
        json.dump(data, f, indent=4)

    print("\nResult validation: both size outputs below should match")
    print("Computed sums of parsed symbols:")
    res = {'t': 0, 'd': 0, 'b': 0, 'sum': 0}
    for sym in symtable:
        res[sym['type']] += sym['size']
        res['sum'] += sym['size']
    print_size(res)
    # DEGBUG: output size results
    print("Output of the '" + args.p + "size' command:")
    print(subprocess.check_output((args.p + 'size', elffile)).decode("utf-8"))

    if not args.d:
        frontend_server.run(ROOT, args.port, 'index.html')
