#!/usr/bin/python

from __builtin__ import list

__author__ = 'Saulo Aflitos'
import os
import sys
import gzip
import cPickle
from copy import copy, deepcopy
from itertools import izip

from pprint import pformat, pprint
from collections import namedtuple, defaultdict

WITH_INDEX     = True

TO_NAMED_TUPLE = True
TO_NAMED_TUPLE = False

INTERLINK      = True
# INTERLINK      = False

DUMP_DB_RAW      = True
DUMP_DB_RAW      = False

DUMP_DB_COMPILED = True
DUMP_DB_COMPILED = False

MAX_READ_LINES   = None
# MAX_READ_LINES   = 50



#
## DEBUG SECTION
#
RE_DO_RAW          = True
RE_DO_RAW          = False

RE_DO_COMPILE      = True
RE_DO_COMPILE      = False

DEBUG               = True
DEBUG               = False

DEBUG_LINES         = 2
DEBUG_BREAK         = 5
PRINT_HEADERS       = False

ITERATE             = True
# ITERATE        = False

ITERATE_MAX         = 2



DATASET = {
    "CCODE"             : { "filename": "Ccode_dump.txt"        },
    "COLL"              : { "filename": "coll_dump.txt"         },
    "COWNER"            : { "filename": "Cowner_dump.txt"       },

    "TAXID_NUC"         : { "filename": "gi_taxid_nucl.dmp.gz"  },
    "TAXID_PROT"        : { "filename": "gi_taxid_prot.dmp.gz"  },

    "ICODE"             : { "filename": "Icode_dump.txt"        },
    "CATEGORIES"        : { "filename": "taxcat/categories.dmp" },

    "TAXDUMP_CITATIONS" : { "filename": "taxdump/citations.dmp" },
    "TAXDUMP_DELNODES"  : { "filename": "taxdump/delnodes.dmp"  },
    "TAXDUMP_DIVISION"  : { "filename": "taxdump/division.dmp"  },
    "TAXDUMP_GC"        : { "filename": "taxdump/gc.prt"        },
    "TAXDUMP_GENCODE"   : { "filename": "taxdump/gencode.dmp"   },
    "TAXDUMP_MERGED"    : { "filename": "taxdump/merged.dmp"    },
    "TAXDUMP_NAMES"     : { "filename": "taxdump/names.dmp"     },
    "TAXDUMP_NODES"     : { "filename": "taxdump/nodes.dmp"     }
}

READ  = 'r'
WRITE = 'w'





def open_file(fn, mode, bin_mode=False, level=9):
    print "opening", fn, "for",
    print ( "reading" if mode == READ else "writing" ), "in",
    print ( "binary"  if bin_mode     else "text"    )

    end_mode = mode
    if bin_mode:
        end_mode += 'b'

    if fn.endswith('.gz'):
        if not bin_mode:
            end_mode += 'b'

        if mode == 'w':
            return gzip.open(fn, mode=end_mode, compresslevel=level)
        else:
            return gzip.open(fn, mode=end_mode)

    else:
        return open(fn, mode=end_mode)


def read_dump(fn, cfg):
    if "skip" in cfg and cfg["skip"]:
        return

    print "  parsing", fn
    ln  = 0
    sep = "\t|\t"

    if "sep" in cfg:
        sep = cfg["sep"]

    if "converters" not in cfg:
        cfg["converters" ] = {}
        cfg["convertersA"] = []

    cfg["data"] = []

    if "header_map" in cfg:
        if "header" in cfg:
            print "header_map and header defined at the same time"
            sys.exit(1)

        cfg["header"] = []

        for hm in cfg["header_map"]:
            hname = hm[0]
            cfg["header"].append( hname )

            if len(hm) == 2:
                cfg["converters" ][hname] = hm[1]
                cfg["convertersA"].append( hm[1] )

            elif len(hm) == 1:
                cfg["converters" ][hname] = str
                cfg["convertersA"].append( str )

            else:
                print "header map defined with wrong number of columns", hm
                sys.exit(1)

    read_header = True
    if "has_header" in cfg and not cfg["has_header"]:
        if "header" not in cfg:
            print "no header defined"
            sys.exit(1)
        read_header = False

    has_read_header = False

    for line in cfg["fh"]:
        line = line.strip()

        if len(line) == 0:
            continue

        if read_header and not has_read_header:
            has_read_header = True
            print "   header", line
            cols = line.split(sep)
            cols = [x.strip("\t").strip("\t|").replace(" ", "_") for x in cols]
            print "    header cols", cols
            cfg["header"     ] = cols
            cfg["convertersA"] = [None]*len(cols)
            for p in xrange(len(cols)):
                cname = cfg["header"][p]
                if cname not in cfg["converters"]:
                    cfg["converters"][cname] = str
                cfg["convertersA"][p] = cfg["converters"][cname]
            continue

        else:
            ln += 1

            # print line
            cols = line.split(sep)
            cols = [x.strip("\t").strip("\t|").strip() for x in cols]

            if DEBUG and ln <= DEBUG_LINES:
                print "    line o cols", ln, cols

            if len(cols) != len(cfg["header"]):
                print "len cols %d != len header %d" % (len(cols), len(cfg["header"]))
                print line
                print cols
                print cfg["header"]
                sys.exit(1)

            dcols = [None] * len(cols)

            for p in xrange(len(cols)):
                dcols[p] = cfg["convertersA"][p](cols[p])

            if DEBUG and ln <= DEBUG_LINES:
                print "    line d cols", ln, dcols

            cfg["data"].append( dcols )

            if DEBUG and ln == DEBUG_BREAK:
                break

            if MAX_READ_LINES is not None and ln ==MAX_READ_LINES:
                break

    print "  parsed", fn, ln, "lines"

    if TO_NAMED_TUPLE:
        header_data_to_named_tuple(cfg)


def read_ptr(fn, cfg):
    """
--**************************************************************************
--  This is the NCBI genetic code table
Genetic-code-table ::= {
name "Mold Mitochondrial; Protozoan Mitochondrial; Coelenterate
 Mitochondrial; Mycoplasma; Spiroplasma" ,
  name "SGC3" ,
  id 4 ,
  ncbieaa  "FFLLSSSSYY**CCWWLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG",
  sncbieaa "--MM---------------M------------MMMM---------------M------------"
  -- Base1  TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG
  -- Base2  TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG
  -- Base3  TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG
 {
  name "Standard" ,
  name "SGC0" ,
  id 1 ,
  ncbieaa  "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG",
  sncbieaa "---M---------------M---------------M----------------------------"
  -- Base1  TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG
  -- Base2  TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG
  -- Base3  TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG
 },
    """

    titles = { "name": str, "id": int, "ncbieaa": str, "sncbieaa": str, "Base1": str, "Base2": str, "Base3": str }

    cfg["data"       ] = []
    # sep = "\t"

    ln  = 0
    for line in cfg["fh"]:
        if len(line) >= 2 and line[:2] == '--':
            continue

        line = line.strip()

        if len(line) == 0:
            continue

        if "Genetic-code-table" in line:
            continue

        ln   += 1

        # print "line", line

        if line[0] == "{":
            if DEBUG and len(cfg["data"       ]) == DEBUG_BREAK:
                break

            cfg["data"       ].append({})
            # print " last", cfg["data"       ][-1]
            continue

        if line[0] == "}":
            continue

        line = line.strip().strip('--').strip()

        cols = [ x.strip().strip('"').strip('-').strip(',').strip().strip(',').strip() for x in line.split() ]
        k    = cols[0]
        v    = " ".join(cols[1:]).strip()

        if k not in titles: # HUGE hack
            v = cfg["data"       ][-1]["name"] + " " + k + " " + v
            k = "name"

        else:
            v = titles[k](v)
            if k in cfg["data"       ][-1]:
                kc = 2
                kn = k + str(kc)
                while kn in cfg["data"       ][-1]:
                    kc += 1
                    kn  = k + str(kc)
                k = kn


        if DEBUG and len(cfg["data"       ]) <= DEBUG_LINES:
            print " i %d k '%s' v '%s'" % (len(cfg["data"       ]), k, v)

        cfg["data"       ][-1][k] = v



    # print cfg["data"]

    if TO_NAMED_TUPLE:
        list_of_hashes_to_named_tuple(cfg)

    else:
        list_of_hashes_to_header_data(cfg)


