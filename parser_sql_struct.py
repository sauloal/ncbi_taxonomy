import os
import sqlalchemy
from sqlalchemy                 import create_engine
from sqlalchemy.orm             import sessionmaker
from sqlalchemy.orm             import relationship, backref
from sqlalchemy                 import Table, Column, Integer, String, Boolean
from sqlalchemy                 import MetaData, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

print "sqlalchemy", sqlalchemy.__version__ 

SQL_ECHO = False
#engine   = create_engine('sqlite:///:memory:', echo=SQL_ECHO)
SQL_FILE_NAME = "ncbi_taxonomy.db"

if os.path.exists(SQL_FILE_NAME):
    os.remove(SQL_FILE_NAME)

engine   = create_engine('sqlite:///'+SQL_FILE_NAME  , echo=SQL_ECHO)

Session  = sessionmaker(bind=engine, autoflush=True, autocommit=False, expire_on_commit=True)
session  = Session()
Base     = declarative_base()
metadata = MetaData()

#BigInteger
#Boolean
#Date
#DateTime
#Enum
#Float
#Integer
#LargeBinary
#Numeric
#PickleType
#SmallInteger
#Text
#Time



#[ "CCODE"            , "inst_id"                       ],
#[ "COWNER"           , "inst_id"                       ],
#[ "ICODE"            , "inst_id"                       ]
#
#[ "TAXDUMP_NODES"    , "parent tax_id"                 ],
#[ "TAXDUMP_NODES"    , "tax_id"                        ],
#[ "TAXDUMP_NAMES"    , "tax_id"                        ],
#[ "TAXDUMP_CITATIONS", "taxid_list"                    ],
#[ "CATEGORIES"       , "taxid"                         ],
#[ "CATEGORIES"       , "species_level_taxid"           ],
#[ "TAXID_NUC"        , "taxid"                         ],
#[ "TAXID_PROT"       , "taxid"                         ],
#
#[ "TAXDUMP_NODES"    , "division id"                   ],
#[ "TAXDUMP_DIVISION" , "division id"                   ]
#
#[ "TAXDUMP_NODES"    , "genetic code id"               ],
#[ "TAXDUMP_GENCODE"  , "genetic code id"               ]
#
#[ "TAXDUMP_NODES"    , "mitochondrial genetic code id" ],
#[ "TAXDUMP_GENCODE"  , "genetic code id"               ]


class db_ccode(Base):
    __tablename__   = 'ccode'
    coll_id         = Column(Integer, primary_key=True            )
    inst_id         = Column(Integer                  , index=True)
    coll_name       = Column(String( 50)                          )
    coll_code       = Column(String( 10)              , index=True)
    coll_size       = Column(Integer                              )
    collection_type = Column(String( 50)              , index=True)
    coll_status     = Column(Boolean                              )
    coll_url        = Column(String(150)                          )
    comments        = Column(String(200)                          )
    qualifier_type  = Column(String( 50)                          )
        
    def __repr__(self):
        return "<ccode(coll_id=%d, inst_id=%d, coll_name='%s', coll_code='%s', coll_size=%d, collection_type='%s', coll_status=%s, coll_url='%s', comments='%s', qualifier_type='%s')>" % (
            self.coll_id,
            self.inst_id,
            self.coll_name,
            self.coll_code,
            self.coll_size,
            self.collection_type,
            str(self.coll_status),
            self.coll_url,
            self.comments,
            self.qualifier_type
        )
    #CCODE(coll_id=7166, inst_id=362, coll_name='Herpetology Collection', coll_code='Herp',
    #coll_size=0, collection_type='museum', coll_status=False, coll_url='',
    #comments='', qualifier_type='specimen_voucher')

class db_coll(Base):
    __tablename__ = 'coll'
    inst_code     = Column(String( 10), primary_key=True            )
    inst_type     = Column(String(  5)                  , index=True)
    inst_name     = Column(String(100)                              )

    def __repr__(self):
        return "<coll(inst_code='%s', inst_type='%s' inst_name='%s')>" % (
            self.inst_code,
            self.inst_type,
            self.inst_name)
    
    #COLL(inst_code='A', inst_type='s', inst_name='Arnold Arboretum, Harvard University')

