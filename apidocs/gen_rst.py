#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

## App Globals

HERE_PATH =  os.path.abspath(os.path.dirname(__file__))
ROOT_PATH = os.path.abspath(os.path.join(HERE_PATH, ".."))

API_DOCS_PATH = os.path.abspath(os.path.join(ROOT_PATH, "apidocs"))


def make_write_toc(root, head, lst):

    if head == "":
        head = "API"

    s = "%s/\n===================================\n\n" % head
    s += ".. toctree::\n"
    s += "    :maxdepth: 1\n"
    s += "\n"

    for i in lst:
        if i.endswith(".rst"):
            s += "    %s\n" % i
        else:
            s += "    %s.rst\n" % i

    s += "\n"

    f = open("%s/index.rst" % (root), "w")
    f.write(s)
    f.close()

def walk_dir(pth):
    ## Get a list of all the files in the mikidown/ dir
    ## Then generate and write the "automodule" .rst "index" stuff for sphinx
    fp = "%s/pyspread/" % ROOT_PATH
    fp += "/".join(pth)
    #rint("========SRC=", pth, fp)

    target_dir = "%s/api/" % (API_DOCS_PATH)
    target_dir += "/".join(pth)
    #print("target_dir=", target_dir)
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)

    ns = ""
    ns += ".".join(pth)
    print("ns=", ns, pth)

    index = []
    for file in sorted(os.listdir(fp)):


        extt = file.split(".")[-1]
        if extt in ("pyw", "pyc", "sql", "tgz", "html", "md", "ini", "png", "csv", "txt", "pysu", "svg"):
            continue
        if file in ["__pycache__", "Qt.py", "fabfile.py", "LICENSE", "share", "test"]:
            continue

        # if file in ["gpi", "rpi", "pitouch"]:
        #     #print ("no gpi=", fp)
        #     continue

        #print("file=", file)
        if file.endswith(".py"):

            if file == "__init__.py":
                con = ""
                with open(fp + "/" + file, "r") as F:
                    con = F.read().strip()
                    F.close
                #print("con=", con)
                if con == "":
                    #print("ignore init", fp)
                    continue

            fn = file[0:-3]

            if ns == "":
                s = "%s.*\n" % (fn)
                modi = "%s" % (fn)
            else:
                s = "%s.%s.*\n" % (ns, fn)
                modi = "%s.%s" % (ns, fn)
            print("  ", fn, s.strip())
            s += "==========================================================\n\n"
            #s += ".. autofunction:: %s.%s\n" % (ns, fn)
            #s += "\n"
            s += ".. automodule:: %s\n" % ( modi)
            s += "    :members:\n"
            s += "    :undoc-members:\n"
            s += "    :private-members:\n"
            #s += "    :special-members:\n"
            s += "    :show-inheritance:\n"
            s += "\n"

            target = "%s/%s.rst" % (target_dir, fn)
            #print(target)
            rstfile = open(target, "w")
            rstfile.write(s)
            rstfile.close()

            index.append(fn)
        else:
            npath = list(pth)
            npath.append(file)
            #print("parts=", npath)
            idx = walk_dir(npath)
            #print(idx)
            index.append("%s/index.rst" % file)

    make_write_toc(target_dir, ns, sorted(index, key=str.lower))

def docs_gen_rst_index():
    """Generetes an .rst files for each py file in source cos sphinx is stupid"""

    ## The "files" and "namespace" we do not want to document

    ## The "files" and "namespace" we do not want to document

    #api_dir = "%s/api/" % (API_DOCS_PATH)
    #local("rm -f -r %s" % api_dir)
    #local("mkdir %s" % api_dir)

    res = walk_dir([])

if __name__ == '__main__':
    src_dir = "%s/pyspread/" % (ROOT_PATH)
    docs_gen_rst_index()