def list_of_hashes_to_named_tuple(cfg):
    keys = []
    for v in cfg["data"]:
        for k in v.keys():
            if k not in keys:
                keys.append(k)

    keys.sort()
    cfg["header"] = keys
    # print keys

    placeholder = namedtuple(cfg["name"], keys)#, verbose=True)
    # setattr(__main__, placeholder.__name__, placeholder)
    # placeholder.__module__ = "__main__"
    globals()[placeholder.__name__] = placeholder
    for pval in xrange(len(cfg["data"])):
        val = cfg["data"][pval]
        lst = [val[x] if x in val else None for x in keys]
        v  = placeholder( *lst )
        cfg["data"][pval] = v


def header_data_to_named_tuple(cfg):
    keys = cfg["header"]
    keys = [ x.replace(" ", "_") for x in keys ]

    # keys.sort()
    # print keys

    placeholder = namedtuple(cfg["name"], keys)#, verbose=True)
    # setattr(__main__, placeholder.__name__, placeholder)
    # placeholder.__module__ = "__main__"
    globals()[placeholder.__name__] = placeholder

    for pval in xrange(len(cfg["data"])):
        lst = cfg["data"][pval]
        v   = placeholder( *lst )
        cfg["data"][pval] = v


def list_of_hashes_to_header_data(cfg):
    keys = []
    for v in cfg["data"]:
        for k in v.keys():
            if k not in keys:
                keys.append(k)

    keys.sort()
    cfg["header"] = keys
    # print keys

    #placeholder = namedtuple(cfg["name"], keys)#, verbose=True)
    # setattr(__main__, placeholder.__name__, placeholder)
    # placeholder.__module__ = "__main__"
    #globals()[placeholder.__name__] = placeholder
    for pval in xrange(len(cfg["data"])):
        val = cfg["data"][pval]
        lst = [val[x] if x in val else None for x in keys]
        # v  = placeholder( *lst )
        cfg["data"][pval] = lst


def parse_flag(v):
    return bool(int(v))


def parse_taxid_list(v):
    return [int(x) for x in v.split()]


def linearize(cfg):
    cfg["data"] = [x[0] for x in cfg["data"]]


def read_raw():
    for file_type in DATASET:
        filename = DATASET[file_type]["filename"]
        print "file type", file_type, "file name", filename, "...",

        if os.path.exists(filename):
            print "OK"

        else:
            print "MISSING"
            sys.exit(1)

    print "all files present"

    for file_type in DATASET:
        filename  = DATASET[file_type]["filename"]
        filebin   = config[ file_type]["bin"     ] if "bin" in config[ file_type] else False

        cfg       = config[ file_type]
        cfg["fh"] = open_file(filename, READ, bin_mode=filebin)
        print "opened", filename

        if "parser" in cfg:
            print " parsing"
            cfg["parser"]( filename, cfg )

            if "post" in cfg:
                cfg["post"](cfg)

        cfg["fh"].close()
        del cfg["fh"]
        if "converters"  in cfg: del cfg["converters"]
        if "convertersA" in cfg: del cfg["convertersA"]
        if "header_map"  in cfg: del cfg["header_map"]
        if "parser"      in cfg: del cfg["parser"]
        if "has_header"  in cfg: del cfg["has_header"]
        if "bin"         in cfg: del cfg["bin"]
        if "sep"         in cfg: del cfg["sep"]
        if "post"        in cfg: del cfg["post"]


def read_db(db_name):
    print "loading db"
    global config
    config = cPickle.load(open_file(db_name, READ, bin_mode=True))
    print "db loaded"


def process_config():
    for lnk in config["_linkers"]:
        for pair in lnk:
            pair[1] = pair[1].replace(" ", "_")

    for db_name in config.keys():
        if db_name[0] == "_":
            continue

        else:
            cfg         = config[db_name]
            cfg["name"] = db_name

            if "holders" in cfg:
                # "holders"   : [["collection_type", "collection_type"],["qualifier_type", "qualifier_type"]],
                for holder_num in xrange(len(cfg["holders"])):
                    holder_key, data_key = cfg["holders"][holder_num]
                    cfg["holders"][holder_num][0] = cfg["holders"][holder_num][0].replace(" ", "_")
                    cfg["holders"][holder_num][1] = cfg["holders"][holder_num][1].replace(" ", "_")
                    cfg["holders"][holder_num].append( config["_holders"][holder_key] )

            if "converters" in cfg:
                conv = cfg["converters"]
                for k in conv:
                    v = conv[k]
                    del conv[k]
                    conv[k.replace(" ", "_")] = v

            if "header_map" in cfg:
                hmap = cfg["header_map"]
                for h in xrange(len(hmap)):
                    hmap[h][0] = hmap[h][0].replace(" ", "_")

            if "desc" in cfg:
                desc = cfg["desc"]
                for k in desc:
                    v = desc[k]
                    del desc[k]
                    desc[k.replace(" ", "_")] = v


def compile_config():
    print "compiling config"

    for db_name in config.keys():
        if db_name[0] == "_":
            continue

        elif "skip" in config[db_name] and config[db_name]["skip"]:
            continue

        else:
            print "DB", db_name
            if DEBUG:
                print " DATA", config[db_name]

            config[db_name] = DumpHolder(config[db_name], create_index=False)


def link_config():
    for db_name in config.keys():
        if db_name[0] == "_":
            continue

        elif "skip" in config[db_name] and config[db_name]["skip"]:
            continue

        else:
            if INTERLINK:
                linkers = {}

                for link_set in config["_linkers"]:
                    for lnk_db_name, lnk_data_key in link_set:
                        if lnk_db_name == db_name:
                            linkers[ lnk_data_key ] = []

                            for lnk_lnk_db_name, lnk_lnk_data_key in link_set:
                                if lnk_lnk_db_name == db_name:
                                    continue

                                linkers[lnk_data_key].append( [lnk_lnk_db_name, lnk_lnk_data_key] )
                                # linkers[lnk_data_key].append( [config[lnk_lnk_db_name], lnk_lnk_data_key] )

                config[db_name].set_linkers(linkers)

                if WITH_INDEX:
                    config[db_name].set_create_index(WITH_INDEX)

    print "config compiled"