class db_cowner(Base):
    __tablename__   = 'cowner'
    inst_id         = Column(Integer    , primary_key=True            ) #1,
    inst_code       = Column(String( 10)                  , index=True) #'AEI',
    aka             = Column(String( 10)                              ) #'',
    inst_name       = Column(String(100)                              ) #'American Entomological Institute',
    country         = Column(String(  3)                              ) #'USA',
    address         = Column(String(200)                              ) #'3005 SW 56th Avenue, Gainesville, Florida 32608-5047',
    phone           = Column(String( 50)                              ) #'',
    fax             = Column(String( 50)                              ) #'',
    record_source   = Column(String( 20)                              ) #'',
    home_url        = Column(String(200)                              ) #'http://aei.tamu.edu/projects/17/public/site/aei/home',
    url_rule        = Column(String( 20)                              ) #'',
    comments        = Column(String(200)                              ) #'',
    collection_type = Column(String( 50)                  , index=True) #'museum',
    qualifier_type  = Column(String( 50)                  , index=True) #'specimen_voucher',
    unique_name     = Column(String( 10)                  , index=True) #'AEI'


    def __repr__(self):
        return "<cowner(inst_id=%d, inst_code='%s', aka='%s', inst_name='%s', country='%s', address='%s', phone='%s', fax='%s', record_source='%s', home_url='%s', url_rule='%s', comments='%s', collection_type='%s', qualifier_type='%s', unique_name='%s')>" % (
            self.inst_id         ,
            self.inst_code       ,
            self.aka             ,
            self.inst_name       ,
            self.country         ,
            self.address         ,
            self.phone           ,
            self.fax             ,
            self.record_source   ,
            self.home_url        ,
            self.url_rule        ,
            self.comments        ,
            self.collection_type ,
            self.qualifier_type  ,
            self.unique_name     ,
        )
    #COWNER(inst_id=1, inst_code='AEI', aka='', inst_name='American Entomological Institute',
    #country='USA', address='3005 SW 56th Avenue, Gainesville, Florida 32608-5047',
    #phone='', fax='', record_source='', home_url='http://aei.tamu.edu/projects/17/public/site/aei/home',
    #url_rule='', comments='', collection_type='museum',
    #qualifier_type='specimen_voucher', unique_name='AEI')

class db_icode(Base):
    __tablename__ = 'icode'
    inst_id         = Column(Integer    , primary_key=True) #1,
    inst_code       = Column(String( 10)                  ) #'AEI',
    unique_name     = Column(String( 10)                  ) #'American Entomological Institute',

    def __repr__(self):
        return "<cowner(inst_id=%d, inst_code='%s', inst_name='%s')>" % (
            self.inst_id         ,
            self.inst_code       ,
            self.aka             ,
            self.inst_name       ,
        )
    #ICODE(inst_id=1, inst_code='AEI', unique_name='AEI')

class db_categories(Base):
    __tablename__       = 'categories'
    top_level_category  = Column(String(1), primary_key=True            ) #'A',
    species_level_taxid = Column(Integer                    , index=True) #1462428,
    taxid               = Column(Integer  , primary_key=True            ) #1462428

    def __repr__(self):
        return "<categories(top_level_category='%s', species_level_taxid=%d, taxid=%d)>" % (
            self.top_level_category , #'A',
            self.species_level_taxid, #1462428,
            self.taxid              , #1462428
        )
    #CATEGORIES(top_level_category='A', species_level_taxid=1462428, taxid=1462428)

class db_citations(Base):
    __tablename__ = 'citations'
    cit_id        = Column(Integer    , primary_key=True            ) #5,
    cit_key       = Column(String(300)                              ) # 'The domestic cat: perspective on the nature and diversity of cats.',
    pubmed_id     = Column(Integer                      , index=True) # 0,
    medline_id    = Column(Integer                      , index=True) # 8603894,
    url           = Column(String(300)                              ) #'',
    text          = Column(String(300)                              ) #'',
    taxid_list    = Column(String(300)                              ) # [9685]

    def __init__(self, cit_id, cit_key, pubmed_id, medline_id, url, text, taxid_list):
        self.cit_id     = cit_id
        self.cit_key    = cit_key
        self.pubmed_id  = pubmed_id
        self.medline_id = medline_id
        self.url        = url
        self.text       = text
        self.taxid_list = ",".join([str(x) for x in taxid_list]) if taxid_list is not None else None

    def __repr__(self):
        return "<citations(cit_id=%d, cit_key='%s', pubmed_id=%d)>" % (
            self.cit_id,
            self.cit_key,
            self.pubmed_id,
            self.medline_id,
            self.url,
            self.text,
            self.taxid_list
        )
    #TAXDUMP_CITATIONS(cit_id=5, cit_key='The domestic cat: perspective on the nature and diversity of cats.',
    #pubmed_id=0, medline_id=8603894, url='', text='', taxid_list=[9685])

