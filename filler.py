#!/usr/bin/python

import os
import sys

import parser_SQL_struct


class csv_holder(object):
    def __init__(self, incsv, col_names):
        self.incsv      = incsv
        self.col_names  = col_names
        self.num_levels = len(col_names)
        self.names      = []
        self.data       = {}
        self.read_csv()
        
    def read_csv(self):
        with open(self.incsv, 'r') as fhd:
            for line in fhd:
                line = line.strip()
                
                if len(line) == 0:
                    continue
                
                if line[0] == "#":
                    continue
                
                cols = line.split("\t")
                name = cols[0]

                if len(name) == 0:
                    continue

                if name in self.names:
                    print "duplicated name '%s'" % name
                    sys.exit(1)
                    
                self.names.append( name )
                
                self.data[ name ] = [None]*self.num_levels

    def save(self, filename):
        print "saving to %s" % filename
        with open(filename, 'w') as fhd:
            #print self.col_names
            fhd.write("name\t" + "\t".join(self.col_names) + "\n")
            for name in self.names:
                data = self.data[name]
                #print data
                cols = name + "\t" + "\t".join([str(d) if d is not None else "" for d in data])
                fhd.write( cols + "\n" )
        

class filler(object):
    def __init__(self, csv, querier):
        self.csv     = csv
        self.querier = querier
        self.get_ids()
        self.get_taxonomy()

    def get_ids(self):
        for name in sorted(self.csv.names):
            tax_ids = self.querier(name)
            
            if   len(tax_ids) == 0:
                print "Species '%s' does not exists" % name
                sys.exit(1)
            elif len(tax_ids) > 1:
                print "More than one instance of %s" % name
                sys.exit(1)
            else:
                tax_id = tax_ids[0]
                print "adding species %-30s id %7d" % (name, tax_id)
                self.csv.data[name][1] = tax_id
                #break
                
    def get_taxonomy(self):
        for name in sorted(self.csv.data):
            tax_id        = self.csv.data[name][1]

            print "getting taxonomy of '%s' id %d" % ( name, tax_id )
            node          = get_node(tax_id)

            #print " node", node
            data          = parse_node(node)

            division_id   = node.division_id
            division_name = get_division_name(division_id)
            print " division_id", division_id, "division_name", division_name

            

            for d in data:
                p_rank   = d[0]
                p_tax_id = d[1]
                p_name   = get_name_from_tax_id(p_tax_id)[0]
                d[3]     = p_name
                print "  parent rank %-15s id %7d name %-30s" % (p_rank, p_tax_id, p_name)
            
                if p_rank in self.csv.col_names:
                    p_pos = self.csv.col_names.index(p_rank)
                    self.csv.data[name][p_pos] = p_name
            
            self.csv.data[name][0] = division_name
            #print self.csv.data[name]
            
            #break

def parse_node(node):
    data            = []
    parent          = node.parent

    data.append( [node.rank, node.tax_id, parent.parent.tax_id, None] )
    #print "  ", data[-1]

    while parent.tax_id != 1:
        data.append( [parent.rank, parent.tax_id, parent.parent.tax_id, None] )
        #print "  ", data[-1]
        parent = parent.parent

    data.append( [parent.rank, parent.tax_id, parent.parent.tax_id, None] )

    #print "  ", data[-1]
    return data

def get_ranks():
    field = parser_SQL_struct.db_nodes.rank
    ranks = session.query(field).distinct().all()
    ranks = [r.rank for r in ranks]
    ranks.sort()
    ranks.remove("no rank")
    return ranks

def query_name(name):
    field1 = parser_SQL_struct.db_names.name_txt
    field2 = parser_SQL_struct.db_names.name_class
    names  = session.query(field1).filter(field1 == name, field2 == "scientific name").all()
    names  = [n.name_txt for n in names]
    names.sort()
    return names

def get_tax_id_from_name(name):
    field1 = parser_SQL_struct.db_names.tax_id
    field2 = parser_SQL_struct.db_names.name_txt
    field3 = parser_SQL_struct.db_names.name_class
    names  = session.query(field1).filter(field2 == name, field3 == "scientific name").all()
    names  = [n.tax_id for n in names]
    names.sort()
    return names

def get_name_from_tax_id(tax_id):
    field1 = parser_SQL_struct.db_names.name_txt
    field2 = parser_SQL_struct.db_names.tax_id
    field3 = parser_SQL_struct.db_names.name_class
    names  = session.query(field1).filter(field2 == tax_id, field3 == "scientific name").all()
    names  = [n.name_txt for n in names]
    names.sort()
    return names

def get_division_name(division_id):
    field1 = parser_SQL_struct.db_division
    divs   = session.query(field1.division_name).filter(field1.division_id == division_id).first()
    return divs.division_name

def get_node(tax_id):
    field1 = parser_SQL_struct.db_nodes
    nodes  = session.query(field1).filter(field1.tax_id == tax_id).first()
    #names  = [n.tax_id for n in names]
    #names.sort()
    return nodes

session  = None
database = None