def save_raw_db(raw_db_file_name):
    print "saving raw"

    pcl = cPickle.Pickler(open_file(raw_db_file_name, WRITE, bin_mode=True), cPickle.HIGHEST_PROTOCOL)

    for db_name in sorted(config.keys()):
        if db_name[0] == "_":
            continue

        elif "skip" in config[db_name] and config[db_name]["skip"]:
            continue

        else:
            print "saving raw", db_name

            pcl.dump( [ db_name, config[ db_name ] ] )
            pcl.clear_memo()


def read_raw_db(raw_db_file_name):
    print "loading raw"

    pcl = cPickle.Unpickler(open_file(raw_db_file_name, READ, bin_mode=True))

    for db_name in sorted(config.keys()):
        if db_name[0] == "_":
            continue

        elif "skip" in config[db_name] and config[db_name]["skip"]:
            continue

        else:
            print "loading raw", db_name

            db_name2, data = pcl.load()

            if db_name != db_name2:
                print " db names differ", db_name, " != ", db_name2

            config[ db_name ] = data


def save_compiled_db(compiled_db_file_name):
    print "saving compiled"

    pcl = cPickle.Pickler(open_file(compiled_db_file_name, WRITE, bin_mode=True), cPickle.HIGHEST_PROTOCOL)

    for db_name in sorted(config.keys()):
        if db_name[0] == "_":
            continue

        elif "skip" in config[db_name] and config[db_name]["skip"]:
            continue

        else:
            print "saving compiled", db_name

            pcl.dump( [ db_name, config[ db_name ].get_compiled_data() ] )
            pcl.clear_memo()


def read_compiled_db(compiled_db_file_name):
    print "loading compiled"

    pcl = cPickle.Unpickler(open_file(compiled_db_file_name, READ, bin_mode=True))

    for db_name in sorted(config.keys()):
        if db_name[0] == "_":
            continue

        elif "skip" in config[db_name] and config[db_name]["skip"]:
            continue

        else:
            print "loading compiled", db_name

            db_name2, data = pcl.load()

            if db_name != db_name2:
                print " db names differ", db_name, " != ", db_name2

            config[ db_name ].set_compiled_data( data )





class ConstHolder(object):
    def __init__(self, name):
        self.name    = name
        self.vars    = []
        self.counter = []

    def get_pos(self, val):
        return self.vars.index( val )

    def get_value(self, pos):
        return self.vars[ pos ]

    def get_count(self, pos):
        return self.counter[ pos ]

    def get_data(self, pos):
        return ( self.get_value( pos ), self.get_count( pos ) )

    def __call__(self, v):
        if v in self.vars:
            ind = self.vars.index(v)
            self.counter[ind] += 1
            return ind

        else:
            self.vars.append(v)
            self.counter.append(0)
            return self(v)

    def __getitem__(self, pos):
        return self.vars[pos]

    def __repr__(self):
        return pformat( { "vars": [(x, y, self.counter[x]) for x, y in enumerate(self.vars)] } )


class LinksHolder(object):
    def __init__(self, value):
        self.links    = {}
        self.value    = value

    def add_link(self, dump_name_from, dump_name_to, col_from, col_to):
        self.links[dump_name_to] = {
            "dump_name_from": dump_name_from,
            "dump_name_to"  : dump_name_to,
            "col_from"      : col_from,
            "col_to"        : col_to
        }

    def get_table_names(self):
        return sorted(self.links.keys())

    def get_value(self):
        return self.value

    def get_link(self, db_name, limit=None, page=None):
        database      = self.links[ db_name        ]
        dump_name_to  = database[   "dump_name_to" ]
        col_to        = database[   "col_to"       ]
        data          = config[     dump_name_to   ].find( col_to, self.value, limit=limit, page=page )

        return data

    def get_links(self, limit=None, page=None):
        res = {}

        for db_name in self.links:
            res[db_name] = self.get_link( db_name, limit=limit, page=page )

        return res

    def __repr__(self):
        links = []

        for db_name in sorted(self.links.keys()):
            links.append( "%s$%s" % (db_name, self.links[db_name]["col_to"]) )

        links = " | ".join( links )
        return "<link : %s : %s>" % ( links, self.value )


