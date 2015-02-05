#!/usr/bin/python

from __builtin__ import list

__author__ = 'Saulo Aflitos'

import os
import sys

import gzip

#from copy import copy, deepcopy
from itertools import izip

from pprint import pformat, pprint
from collections import namedtuple, defaultdict

from parser_sql_struct import *

#      save 2 1    load 2 1    save latest 1   load latest 1   load no pickle   save json 1   read json
#real  4m30.067s   5m27.524s   4m42.931s       5m29.587s       2m54.808s        7m47.482s     7m09.099s
#user  3m56.183s   4m47.196s   4m00.956s       4m45.990s       2m35.346s        6m21.610s     6m09.984s
#sys   0m33.618s   0m39.956s   0m41.678s       0m43.237s       0m19.175s        1m25.403s     0m58.721s



MAX_READ_LINES   = None   # max number of lines to read
MAX_READ_LINES   = 500

DUMP_EVERY       = 25000


#
## DEBUG SECTION
#
RE_DO_RAW        = True   # force redo raw data
RE_DO_RAW        = False

DEBUG            = True   # debug
DEBUG            = False

DEBUG_LINES      = 2      # number of lines to print
DEBUG_BREAK      = 5      # number of line sto read
PRINT_HEADERS    = False  # print header information

ITERATE          = True   # iterate over data
ITERATE          = False

ITERATE_MAX      = 2      # number of register to iterate over

TO_NAMED_TUPLE   = False

if DEBUG:
    TO_NAMED_TUPLE   = True

#http://darwin.zoology.gla.ac.uk/~rpage/tbmap/downloads/ncbi/


READ    = 'r'
WRITE   = 'w'
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
        if DEBUG:
            print v


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
        if DEBUG:
            print v


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
        cfg["data"][pval] = tuple(lst)
        if DEBUG:
            print cfg["data"][pval]


def parse_flag(v):
    return bool(int(v))


def parse_taxid_list(v):
    return [int(x) for x in v.split()] if v is not None else None


def linearize(cfg):
    cfg["data"] = [x[0] for x in cfg["data"]]





def read_dump(fn, cfg):
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

            v = None

            if len(hm) == 2:
                v = hm[1]

            elif len(hm) == 1:
                v = str

            else:
                print "header map defined with wrong number of columns", hm
                sys.exit(1)

            cfg["converters" ][hname] = v
            cfg["convertersA"].append(  v )


    read_header = True
    if "has_header" in cfg and not cfg["has_header"]:
        if "header" not in cfg:
            print "no header defined"
            sys.exit(1)
        read_header = False

    has_read_header = False



    for line in cfg["fh"]:
        line = line.strip().decode('ascii', 'ignore')

        if len(line) == 0:
            continue

        if read_header and not has_read_header:
            has_read_header = True
            print "   header", line
            cols = line.split(sep)
            print "    header cols B", cols
            cols = [x.strip("\t").strip("\t|").replace(" ", "_") for x in cols]
            print "    header cols A", cols
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
            cols = [x if x != '' else None for x in cols]

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

            cfg["data"].append( tuple(dcols) )

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


def add_to_db(cfg):
    print "saving to sql db", cfg["name"]
    db_table = cfg["db"      ]
    header   = cfg["header"  ]
    uniques  = None
    if "_uniques" in cfg:
        uniques  = {}
        for x in cfg["_uniques"]:
            uniques[x] = {}

    for pval in xrange(len(cfg["data"])):
        vals = cfg["data"][pval]
        #print vals
        v    = dict(izip(iter(header), iter(vals)))
        if uniques is not None and len(uniques) > 0:
            found = False
            for u in uniques:
                if v[u] in uniques[u]:
                    uniques[u][v[u]] += 1
                    print "duplicated register", v
                    found = True
                    
                else:
                    uniques[u][v[u]] = 1
            if found:
                continue
            
        register = db_table( **v )
        #print register
        #session.merge( register )
        session.add( register )
        
        if ( DUMP_EVERY is not None ) and ( pval != 0 ) and ( pval % DUMP_EVERY == 0 ):
            print "saving to sql db", cfg["name"], "commiting", "%8d"%pval,'...',
            session.commit()
            print "DONE"
            
    print "saving to sql db", cfg["name"], "final commit"
    session.commit()
    print "saving to sql db", cfg["name"], "finished"

    if uniques is not None:
        print "duplicated registers"
        for k in uniques:
            print " offending key:", k
            vals = uniques[k]
            for v in [x for x in vals if vals[x] > 1]:
                print "  val:", v, vals[x]

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