class db_delnodes(Base):
    __tablename__ = 'delnodes'
    tax_id        = Column(Integer  , primary_key=True) #1608297

    def __repr__(self):
        return "<delnodes(tax_id=%d)>" % (
            self.tax_id , #1608297,
        )
    #TAXDUMP_DELNODES(tax_id=1608297)

class db_division(Base):
    __tablename__ = 'division'
    division_id   = Column(Integer, primary_key=True) #0,
    division_cde  = Column(String( 10)              ) #'BCT',
    division_name = Column(String( 15)              ) #'Bacteria'
    comments      = Column(String(100)              ) #''

    def __repr__(self):
        return "<division(division_id=%d, division_cde='%s', division_name='%s', comments='%s')>" % (
            self.division_id,  #0,
            self.division_cde, #'BCT',
            self.division_name,#'Bacteria'
            self.comments,     #''
        )
    #TAXDUMP_DIVISION(division_id=0, division_cde='BCT', division_name='Bacteria', comments='')

class db_gc(Base):
    __tablename__ = 'gc'
    id            = Column(Integer, primary_key=True) #1,
    name          = Column(String( 10)              ) #'Standard',
    name2         = Column(String( 10)              ) #'SGC0',
    Base1         = Column(String(100)              ) #'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG',
    Base2         = Column(String(100)              ) #'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG',
    Base3         = Column(String(100)              ) #'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG',
    ncbieaa       = Column(String(100)              ) #'FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"',
    sncbieaa      = Column(String(100)              ) #'M---------------M---------------M')

    def __repr__(self):
        return "<gc(id=%d, name='%s', name2='%s', Base1='%s', Base2='%s', Base3='%s', ncbieaa='%s', sncbieaa='%s')>" % (
            self.id       ,
            self.name     ,
            self.name2    ,
            self.Base1    ,
            self.Base2    ,
            self.Base3    ,
            self.ncbieaa  ,
            self.sncbieaa 
        )
    #id=1, name='Standard', name2='SGC0',
    #TAXDUMP_GC(Base1='TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG',
    #Base2='TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG',
    #Base3='TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG',
    #ncbieaa='FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"',
    #sncbieaa='M---------------M---------------M')

class db_gencode(Base):
    __tablename__   = 'gencode'
    #ForeignKey('nodes.mitochondrial_genetic_code_id'), 
    genetic_code_id = Column(Integer    , ForeignKey('nodes.genetic_code_id'), primary_key=True) #1
    abbreviation    = Column(String( 10)                                              ) #'', 
    name            = Column(String( 10)                                              ) #'Standard',
    cde             = Column(String(100)                                              ) #'FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG',
    starts          = Column(String(100)                                              ) #'---M---------------M---------------M----------------------------')

    def __repr__(self):
        return "<gencode(genetic_code_id=%d, abbreviation='%s', name='%s', cde='%s', starts='%s')>" % (
            self.genetic_code_id,
            self.abbreviation   ,
            self.name           ,
            self.cde            ,
            self.starts
        )
    #TAXDUMP_GENCODE(genetic_code_id=1, abbreviation='', name='Standard',
    #cde='FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG',
    #starts='---M---------------M---------------M----------------------------')

class db_names(Base):
    __tablename__ = 'names'
    tax_id        = Column(Integer   , ForeignKey('nodes.tax_id'), primary_key=True) #1
    name_txt      = Column(String(10),                             primary_key=True) #'all',
    unique_name   = Column(String(10)                                              ) #'',
    name_class    = Column(String(10),                             primary_key=True) #'synonym',

    def __repr__(self):
        return "<names(tax_id=%d, name_txt='%s', unique_name='%s', name_class='%s')>" % (
            self.tax_id,
            self.name_txt,
            self.unique_name,
            self.name_class
        )
    #TAXDUMP_NAMES(tax_id=1, name_txt='all', unique_name='', name_class='synonym')