class DumpHolder(object):
    def __init__(self, cfg, use_named_tuple=False, as_dict=False, as_list=False, create_index=False, create_all_indexes=False):
        # self.cfg                = cfg
        self.header             = cfg["header" ]
        self.data               = cfg["data"   ]
        self.desc               = cfg["desc"   ] if "desc"    in cfg else None
        self.name               = cfg["name"   ] if "name"    in cfg else None
        self.holders            = cfg["holders"] if "holders" in cfg else None
        self.linkers            = cfg["linkers"] if "linkers" in cfg else None
        self.named_tuple        = None
        self.index              = None
        self.create_index       = create_index
        self.create_all_indexes = create_all_indexes

        self.as_dict            = as_dict
        self.as_list            = as_list

        self.headerI            = {}
        for i in xrange(len(self.header)):
            self.headerI[ self.header[i] ] = i

        if use_named_tuple:
            self._gen_named_tuple()

        self._gen_index()

    def set_linkers(self, linkers):
        self.linkers = linkers
        self._gen_index( force=True )

    def get_linkers(self):
        return self.linkers

    def set_index(self, index):
        self.index = index

    def get_index(self):
        return self.index

    def get_compiled_data(self):
        return {
            "linkers"           : self.linkers,
            "index"             : self.index,
            "named_tuple"       : self.named_tuple is not None,
            "create_index"      : self.create_index,
            "create_all_indexes": self.create_all_indexes,
            "as_dict"           : self.as_dict,
            "as_list"           : self.as_list
        }

    def get_all_data(self):
        c = self.get_compiled_data()
        c["data"   ] = self.data
        c["header" ] = self.header
        c["headerI"] = self.headerI
        c["data"   ] = self.data
        c["desc"   ] = self.desc
        c["name"   ] = self.name
        c["holders"] = self.holders
        return c

    def set_compiled_data(self, c):
        self.linkers            = c["linkers"           ]
        self.index              = c["index"             ]

        if c["named_tuple"       ]:
             self._gen_named_tuple()

        self.create_index       = c["create_index"      ]
        self.create_all_indexes = c["create_all_indexes"]
        self.as_dict            = c["as_dict"           ]
        self.as_list            = c["as_list"           ]

    def set_all_data(self, c):
        self.set_compiled_data(c)
        self.data    = c["data"   ]
        self.header  = c["header" ]
        self.headerI = c["headerI"]
        self.data    = c["data"   ]
        self.desc    = c["desc"   ]
        self.name    = c["name"   ]
        self.holders = c["holders"]

    def _gen_index(self, force=False):
        fields = None

        def get_true_val(col_name, v):
            return self.holders[col_name].get_value(v)

        def get_orig_val(col_name, v):
            return v

        if self.linkers is not None:
            fields = self.linkers.keys()

        if ( self.index is None ) or force:
            if self.create_index:
                if fields is None or self.create_all_indexes:
                    fields = self.header

                self.index = {}
                for col_name in fields:
                    print "creating index for", self.name, "col", col_name
                    col_pos = self.headerI[col_name]

                    func = get_orig_val

                    if self.holders is not None and col_name in self.holders:
                        func = get_true_val


                    try:
                        index_dict = defaultdict(list)
                        [ index_dict[ func(col_name, line[col_pos]) ].append( idx ) for idx, line in enumerate(self.data) ]

                    except TypeError:
                        index_dict = defaultdict(list)
                        [ [index_dict[ func( col_name, line[col_pos][iidx] ) ].append( idx ) for iidx, iline in enumerate(line[col_pos])] for idx, line in enumerate(self.data) ]

                    # index_dict = dict(index_dict)
                    if DEBUG:
                        print "  index_dict", index_dict
                    print "  index length", len(index_dict)

                    self.index[ col_name ] = index_dict

    def set_create_index(self, v):
        self.create_index = v
        self._gen_index()

    def set_create_all_indexes(self, v):
        self.create_all_indexes = v
        self._gen_index()

    def set_as_dict(self, v):
        self.as_dict = v

    def set_as_list(self, v):
        self.as_list = v

    def set_use_named_tuple(self, v):
        if v:
            if self.named_tuple is not None: # already active
                pass
            else: # activate
                self._gen_named_tuple()
        else:
            self.named_tuple = None

    def _gen_named_tuple(self):
        self.named_tuple = namedtuple(self.name, self.header)

    def get_header(self):
        return self.header

    def _get_item_val(self, item):
        val = copy( self.data[item] )

        if self.holders is not None:
            for holder_num in xrange(len(self.holders)):
                holder_key, data_key, holder = self.holders[ holder_num ]
                data_pos        = self.headerI[ data_key ]
                data            = val[ data_pos ]
                val[ data_pos ] = holder.get_value( data )

        if self.desc is not None:
            # print "val", val
            for data_key in self.desc:
                # print " desc", data_key,
                data_pos        = self.headerI[data_key]
                # print "pos", data_pos,
                data            = val[ data_pos ]
                # print "data", data,
                ndata           = self.desc[ data_key ][ data ]
                # print "ndata", ndata
                val[ data_pos ] = ndata

        if self.linkers is not None:
            # LinkHolder
            # cfg["linkers"][lnk_data_key].append( [config[lnk_lnk_db_name], lnk_lnk_data_key] )

            for data_key in self.linkers:
                links           = self.linkers[ data_key ]
                data_pos        = self.headerI[ data_key ]
                data            = val[ data_pos ]
                links_holder    = LinksHolder( data )

                for lnk_db, lnk_data_key in links:
                    links_holder.add_link(self.name, lnk_db, data_key, lnk_data_key)

                val[ data_pos ] = links_holder

        return val

    def get_item(self, item, as_dict=False, as_list=False):
        vals = self._get_item_val(item)

        if as_dict or self.as_dict: # return as dict
            if TO_NAMED_TUPLE:
                return vals._asdict()

            else:
                if isinstance(vals, list):
                    return dict(izip(iter(self.header), iter(vals)))
                else:
                    return dict(izip(iter(self.header), iter([vals])))

        elif as_list or self.as_list: # return as list
            if TO_NAMED_TUPLE:
                return vals.__getnewargs__()

            else:
                return vals

        elif self.named_tuple is None: # return as is (default)
            return vals

        else: #convert to tuple if tuple was requested (default)
            if isinstance(vals, list):
                return self.named_tuple( *vals )
            else:
                return self.named_tuple( [vals] )

    def get_val(self, item, name):
        if TO_NAMED_TUPLE:
            return getattr(self.data[ item ], name)

        else:
            return self.data[ item ][ self.headerI[ name ] ]

    def get_name(self):
        return self.name

    def get_num_cols(self):
        return len(self.header)

    def get_size(self):
        return len(self.data)

    def find(self, col_name, value, limit=None, page=None ):
        if isinstance(value, list):
            res = {}
            for val in value:
                res[val] = self._find_value( col_name, val, limit=limit, page=page )
            return res
        else:
            return self._find_value( col_name, value, limit=limit, page=page )

    def _find_value(self, col_name, value, limit=None, page=None):
        if page is None:
            page = 0

        res    = None
        if ( self.index is not None ) and ( col_name in self.index ):
            index = self.index[ col_name ]
            if value in index:
                poses = index[ value ]

                if limit is None:
                    limit = len(poses)

                res   = [self.get_item( pos ) for pos in poses[page*limit:page*limit+limit]]

                if DEBUG:
                    print "QFIND: col_name", col_name, "value", value, "res", res

            else:
                if (not DEBUG) and (MAX_READ_LINES is None):
                    print "  col_name", col_name, "value", value, "NOT FOUND"
                    print "  ", index
                    sys.exit(1)

        else:
            col_pos = self.headerI[col_name]
            res     = [ self.get_item( idx ) for idx, line in enumerate( self.data ) if line[col_pos] == value ]

            if DEBUG:
                print "FIND: col_name", col_name, "col_pos", col_pos, "value", value, "res", res

            if limit is not None:
                if len(res) > limit:
                    res = res[page*limit:page*limit+limit]


        if res is None or len(res) == 0:
            return None

        return res

    def __len__(self):
        return self.get_size()

    def __getitem__(self, item):
        return self.get_item(item)

    # def __iter__(self):
    #     return iter(self)


class DbHolder(object):
    def __init__(self):
        self.dbs = {}

    def add(self, cfg):
        if isinstance(cfg, DumpHolder):
            self.add_dump_holder( DumpHolder(cfg) )
        else:
            self.add_dump_holder(cfg)

    def add_dump_holder(self, dmp):
        dmp_name = dmp.get_name()
        self.dbs[ dmp_name ] = dmp
        self.process_dump_holder(dmp_name)

    def get_dbs(self):
        return self.dbs.keys()

    def process_dump_holder(self):
        for db_name in self.dbs:
            for data_key in self.dbs[db_name].get_header():
                # if data_key in
                pass
        # linkers = {
        #     "inst_id"                      : [ "CCODE"           , "COWNER"          , "ICODE" ],

        #TODO
        pass

    def get_db(self, db_name):
        return self.dbs[db_name]

    def get_header(self, db_name):
        return self.get_db(db_name).get_header()

    def get_item(self, db_name, item, as_dict=False, as_list=False):
        val = self.get_db(db_name).get_item(item, as_dict=as_dict, as_list=as_list)
        return val

    def get_val(self, db_name, item, name):
        val = self.get_db(db_name).get_val(item, name)
        return val

    def get_num_cols(self, db_name):
        return self.get_db(db_name).get_num_cols()

    def get_size(self, db_name):
        return self.get_db(db_name).get_size()