def read_raw_files():
    max_filetype = max([len(        file_type             ) for file_type in DATASET])
    max_filename = max([len(DATASET[file_type]["filename"]) for file_type in DATASET])
    
    for file_type in DATASET:
        filename = DATASET[file_type]["filename"]
        print ("file type %-"+str(max_filetype)+"s file name %-"+str(max_filename)+"s") % ( file_type, filename ), '...',

        if os.path.exists(filename):
            print "OK"

        else:
            print "MISSING"
            sys.exit(1)

    print "all files present"

    for file_type in DATASET:
        cfg       = config[ file_type]

        if "skip" in cfg and cfg["skip"]:
            continue
    
        if "db" not in cfg and not DEBUG:
            continue
        
        if "parser" not in cfg:
            continue
        
        filename  = DATASET[file_type]["filename"]
        filebin   = cfg["bin"     ] if "bin" in cfg else False
            
        cfg["fh"] = open_file(filename, READ, bin_mode=filebin)
        print "opened", filename
    

        print " parsing"
        cfg["parser"]( filename, cfg )

        if "post" in cfg:
            cfg["post"](cfg)

        cfg["fh"].close()
        del cfg["fh"]
        
        if not DEBUG:
            add_to_db(cfg)

        if "converters"  in cfg: del cfg["converters" ]
        if "convertersA" in cfg: del cfg["convertersA"]
        if "header_map"  in cfg: del cfg["header_map" ]
        if "parser"      in cfg: del cfg["parser"     ]
        if "has_header"  in cfg: del cfg["has_header" ]
        if "bin"         in cfg: del cfg["bin"        ]
        if "sep"         in cfg: del cfg["sep"        ]
        if "post"        in cfg: del cfg["post"       ]
        if "db"          in cfg: del cfg["db"         ]
        if "data"        in cfg: del cfg["data"       ]


def main():
    print "main"

    process_config()
    read_raw_files()



   