def main(args):
    cmd   = args[0]

    print "creating db"
    parser_SQL_struct.load_db()

    global session
    global database
    session  = parser_SQL_struct.session
    database = parser_SQL_struct.database

    if   cmd == "list":
        ranks = get_ranks()
        print "\n".join( ranks )
        
    elif cmd == "fill":
        incsv  = args[1]
        ranks  = get_ranks()
        ranks.insert(0, "tax_id"  )
        ranks.insert(0, "division")
        holder = csv_holder(incsv, ranks)
        fill   = filler(holder, get_tax_id_from_name)
        holder.save(incsv + '.filled.csv')
        
    elif cmd == "query":
        name =  args[1]
        print "Querying '%s'" % name
        #names = query_name(name)
        names = get_tax_id_from_name(name)
        if len(names) > 0:
            print "\n".join( [str(x) for x in names] )

        else:
            print "Species '%s' does not exists" % name
    

if __name__ == '__main__':
    main(sys.argv[1:])
    
    
#ncbi_taxonomy.db_division.tsv
#division_id     division_cde    division_name   comments
#0       BCT     Bacteria
#1       INV     Invertebrates
#2       MAM     Mammals
#3       PHG     Phages
#4       PLN     Plants
#5       PRI     Primates
#6       ROD     Rodents
#7       SYN     Synthetic
#8       UNA     Unassigned      No species nodes should inherit this division assignment
#9       VRL     Viruses
#10      VRT     Vertebrates
#11      ENV     Environmental samples   Anonymous sequences cloned directly from the environment
#CREATE TABLE division (
#        division_id INTEGER NOT NULL,
#        division_cde VARCHAR(10),
#        division_name VARCHAR(15),
#        comments VARCHAR(100),
#        PRIMARY KEY (division_id),
#        FOREIGN KEY(division_id) REFERENCES nodes (division_id)
#);


#ncbi_taxonomy.db_names.tsv
#tax_id  name_txt        unique_name     name_class
#1       all             synonym
#1       root            scientific name
#2       Bacteria        Bacteria <prokaryote>   scientific name
#2       Monera  Monera <Bacteria>       in-part
#2       Procaryotae     Procaryotae <Bacteria>  in-part
#2       Prokaryota      Prokaryota <Bacteria>   in-part
#2       Prokaryotae     Prokaryotae <Bacteria>  in-part
#2       bacteria        bacteria <blast2>       blast name
#2       eubacteria              genbank common name
#2       not Bacteria Haeckel 1894               synonym
#2       prokaryote      prokaryote <Bacteria>   in-part
#2       prokaryotes     prokaryotes <Bacteria>  in-part
#CREATE TABLE names (
#        tax_id INTEGER NOT NULL,
#        name_txt VARCHAR(10) NOT NULL,
#        unique_name VARCHAR(10),
#        name_class VARCHAR(10) NOT NULL,
#        PRIMARY KEY (tax_id, name_txt, name_class),
#        FOREIGN KEY(tax_id) REFERENCES nodes (tax_id)
#);


#ncbi_taxonomy.db_nodes.tsv
#tax_id  parent_tax_id   rank    embl_code       division_id     inherited_div_flag      genetic_code_id inherited_gc_flag       mitochondrial_genetic_code_id   inherited_mgc_flag      genbank_hidden_flag     hidden_subtree_root_flag
#        comments
#1       1       no rank         8       0       1       0       0       0       0       0
#2       131567  superkingdom            0       0       11      0       0       0       0       0
#6       335928  genus           0       1       11      1       0       1       0       0
#7       6       species AC      0       1       11      1       0       1       1       0
#9       32199   species BA      0       1       11      1       0       1       1       0
#10      135621  genus           0       1       11      1       0       1       0       0
#11      1707    species CG      0       1       11      1       0       1       1       0
#13      203488  genus           0       1       11      1       0       1       0       0
#14      13      species DT      0       1       11      1       0       1       1       0
#16      32011   genus           0       1       11      1       0       1       0       0
#17      16      species MM      0       1       11      1       0       1       1       0
#18      213423  genus           0       1       11      1       0       1       0       0
#19      18      species PC      0       1       11      1       0       1       1       0
#20      76892   genus           0       1       11      1       0       1       0       0
#CREATE TABLE nodes (
#        tax_id INTEGER NOT NULL,
#        parent_tax_id INTEGER,
#        rank VARCHAR(10),
#        embl_code VARCHAR(10),
#        division_id INTEGER,
#        inherited_div_flag BOOLEAN,
#        genetic_code_id INTEGER,
#        inherited_gc_flag BOOLEAN,
#        mitochondrial_genetic_code_id INTEGER,
#        inherited_mgc_flag BOOLEAN,
#        genbank_hidden_flag BOOLEAN,
#        hidden_subtree_root_flag BOOLEAN,
#        comments VARCHAR(100),
#        PRIMARY KEY (tax_id),
#        FOREIGN KEY(parent_tax_id) REFERENCES nodes (tax_id),
#        CHECK (inherited_div_flag IN (0, 1)),
#        CHECK (inherited_gc_flag IN (0, 1)),
#        CHECK (inherited_mgc_flag IN (0, 1)),
#        CHECK (genbank_hidden_flag IN (0, 1)),
#        CHECK (hidden_subtree_root_flag IN (0, 1))
#);