def main():
    print "main"
    raw_db_file_name      = "db.raw.pickle.gz"
    compiled_db_file_name = "db.compiled.pickle.gz"


    if RE_DO_RAW:
        if os.path.exists(raw_db_file_name):
            os.remove(raw_db_file_name)

        if os.path.exists(compiled_db_file_name):
            os.remove(compiled_db_file_name)


    if RE_DO_COMPILE:
        if os.path.exists(compiled_db_file_name):
            os.remove(compiled_db_file_name)




    if not os.path.exists(raw_db_file_name):
        print "reading raw data"
        read_raw()
        print "raw data read"

        if DEBUG:
            pprint(config, depth=10)

        print "compiling raw data"
        compile_config()
        print "raw data compiled"

        if DUMP_DB_RAW:
            print "saving raw db"
            save_raw_db(raw_db_file_name)
            print "raw db saved"

            if DEBUG:
                print "loading raw db"
                read_raw_db(raw_db_file_name)
                print "raw db loaded"

    else:
        print "loading raw db"
        read_raw_db(raw_db_file_name)
        print "raw db loaded"



    if not os.path.exists(compiled_db_file_name):
        print "linking raw db"
        link_config()
        print "raw db linked"

        if DUMP_DB_COMPILED:
            print "saving compiled db"
            save_compiled_db(compiled_db_file_name)
            print "compiled db saved"

            if DEBUG:
                print "reading compiled db"
                read_compiled_db(compiled_db_file_name)
                print "compiled db read"

    else:
        print "reading compiled db"
        read_compiled_db(compiled_db_file_name)
        print "compiled db read"





    if PRINT_HEADERS:
        for db_name in config:
            if db_name[0] == "_":
                continue

            if "skip" in config[db_name] and config[db_name]["skip"]:
                continue

            print "db", db_name, config[db_name]["header"]

    if ITERATE:
        for db_name in config:
            if db_name[0] == "_":
                continue

            if "skip" in config[db_name] and config[db_name]["skip"]:
                continue

            print "db", db_name

            dmp = config[db_name]


            print  " printing el"
            elc = 0
            for el in dmp:
                print el
                elc += 1
                if ITERATE_MAX is not None and elc > ITERATE_MAX:
                    break


            print  " printing el as dict"
            dmp.set_as_dict(True)
            elc = 0
            for el in dmp:
                print el
                elc += 1
                if ITERATE_MAX is not None and elc > ITERATE_MAX:
                    break


            print  " printing el as list"
            dmp.set_as_dict(False)
            dmp.set_as_list(True)
            elc = 0
            for el in dmp:
                print el
                elc += 1
                if ITERATE_MAX is not None and elc > ITERATE_MAX:
                    break


            print  " printing el as tuple"
            dmp.set_use_named_tuple(True)
            dmp.set_as_dict(False)
            dmp.set_as_list(False)
            elc = 0
            for el in dmp:
                print el
                elc += 1
                if ITERATE_MAX is not None and elc > ITERATE_MAX:
                    break


            print  " printing el as tuple and dict"
            dmp.set_as_dict(True)
            elc = 0
            for el in dmp:
                print el
                elc += 1
                if ITERATE_MAX is not None and elc > ITERATE_MAX:
                    break


            print  " printing el as tuple and list"
            dmp.set_as_dict(False)
            dmp.set_as_list(True)
            elc = 0
            for el in dmp:
                print el
                elc += 1
                if ITERATE_MAX is not None and elc > ITERATE_MAX:
                    break


            print  " printing el links"
            dmp.set_use_named_tuple(False)
            dmp.set_as_dict(False)
            dmp.set_as_list(False)
            elc = 0
            for el in dmp:
                for v in el:
                    if isinstance(v, LinksHolder):
                        lnk = v.get_links(limit=2)
                        print "L", v.value, "lnk", v, "vals", lnk
                        # print "L", v.value, "lnk", v, "vals", len(lnk)

                    else:
                        print "v", v

                print
                elc += 1
                if ITERATE_MAX is not None and elc > ITERATE_MAX:
                    break

            print  " FINISHED"



holders = {
    "collection_type": ConstHolder("collection_type"),
    "qualifier_type" : ConstHolder("qualifier_type" ),
    "country"        : ConstHolder("country"        ),
    "name class"     : ConstHolder("name class"     ),#-- (synonym, common name, ...)
    "rank"           : ConstHolder("rank"           ),#-- rank of this node (superkingdom, kingdom, ...)
}



config = {
    "_holders": holders,
    "_linkers": [
        [
            [ "CCODE"            , "inst_id"                       ],
            [ "COWNER"           , "inst_id"                       ],
            [ "ICODE"            , "inst_id"                       ]
        ],
        [
            [ "TAXDUMP_NODES"    , "parent tax_id"                 ],
            [ "TAXDUMP_NAMES"    , "tax_id"                        ],
            [ "TAXDUMP_CITATIONS", "taxid_list"                    ],
        ],
        [
            [ "TAXDUMP_NODES"    , "tax_id"                        ],
            [ "TAXDUMP_NAMES"    , "tax_id"                        ],
            [ "TAXDUMP_CITATIONS", "taxid_list"                    ],
        ],
        [
            [ "TAXDUMP_NODES"    , "division id"                   ],
            [ "TAXDUMP_DIVISION" , "division id"                   ]
        ],
        [
            [ "TAXDUMP_NODES"    , "genetic code id"               ],
            [ "TAXDUMP_GENCODE"  , "genetic code id"               ]
        ],
        [
            [ "TAXDUMP_NODES"    , "mitochondrial genetic code id" ],
            [ "TAXDUMP_GENCODE"  , "genetic code id"               ]
        ],
        [
            [ "CATEGORIES"       , "taxid"                         ],
            [ "TAXDUMP_NAMES"    , "tax_id"                        ]
        ],
        [
            [ "CATEGORIES"       , "species_level_taxid"           ],
            [ "TAXDUMP_NAMES"    , "tax_id"                        ]
        ]
    ],
    "CCODE"             : {
                            "parser"    : read_dump,
                            "holders"   : [["collection_type", "collection_type"],["qualifier_type", "qualifier_type"]],
                            "converters": {
                                "coll_id"        : int,
                                "inst_id"        : int,
                                "coll_size"      : int,
                                "coll_status"    : parse_flag,
                                "collection_type": holders["collection_type"],
                                "qualifier_type" : holders["qualifier_type" ],
                            }
    },
    "COLL"              : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "sep"       : "\t",
                            "header_map": [
                                ["inst_code"],#The first column is the top-level category -
                                ["inst_type"],#and the second column is the corresponding species-level taxid.
                                ["inst_name"] #third column is the taxid itself,
                            ]
    },
    "COWNER"            : {
                            "parser"    : read_dump,
                            "holders"   : [["country", "country"],["collection_type", "collection_type"],["qualifier_type", "qualifier_type"]],
                            "converters": {
                                "inst_id"        : int,
                                "country"        : holders["country"],
                                "collection_type": holders["collection_type"],
                                "qualifier_type" : holders["qualifier_type"],
                            }
    },
    "TAXID_NUC"         : {
                            "skip"      : True,
                            "bin"       : True,
                            "parser"    : read_dump,
                            "has_header": False,
                            "sep"       : "\t",
                            "header_map": [
                                ["gi"   , int ],#nucleotide's gi
                                ["taxid", int ],#taxid
                            ]
    },
    "TAXID_PROT"        : {
                            "skip"      : True,
                            "bin"       : True,
                            "parser"    : read_dump,
                            "has_header": False,
                            "sep"       : "\t",
                            "header_map": [
                                ["gi"   , int ],#nucleotide's gi
                                ["taxid", int ],#taxid
                            ]
    },
    "ICODE"             : {
                            "parser": read_dump,
                            "converters": {
                                "inst_id": int
                            }
    },
    "CATEGORIES"        : {
                            "bin"       : False,
                            "parser"    : read_dump,
                            "has_header": False,
                            "sep"       : "\t",
                            "header_map": [
                                ["top_level_category"       ],#The first column is the top-level category -
                                ["species_level_taxid", int ],#and the second column is the corresponding species-level taxid.
                                ["taxid"              , int ],#third column is the taxid itself,
                            ],
                            "desc"      : {
                                "top_level_category": {
                                      "A": "Archaea",
                                      "B": "Bacteria",
                                      "E": "Eukaryota",
                                      "V": "Viruses and Viroids",
                                      "U": "Unclassified and Other",
                                }
                            }
    },
    "TAXDUMP_CITATIONS" : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "header_map": [
                                ["cit_id"    , int             ],#-- the unique id of citation
                                ["cit_key"                     ],#-- citation key
                                ["pubmed_id" , int             ],#-- unique id in PubMed database (0 if not in PubMed)
                                ["medline_id", int             ],#-- unique id in MedLine database (0 if not in MedLine)
                                ["url"                         ],#-- URL associated with citation
                                ["text"                        ],#-- any text (usually article name and authors)
                                                                 # -- The following characters are escaped in this text by a backslash:
                                                                 # -- newline (appear as "\n"),
                                                                 # -- tab character ("\t"),
                                                                 # -- double quotes ('\ "'),
                                                                 # -- backslash character (" \\ ").
                                ["taxid_list", parse_taxid_list],#-- list of node ids separated by a single space
                            ]
    },
    "TAXDUMP_DELNODES"  : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "header_map": [
                                ["tax_id", int],#-- deleted node id
                            ],
                            # "post": linearize
    },
    "TAXDUMP_DIVISION"  : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "header_map": [
                                ["division id"  , int],#-- taxonomy database division id
                                ["division cde"      ],#-- GenBank division code (three characters)
                                ["division name"     ],#-- e.g. BCT, PLN, VRT, MAM, PRI...
                                ["comments"          ] #comments
                            ]
    },
    "TAXDUMP_GC"        : {
                            "parser"    : read_ptr
    },
    "TAXDUMP_GENCODE"   : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "header_map": [
                                ["genetic code id",	int],#-- GenBank genetic code id
                                ["abbreviation"        ],#-- genetic code name abbreviation
                                ["name"                ],#-- genetic code name
                                ["cde"                 ],#-- translation table for this genetic code
                                ["starts"              ] #-- start codons for this genetic code
                            ]
    },
    "TAXDUMP_MERGED"    : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "header_map": [
                                ["old_tax_id"    , int        ],#-- id of nodes which has been merged
                                ["new_tax_id"    , int        ] #-- id of nodes which is result of merging
                            ]
    },
    "TAXDUMP_NAMES"     : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "holders"   : [["name class", "name class"]],
                            "header_map": [
                                ["tax_id"     , int                  ],#-- the id of node associated with this name
                                ["name_txt"                          ],#-- name itself
                                ["unique name"                       ],#-- the unique variant of this name if name not unique
                                ["name class" , holders["name class"]] #-- (synonym, common name, ...)
                            ]
    },
    "TAXDUMP_NODES"     : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "holders"   : [["rank", "rank"]],
                            "header_map": [
                                ["tax_id"                       , int            ],#-- node id in GenBank taxonomy database
                                ["parent tax_id"                , int            ],#-- parent node id in GenBank taxonomy database
                                ["rank"                         , holders["rank"]],#-- rank of this node (superkingdom, kingdom, ...)
                                ["embl code"                                     ],#-- locus-name prefix; not unique
                                ["division id"                  , int            ],#-- see division.dmp file
                                ["inherited div flag"           , parse_flag     ],#-- 1 if node inherits division from parent
                                ["genetic code id"              , int            ],#-- see gencode.dmp file
                                ["inherited GC flag"            , parse_flag     ],#-- 1 if node inherits genetic code from parent
                                ["mitochondrial genetic code id", int            ],#-- see gencode.dmp file
                                ["inherited MGC flag"           , parse_flag     ],#-- 1 if node inherits mitochondrial gencode from parent
                                ["GenBank hidden flag"          , parse_flag     ],#-- 1 if name is suppressed in GenBank entry lineage
                                ["hidden subtree root flag"     , parse_flag     ],#-- 1 if this subtree has no sequence data yet
                                ["comments"                                      ] #-- free-text comments and citations
                            ]
    }
}