class db_taxid_nuc(Base):
    __tablename__ = 'taxid_nuc'
    gi            = Column(Integer  ,                             primary_key=True            ) #1608297
    taxid         = Column(Integer  , ForeignKey('nodes.tax_id'),                   index=True) #1608297

    def __repr__(self):
        return "<taxid_nuc(gi=%d, tax_id=%d)>" % (
            self.gi, #1608297,
            self.tax_id, #1608297,
        )

class db_taxid_prot(Base):
    __tablename__ = 'db_taxid_prot'
    gi            = Column(Integer  ,                             primary_key=True            ) #1608297
    taxid         = Column(Integer  , ForeignKey('nodes.tax_id'),                   index=True) #1608297

    def __repr__(self):
        return "<db_taxid_prot(gi=%d, tax_id=%d)>" % (
            self.gi, #1608297,
            self.tax_id, #1608297,
        )

class db_nodes(Base):
    __tablename__                 = 'nodes'
    tax_id                        = Column(Integer    ,                             primary_key=True            )#1,
    parent_tax_id                 = Column(Integer    , ForeignKey('nodes.tax_id')                  , index=True)#1,
    rank                          = Column(String( 10)                                              , index=True) #'no rank',
    embl_code                     = Column(String( 10)                                                          ) #'',
    division_id                   = Column(Integer                                                  , index=True) #8,
    inherited_div_flag            = Column(Boolean                                                              ) #False,
    genetic_code_id               = Column(Integer                                                  , index=True) #1,
    inherited_GC_flag             = Column(Boolean                                                              ) #False,
    mitochondrial_genetic_code_id = Column(Integer                                                  , index=True) #0,
    inherited_MGC_flag            = Column(Boolean                                                              ) #False,
    GenBank_hidden_flag           = Column(Boolean                                                              ) #False,
    hidden_subtree_root_flag      = Column(Boolean                                                              ) #False,
    comments                      = Column(String(100)                                                          ) #''
    
    #http://docs.sqlalchemy.org/en/rel_0_9/orm/self_referential.html
    children = relationship("db_nodes",
                backref=backref('parent', remote_side=[tax_id])
            )
    
    nucleotides  = relationship("db_taxid_nuc" , order_by="db_taxid_nuc.gi"     , backref=backref("nodes"        , uselist=False)               )
    proteins     = relationship("db_taxid_prot", order_by="db_taxid_prot.gi"    , backref=backref("nodes"        , uselist=False)               )
    name         = relationship("db_names"     , order_by="db_names.unique_name", backref=backref("nodes"                       ), uselist=False)
    genetic_code = relationship("db_gencode"   , order_by="db_gencode.name"     , backref=backref("nodes_genetic"               ), uselist=False, foreign_keys=genetic_code_id)


    #user = relationship("User", backref=backref('addresses', order_by=id))
    #addresses = relationship("Address", order_by="Address.id", backref="user")

    def __repr__(self):
        return "<names(tax_id=%d, parent_tax_id=%d, rank='%s', embl_code='%s', division_id=%d, inherited_div_flag=%s, genetic_code_id=%d, inherited_GC_flag=%s, mitochondrial_genetic_code_id=%d, inherited_MGC_flag=%s, GenBank_hidden_flag=%s, hidden_subtree_root_flag=%s, comments='%s')>" % (
            self.tax_id                        ,
            self.parent_tax_id                 ,
            self.rank                          ,
            self.embl_code                     ,
            self.division_id                   ,
            str(self.inherited_div_flag)       ,
            self.genetic_code_id               ,
            str(self.inherited_GC_flag)        ,
            self.mitochondrial_genetic_code_id ,
            str(self.inherited_MGC_flag)       ,
            str(self.GenBank_hidden_flag)      ,
            str(self.hidden_subtree_root_flag) ,
            self.comments                      
        )
    #TAXDUMP_NODES(tax_id=1, parent_tax_id=1, rank='no rank', embl_code='',
    #division_id=8, inherited_div_flag=False, genetic_code_id=1, inherited_GC_flag=False,
    #mitochondrial_genetic_code_id=0, inherited_MGC_flag=False, GenBank_hidden_flag=False,
    #hidden_subtree_root_flag=False, comments='')