config = {
    "_linkers": [
        [
            [ "CCODE"            , "inst_id"                       ],
            [ "COWNER"           , "inst_id"                       ],
            [ "ICODE"            , "inst_id"                       ]
        ],
        [
            [ "TAXDUMP_NODES"    , "parent tax_id"                 ],
            [ "TAXDUMP_NODES"    , "tax_id"                        ],
            [ "TAXDUMP_NAMES"    , "tax_id"                        ],
            [ "TAXDUMP_CITATIONS", "taxid_list"                    ],
            [ "CATEGORIES"       , "taxid"                         ],
            [ "CATEGORIES"       , "species_level_taxid"           ],
            [ "TAXID_NUC"        , "taxid"                         ],
            [ "TAXID_PROT"       , "taxid"                         ],
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
        ]
    ],
    "CCODE"             : {
                            "parser"    : read_dump,
                            "converters": {
                                "coll_id"        : int,
                                "inst_id"        : int,
                                "coll_size"      : int,
                                "coll_status"    : parse_flag,
                                #"collection_type": holders["collection_type"],
                                #"qualifier_type" : holders["qualifier_type" ],
                            },
                            "db"        : db_ccode
    },
    "COLL"              : {
                            "_uniques"  : ["inst_code"],
                            "parser"    : read_dump,
                            "has_header": False,
                            "sep"       : "\t",
                            "header_map": [
                                [ "inst_code" ],#The first column is the top-level category -
                                [ "inst_type" ],#and the second column is the corresponding species-level taxid.
                                [ "inst_name" ] #third column is the taxid itself,
                            ],
                            "db"        : db_coll
    },
    "COWNER"            : {
                            "parser"    : read_dump,
                            "converters": {
                                "inst_id"        : int,
                                #"country"        : holders["country"        ],
                                #"collection_type": holders["collection_type"],
                                #"qualifier_type" : holders["qualifier_type" ],
                            },
                            "db"        : db_cowner
    },
    "TAXID_NUC"         : {
                            #"skip"      : True,
                            "bin"       : True,
                            "parser"    : read_dump,
                            "has_header": False,
                            "sep"       : "\t",
                            "header_map": [
                                [ "gi"   , int ],#nucleotide's gi
                                [ "taxid", int ],#taxid
                            ],
                            "db"        : db_taxid_nuc
    },
    "TAXID_PROT"        : {
                            #"skip"      : True,
                            "bin"       : True,
                            "parser"    : read_dump,
                            "has_header": False,
                            "sep"       : "\t",
                            "header_map": [
                                [ "gi"   , int ],#nucleotide's gi
                                [ "taxid", int ],#taxid
                            ],
                            "db"        : db_taxid_prot
    },
    "ICODE"             : {
                            "parser": read_dump,
                            "converters": {
                                "inst_id": int
                            },
                            "db"        : db_icode
    },
    "CATEGORIES"        : {
                            "bin"       : False,
                            "parser"    : read_dump,
                            "has_header": False,
                            "sep"       : "\t",
                            "header_map": [
                                [ "top_level_category"       ],#The first column is the top-level category -
                                [ "species_level_taxid", int ],#and the second column is the corresponding species-level taxid.
                                [ "taxid"              , int ],#third column is the taxid itself,
                            ],
                            "desc"      : {
                                "top_level_category": {
                                      "A": "Archaea",
                                      "B": "Bacteria",
                                      "E": "Eukaryota",
                                      "V": "Viruses and Viroids",
                                      "U": "Unclassified and Other",
                                }
                            },
                            "db"        : db_categories
    },
    "TAXDUMP_CITATIONS" : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "header_map": [
                                [ "cit_id"    , int              ],#-- the unique id of citation
                                [ "cit_key"                      ],#-- citation key
                                [ "pubmed_id" , int              ],#-- unique id in PubMed database (0 if not in PubMed)
                                [ "medline_id", int              ],#-- unique id in MedLine database (0 if not in MedLine)
                                [ "url"                          ],#-- URL associated with citation
                                [ "text"                         ],#-- any text (usually article name and authors)
                                                                   # -- The following characters are escaped in this text by a backslash:
                                                                   # -- newline (appear as "\n"),
                                                                   # -- tab character ("\t"),
                                                                   # -- double quotes ('\ "'),
                                                                   # -- backslash character (" \\ ").
                                [ "taxid_list", parse_taxid_list ],#-- list of node ids separated by a single space
                            ],
                            "db"        : db_citations
    },
    "TAXDUMP_DELNODES"  : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "header_map": [
                                [ "tax_id", int ],#-- deleted node id
                            ],
                            # "post": linearize
                            "db"        : db_delnodes
    },
    "TAXDUMP_DIVISION"  : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "header_map": [
                                [ "division id"  , int ],#-- taxonomy database division id
                                [ "division cde"       ],#-- GenBank division code (three characters)
                                [ "division name"      ],#-- e.g. BCT, PLN, VRT, MAM, PRI...
                                [ "comments"           ] #comments
                            ],
                            "db"        : db_division
    },
    "TAXDUMP_GC"        : {
                            "parser"    : read_ptr,
                            "db"        : db_gc
    },
    "TAXDUMP_GENCODE"   : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "header_map": [
                                [ "genetic code id",	int],#-- GenBank genetic code id
                                [ "abbreviation"           ],#-- genetic code name abbreviation
                                [ "name"                   ],#-- genetic code name
                                [ "cde"                    ],#-- translation table for this genetic code
                                [ "starts"                 ] #-- start codons for this genetic code
                            ],
                            "db": db_gencode
    },
    "TAXDUMP_MERGED"    : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "header_map": [
                                [ "old_tax_id"    , int    ],#-- id of nodes which has been merged
                                [ "new_tax_id"    , int    ] #-- id of nodes which is result of merging
                            ],
                            "db": db_merged
    },
    "TAXDUMP_NAMES"     : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "header_map": [
                                [ "tax_id"     , int                   ],#-- the id of node associated with this name
                                [ "name_txt"                           ],#-- name itself
                                [ "unique name"                        ],#-- the unique variant of this name if name not unique
                                [ "name class"                         ] #-- (synonym, common name, ...)
                                #[ "name class" , holders["name class"] ] #-- (synonym, common name, ...)
                            ],
                            "db": db_names
    },
    "TAXDUMP_NODES"     : {
                            "parser"    : read_dump,
                            "has_header": False,
                            "header_map": [
                                [ "tax_id"                       , int             ],#-- node id in GenBank taxonomy database
                                [ "parent tax_id"                , int             ],#-- parent node id in GenBank taxonomy database
                                #[ "rank"                         , holders["rank"] ],#-- rank of this node (superkingdom, kingdom, ...)
                                [ "rank"                                           ],#-- rank of this node (superkingdom, kingdom, ...)
                                [ "embl code"                                      ],#-- locus-name prefix; not unique
                                [ "division id"                  , int             ],#-- see division.dmp file
                                [ "inherited div flag"           , parse_flag      ],#-- 1 if node inherits division from parent
                                [ "genetic code id"              , int             ],#-- see gencode.dmp file
                                [ "inherited GC flag"            , parse_flag      ],#-- 1 if node inherits genetic code from parent
                                [ "mitochondrial genetic code id", int             ],#-- see gencode.dmp file
                                [ "inherited MGC flag"           , parse_flag      ],#-- 1 if node inherits mitochondrial gencode from parent
                                [ "GenBank hidden flag"          , parse_flag      ],#-- 1 if name is suppressed in GenBank entry lineage
                                [ "hidden subtree root flag"     , parse_flag      ],#-- 1 if this subtree has no sequence data yet
                                [ "comments"                                       ] #-- free-text comments and citations
                            ],
                            "db": db_nodes
    }
}