if __name__ == "__main__":
    process_config()
    main()









"""
db TAXDUMP_GENCODE ['genetic code id', 'abbreviation', 'name', 'cde', 'starts']
db CCODE ['coll_id', 'inst_id', 'coll_name', 'coll_code', 'coll_size', 'collection_type', 'coll_status', 'coll_url', 'comments', 'qualifier_type']
db COWNER ['inst_id', 'inst_code', 'aka', 'inst_name', 'country', 'address', 'phone', 'fax', 'record_source', 'home_url', 'url_rule', 'comments', 'collection_type', 'qualifier_type', 'unique_name']
db TAXDUMP_DIVISION ['division id', 'division cde', 'division name', 'comments']
db TAXDUMP_GC ['Base1', 'Base2', 'Base3', 'id', 'name', 'name2', 'ncbieaa', 'sncbieaa']
db TAXDUMP_NAMES ['tax_id', 'name_txt', 'unique name', 'name class']
db COLL ['inst_code', 'inst_type', 'inst_name']
db ICODE ['inst_id', 'inst_code', 'unique_name']
db TAXDUMP_MERGED ['old_tax_id', 'new_tax_id']
db TAXDUMP_DELNODES ['tax_id']
db TAXDUMP_NODES ['tax_id', 'parent tax_id', 'rank', 'embl code', 'division id', 'inherited div flag', 'genetic code id', 'inherited GC flag', 'mitochondrial genetic code id', 'inherited MGC flag', 'GenBank hidden flag', 'hidden subtree root flag', 'comments']
db TAXDUMP_CITATIONS ['cit_id', 'cit_key', 'pubmed_id', 'medline_id', 'url', 'text', 'taxid_list']
db CATEGORIES ['top_level_category', 'species_level_taxid', 'taxid']




# db CCODE ['coll_id', 'inst_id', 'coll_name', 'coll_code', 'coll_size', 'collection_type', 'coll_status', 'coll_url', 'comments', 'qualifier_type']
# db COWNER ['inst_id', 'inst_code', 'aka', 'inst_name', 'country', 'address', 'phone', 'fax', 'record_source', 'home_url', 'url_rule', 'comments', 'collection_type', 'qualifier_type', 'unique_name']
# db ICODE ['inst_id', 'inst_code', 'unique_name']

# db TAXDUMP_NODES ['tax_id', 'parent tax_id', 'rank', 'embl code', 'division id', 'inherited div flag', 'genetic code id', 'inherited GC flag', 'mitochondrial genetic code id', 'inherited MGC flag', 'GenBank hidden flag', 'hidden subtree root flag', 'comments']
# db TAXDUMP_NAMES ['tax_id', 'name_txt', 'unique name', 'name class']
# db CATEGORIES ['top_level_category', 'species_level_taxid', 'taxid']

# db TAXDUMP_NODES ['tax_id', 'parent tax_id', 'rank', 'embl code', 'division id', 'inherited div flag', 'genetic code id', 'inherited GC flag', 'mitochondrial genetic code id', 'inherited MGC flag', 'GenBank hidden flag', 'hidden subtree root flag', 'comments']
# db TAXDUMP_DIVISION ['division id', 'division cde', 'division name', 'comments']

# db TAXDUMP_NODES ['tax_id', 'parent tax_id', 'rank', 'embl code', 'division id', 'inherited div flag', 'genetic code id', 'inherited GC flag', 'mitochondrial genetic code id', 'inherited MGC flag', 'GenBank hidden flag', 'hidden subtree root flag', 'comments']
# db TAXDUMP_GENCODE ['genetic code id', 'abbreviation', 'name', 'cde', 'starts']

# db COLL ['inst_code', 'inst_type', 'inst_name']
# db TAXDUMP_GC ['Base1', 'Base2', 'Base3', 'id', 'name', 'name2', 'ncbieaa', 'sncbieaa']
# db TAXDUMP_CITATIONS ['cit_id', 'cit_key', 'pubmed_id', 'medline_id', 'url', 'text', 'taxid_list']

# db TAXDUMP_MERGED ['old_tax_id', 'new_tax_id']
# db TAXDUMP_DELNODES ['tax_id']
"""