#[ "CCODE"            , "inst_id"                       ],
#[ "COWNER"           , "inst_id"                       ],
#[ "ICODE"            , "inst_id"                       ]
#
#[ "TAXDUMP_NODES"    , "parent tax_id"                 ],
#[ "TAXDUMP_NODES"    , "tax_id"                        ],
#[ "TAXDUMP_NAMES"    , "tax_id"                        ],
#[ "TAXDUMP_CITATIONS", "taxid_list"                    ],
#[ "CATEGORIES"       , "taxid"                         ],
#[ "CATEGORIES"       , "species_level_taxid"           ],
#[ "TAXID_NUC"        , "taxid"                         ],
#[ "TAXID_PROT"       , "taxid"                         ],
#
#[ "TAXDUMP_NODES"    , "division id"                   ],
#[ "TAXDUMP_DIVISION" , "division id"                   ]
#
#[ "TAXDUMP_NODES"    , "genetic code id"               ],
#[ "TAXDUMP_GENCODE"  , "genetic code id"               ]
#
#[ "TAXDUMP_NODES"    , "mitochondrial genetic code id" ],
#[ "TAXDUMP_GENCODE"  , "genetic code id"               ]



class db_merged(Base):
    __tablename__ = 'merged'
    old_tax_id    = Column(Integer  , primary_key=True            ) #1608297
    new_tax_id    = Column(Integer                    , index=True) #1608297

    def __repr__(self):
        return "<merged(old_tax_id=%d, new_tax_id=%d)>" % (
            self.old_tax_id, #1608297,
            self.new_tax_id, #1608297,
        )
    #TAXDUMP_MERGED(old_tax_id=12, new_tax_id=74109)




#ICODE(inst_id=1, inst_code='AEI', unique_name='AEI')
#CATEGORIES(top_level_category='A', species_level_taxid=1462428, taxid=1462428)
#CCODE(coll_id=7166, inst_id=362, coll_name='Herpetology Collection', coll_code='Herp', coll_size=0, collection_type='museum', coll_status=False, coll_url='', comments='', qualifier_type='specimen_voucher')
#COLL(inst_code='A', inst_type='s', inst_name='Arnold Arboretum, Harvard University')
#COWNER(inst_id=1, inst_code='AEI', aka='', inst_name='American Entomological Institute', country='USA', address='3005 SW 56th Avenue, Gainesville, Florida 32608-5047', phone='', fax='', record_source='', home_url='http://aei.tamu.edu/projects/17/public/site/aei/home', url_rule='', comments='', collection_type='museum', qualifier_type='specimen_voucher', unique_name='AEI')
#TAXDUMP_GENCODE(genetic_code_id=1, abbreviation='', name='Standard', cde='FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG', starts='---M---------------M---------------M----------------------------')
#TAXDUMP_GC(Base1='TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG', Base2='TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG', Base3='TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG', id=1, name='Standard', name2='SGC0', ncbieaa='FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"', sncbieaa='M---------------M---------------M')
#TAXDUMP_NODES(tax_id=1, parent_tax_id=1, rank='no rank', embl_code='', division_id=8, inherited_div_flag=False, genetic_code_id=1, inherited_GC_flag=False, mitochondrial_genetic_code_id=0, inherited_MGC_flag=False, GenBank_hidden_flag=False, hidden_subtree_root_flag=False, comments='')
#TAXDUMP_MERGED(old_tax_id=12, new_tax_id=74109)
#TAXDUMP_CITATIONS(cit_id=5, cit_key='The domestic cat: perspective on the nature and diversity of cats.', pubmed_id=0, medline_id=8603894, url='', text='', taxid_list=[9685])
#TAXDUMP_DIVISION(division_id=0, division_cde='BCT', division_name='Bacteria', comments='')
#TAXDUMP_NAMES(tax_id=1, name_txt='all', unique_name='', name_class='synonym')
#TAXDUMP_DELNODES(tax_id=1608297)


Base.metadata.create_all(engine)

for t in metadata.sorted_tables:
    print t.name



#trans = session.begin()
#r1 = session.execute(table1.select())
#session.execute(table1.insert(), col1=7, col2='this is some data')
#trans.commit()
#session.close()