if __name__ == "__main__":
    main()









"""
db TAXDUMP_GENCODE   ['genetic code id', 'abbreviation', 'name', 'cde', 'starts']
db CCODE             ['coll_id', 'inst_id', 'coll_name', 'coll_code', 'coll_size', 'collection_type', 'coll_status', 'coll_url', 'comments', 'qualifier_type']
db COWNER            ['inst_id', 'inst_code', 'aka', 'inst_name', 'country', 'address', 'phone', 'fax', 'record_source', 'home_url', 'url_rule', 'comments', 'collection_type', 'qualifier_type', 'unique_name']
db TAXDUMP_DIVISION  ['division id', 'division cde', 'division name', 'comments']
db TAXDUMP_GC        ['Base1', 'Base2', 'Base3', 'id', 'name', 'name2', 'ncbieaa', 'sncbieaa']
db TAXDUMP_NAMES     ['tax_id', 'name_txt', 'unique name', 'name class']
db COLL              ['inst_code', 'inst_type', 'inst_name']
db ICODE             ['inst_id', 'inst_code', 'unique_name']
db TAXDUMP_MERGED    ['old_tax_id', 'new_tax_id']
db TAXDUMP_DELNODES  ['tax_id']
db TAXDUMP_NODES     ['tax_id', 'parent tax_id', 'rank', 'embl code', 'division id', 'inherited div flag', 'genetic code id', 'inherited GC flag', 'mitochondrial genetic code id', 'inherited MGC flag', 'GenBank hidden flag', 'hidden subtree root flag', 'comments']
db TAXDUMP_CITATIONS ['cit_id', 'cit_key', 'pubmed_id', 'medline_id', 'url', 'text', 'taxid_list']
db CATEGORIES        ['top_level_category', 'species_level_taxid', 'taxid']




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