"""
{'CATEGORIES': {'data': [['A', 1462428, 1462428], ['A', 1462428, 743730]],
                'desc': {'top_level_category': {'A': 'Archaea',
                                                'B': 'Bacteria',
                                                'E': 'Eukaryota',
                                                'U': 'Unclassified and Other',
                                                'V': 'Viruses and Viroids'}},
                'header': ['top_level_category',
                           'species_level_taxid',
                           'taxid'],
                'name': 'CATEGORIES'},
 'CCODE': {'data': [[7166,
                     362,
                     'Herpetology Collection',
                     'Herp',
                     0,
                     0,
                     False,
                     '',
                     '',
                     0],
                    [7167,
                     362,
                     'Egg Collection',
                     'Egg',
                     0,
                     0,
                     False,
                     '',
                     '',
                     0]],
           'header': ['coll_id',
                      'inst_id',
                      'coll_name',
                      'coll_code',
                      'coll_size',
                      'collection_type',
                      'coll_status',
                      'coll_url',
                      'comments',
                      'qualifier_type'],
           'holders': [['collection_type',
                        'collection_type',
                        {'vars': [(0, 'museum', 4)]}],
                       ['qualifier_type',
                        'qualifier_type',
                        {'vars': [(0, 'specimen_voucher', 4)]}]],
           'name': 'CCODE'},
 'COLL': {'data': [['A', 's', 'Arnold Arboretum, Harvard University'],
                   ['AA', 's', 'Ministry of Science, Academy of Sciences']],
          'header': ['inst_code', 'inst_type', 'inst_name'],
          'name': 'COLL'},
 'COWNER': {'data': [[1,
                      'AEI',
                      '',
                      'American Entomological Institute',
                      0,
                      '3005 SW 56th Avenue, Gainesville, Florida 32608-5047',
                      '',
                      '',
                      '',
                      'http://aei.tamu.edu/projects/17/public/site/aei/home',
                      '',
                      '',
                      0,
                      0,
                      'AEI'],
                     [2,
                      'AMG',
                      '',
                      'Albany Museum',
                      1,
                      'Albany Museum, Somerset Street, Grahamstown 6139',
                      '+27 46 6222312',
                      '+27 46 622 2398',
                      '',
                      'http://www.ru.ac.za/static/affiliates/am/?request=affiliates/am/',
                      '',
                      '',
                      0,
                      0,
                      'AMG']],
            'header': ['inst_id',
                       'inst_code',
                       'aka',
                       'inst_name',
                       'country',
                       'address',
                       'phone',
                       'fax',
                       'record_source',
                       'home_url',
                       'url_rule',
                       'comments',
                       'collection_type',
                       'qualifier_type',
                       'unique_name'],
            'holders': [['country',
                         'country',
                         {'vars': [(0, 'USA', 1), (1, 'South Africa', 1)]}],
                        ['collection_type',
                         'collection_type',
                         {'vars': [(0, 'museum', 4)]}],
                        ['qualifier_type',
                         'qualifier_type',
                         {'vars': [(0, 'specimen_voucher', 4)]}]],
            'name': 'COWNER'},
 'ICODE': {'data': [[1, 'AEI', 'AEI'], [2, 'AMG', 'AMG']],
           'header': ['inst_id', 'inst_code', 'unique_name'],
           'name': 'ICODE'},
 'TAXDUMP_CITATIONS': {'data': [[5,
                                 'The domestic cat: perspective on the nature and diversity of cats.',
                                 0,
                                 8603894,
                                 '',
                                 '',
                                 [9685]],
                                [7,
                                 'Equine herpesvirus',
                                 0,
                                 819656,
                                 '',
                                 '',
                                 []]],
                       'header': ['cit_id',
                                  'cit_key',
                                  'pubmed_id',
                                  'medline_id',
                                  'url',
                                  'text',
                                  'taxid_list'],
                       'name': 'TAXDUMP_CITATIONS'},
 'TAXDUMP_DELNODES': {'data': [[1604857], [1604856]],
                      'header': ['tax_id'],
                      'name': 'TAXDUMP_DELNODES'},
 'TAXDUMP_DIVISION': {'data': [[0, 'BCT', 'Bacteria', ''],
                               [1, 'INV', 'Invertebrates', '']],
                      'header': ['division_id',
                                 'division_cde',
                                 'division_name',
                                 'comments'],
                      'name': 'TAXDUMP_DIVISION'},
 'TAXDUMP_GC': {'data': [['TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG',
                          'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG',
                          'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG',
                          1,
                          'Standard',
                          'SGC0',
                          'FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"',
                          'M---------------M---------------M'],
                         ['TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG',
                          'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG',
                          'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG',
                          2,
                          'Vertebrate Mitochondrial',
                          'SGC1',
                          'FFLLSSSSYY**CCWWLLLLPPPPHHQQRRRRIIMMTTTTNNKKSS**VVVVAAAADDEEGGGG"',
                          'MMMM---------------M']],
                'header': ['Base1',
                           'Base2',
                           'Base3',
                           'id',
                           'name',
                           'name2',
                           'ncbieaa',
                           'sncbieaa'],
                'name': 'TAXDUMP_GC'},
 'TAXDUMP_GENCODE': {'data': [[0, '', 'Unspecified', '', ''],
                              [1,
                               '',
                               'Standard',
                               'FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG',
                               '---M---------------M---------------M----------------------------']],
                     'header': ['genetic_code_id',
                                'abbreviation',
                                'name',
                                'cde',
                                'starts'],
                     'name': 'TAXDUMP_GENCODE'},
 'TAXDUMP_MERGED': {'data': [[12, 74109], [30, 29]],
                    'header': ['old_tax_id', 'new_tax_id'],
                    'name': 'TAXDUMP_MERGED'},
 'TAXDUMP_NAMES': {'data': [[1, 'all', '', 0], [1, 'root', '', 1]],
                   'header': ['tax_id',
                              'name_txt',
                              'unique_name',
                              'name_class'],
                   'holders': [['name_class',
                                'name_class',
                                {'vars': [(0, 'synonym', 1), (1, 'scientific name', 1)]}]],
                   'name': 'TAXDUMP_NAMES'},
 'TAXDUMP_NODES': {'data': [[1,
                             1,
                             0,
                             '',
                             8,
                             False,
                             1,
                             False,
                             0,
                             False,
                             False,
                             False,
                             ''],
                            [2,
                             131567,
                             1,
                             '',
                             0,
                             False,
                             11,
                             False,
                             0,
                             False,
                             False,
                             False,
                             '']],
                   'header': ['tax_id',
                              'parent_tax_id',
                              'rank',
                              'embl_code',
                              'division_id',
                              'inherited_div_flag',
                              'genetic_code_id',
                              'inherited_GC_flag',
                              'mitochondrial_genetic_code_id',
                              'inherited_MGC_flag',
                              'GenBank_hidden_flag',
                              'hidden_subtree_root_flag',
                              'comments'],
                   'holders': [['rank',
                                'rank',
                                {'vars': [(0, 'no rank', 1), (1, 'superkingdom', 1)]}]],
                   'name': 'TAXDUMP_NODES'},
 'TAXID_NUC': {'name': 'TAXID_NUC', 'skip': True},
 'TAXID_PROT': {'name': 'TAXID_PROT', 'skip': True},
 '_holders': {'collection_type': {'vars': [(0, 'museum', 4)]},
              'country': {'vars': [(0, 'USA', 1), (1, 'South Africa', 1)]},
              'name class': {'vars': [(0, 'synonym', 1), (1, 'scientific name', 1)]},
              'qualifier_type': {'vars': [(0, 'specimen_voucher', 4)]},
              'rank': {'vars': [(0, 'no rank', 1), (1, 'superkingdom', 1)]}},
 '_linkers': [[['CCODE', 'inst_id'],
               ['COWNER', 'inst_id'],
               ['ICODE', 'inst_id']],
              [['TAXDUMP_NODES', 'parent_tax_id'],
               ['TAXDUMP_NAMES', 'tax_id'],
               ['TAXDUMP_CITATIONS', 'taxid_list']],
              [['TAXDUMP_NODES', 'tax_id'],
               ['TAXDUMP_NAMES', 'tax_id'],
               ['TAXDUMP_CITATIONS', 'taxid_list']],
              [['TAXDUMP_NODES', 'division_id'],
               ['TAXDUMP_DIVISION', 'division_id']],
              [['TAXDUMP_NODES', 'genetic_code_id'],
               ['TAXDUMP_GENCODE', 'genetic_code_id']],
              [['TAXDUMP_NODES', 'mitochondrial_genetic_code_id'],
               ['TAXDUMP_GENCODE', 'genetic_code_id']],
              [['CATEGORIES', 'tax_id'], ['TAXDUMP_NAMES', 'tax_id']],
              [['CATEGORIES', 'species_level_taxid'],
               ['TAXDUMP_NAMES', 'tax_id']]]}
"""


"""
gi_taxid
The gi_taxid_nucl.dmp is about 160 MB and contains  two columns: the nucleotide's gi and taxid.
The gi_taxid_prot.dmp is about 17 MB and contains two columns:  the protein's gi  and taxid.

The file gi_taxid_nucl_diff.dmp contains differences between the latest and previous
dump files of the nucleotide's gi  and taxid;
The file gi_taxid_prot_diff.dmp contains differences between the latest and previous
dump files of the protein's gi  and taxid;

The first (left) column is the GenBank identifier (gi),
the second (right) column is taxonomy identifier (taxid).
The files are updated every Monday around 2am EST.

Please do not attempt to view the files with web browser (some of them could be huge).
You can download the file with netscape by right mouse click and
select 'Save link as...' or use ftp instead.

8       9913
10      9913
12      9913
14      9913
32      9913
35      9913
42      9913
44      9913






taxcat
categories.dmp contains a single line for each node
that is at or below the species level in the NCBI
taxonomy database.

The first column is the top-level category -

  A = Archaea
  B = Bacteria
  E = Eukaryota
  V = Viruses and Viroids
  U = Unclassified and Other

The third column is the taxid itself,
and the second column is the corresponding
species-level taxid.

These nodes in the taxonomy -

  242703 - Acidilobus saccharovorans
  666510 - Acidilobus saccharovorans 345-15

will appear in categories.dmp as -

A       242703  242703
A       242703  666510



coll
A	s	Arnold Arboretum, Harvard University



taxdump
*.dmp files are bcp-like dump from GenBank taxonomy database.
The readme.txt file gives a brief description of *.dmp files. These files
contain taxonomic information and are briefly described below. Each of the
files store one record in the single line that are delimited by "\t|\n"
(tab, vertical bar, and newline) characters. Each record consists of one
or more fields delimited by "\t|\t" (tab, vertical bar, and tab) characters.
The brief description of field position and meaning for each file follows.



nodes.dmp
---------

This file represents taxonomy nodes. The description for each node includes
the following fields:

	tax_id					-- node id in GenBank taxonomy database
 	parent tax_id				-- parent node id in GenBank taxonomy database
 	rank					-- rank of this node (superkingdom, kingdom, ...)
 	embl code				-- locus-name prefix; not unique
 	division id				-- see division.dmp file
 	inherited div flag  (1 or 0)		-- 1 if node inherits division from parent
 	genetic code id				-- see gencode.dmp file
 	inherited GC  flag  (1 or 0)		-- 1 if node inherits genetic code from parent
 	mitochondrial genetic code id		-- see gencode.dmp file
 	inherited MGC flag  (1 or 0)		-- 1 if node inherits mitochondrial gencode from parent
 	GenBank hidden flag (1 or 0)            -- 1 if name is suppressed in GenBank entry lineage
 	hidden subtree root flag (1 or 0)       -- 1 if this subtree has no sequence data yet
 	comments				-- free-text comments and citations

1	|	1	|	no rank	|		|	8	|	0	|	1	|	0	|	0	|	0	|	0	|	0	|		|
2	|	131567	|	superkingdom	|		|	0	|	0	|	11	|	0	|	0	|	0	|	0	|	0	|		|



names.dmp
---------
Taxonomy names file has these fields:

	tax_id					-- the id of node associated with this name
	name_txt				-- name itself
	unique name				-- the unique variant of this name if name not unique
	name class				-- (synonym, common name, ...)

division.dmp
------------
Divisions file has these fields:
	division id				-- taxonomy database division id
	division cde				-- GenBank division code (three characters)
	division name				-- e.g. BCT, PLN, VRT, MAM, PRI...
	comments

gencode.dmp
-----------
Genetic codes file:

	genetic code id				-- GenBank genetic code id
	abbreviation				-- genetic code name abbreviation
	name					-- genetic code name
	cde					-- translation table for this genetic code
	starts					-- start codons for this genetic code

delnodes.dmp
------------
Deleted nodes (nodes that existed but were deleted) file field:

	tax_id					-- deleted node id

merged.dmp
----------
Merged nodes file fields:

	old_tax_id                              -- id of nodes which has been merged
	new_tax_id                              -- id of nodes which is result of merging

citations.dmp
-------------
Citations file fields:

	cit_id					-- the unique id of citation
	cit_key					-- citation key
	pubmed_id				-- unique id in PubMed database (0 if not in PubMed)
	medline_id				-- unique id in MedLine database (0 if not in MedLine)
	url					-- URL associated with citation
	text					-- any text (usually article name and authors)
						-- The following characters are escaped in this text by a backslash:
						-- newline (appear as "\n"),
						-- tab character ("\t"),
						-- double quotes ('\ "'),
						-- backslash character (" \\ ").
	taxid_list				-- list of node ids separated by a single space



gc.tr
--**************************************************************************
--  This is the NCBI genetic code table
Genetic-code-table ::= {
 {
  name "Standard" ,
  name "SGC0" ,
  id 1 ,
  ncbieaa  "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG",
  sncbieaa "---M---------------M---------------M----------------------------"
  -- Base1  TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG
  -- Base2  TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG
  -- Base3  TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG
 },

"""
