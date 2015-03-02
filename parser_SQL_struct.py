import os
from collections import namedtuple


import sqlalchemy
from sqlalchemy                   import create_engine
from sqlalchemy.orm               import sessionmaker, scoped_session
from sqlalchemy.orm               import relationship, backref
from sqlalchemy                   import Table, Column, Integer, String, Boolean, Index
from sqlalchemy                   import MetaData, ForeignKey
from sqlalchemy.ext.declarative   import declarative_base
from sqlalchemy.engine            import reflection
from sqlalchemy.dialects          import mysql, sqlite
from sqlalchemy.engine.interfaces import Compiled
from sqlalchemy.sql.expression    import insert
from sqlalchemy.sql               import compiler

from sqlalchemy.schema import (
    MetaData,
    Table,
    DropTable,
    ForeignKeyConstraint,
    DropConstraint,
    )

print "sqlalchemy", sqlalchemy.__version__ 

SQL_ECHO = False
#engine   = create_engine('sqlite:///:memory:', echo=SQL_ECHO)
SQL_FILE_NAME = "ncbi_taxonomy.db"

Base      = declarative_base()
session   = None
database  = None
indexes   = {}



def dump_all(tables=None):
    dump_schema()
    dump_tables()
    dump_sql()
    if tables is not None:
        dump_tsv(tables)

def dump_schema():
    print "dumping schema"
    os.system( "echo .schema | sqlite3 %s > %s.schema"  % (SQL_FILE_NAME,SQL_FILE_NAME) )

def dump_tsv(tables):
    print "dumping tsv"
    for table in tables:
        print "dumping tsv", table, "to %(file_name)s_%(table_name)s.tsv" % { "file_name": SQL_FILE_NAME, "table_name": table }
        os.system( 'echo ".header on\n.mode tabs\n.output %(file_name)s_%(table_name)s.tsv\nSELECT * FROM %(table_name)s;" | sqlite3 %(file_name)s >/dev/null' % { "file_name": SQL_FILE_NAME, "table_name": table } )

def dump_tables():
    print "dumping tables"
    os.system( "echo .tables | sqlite3 %s > %s.tables"  % (SQL_FILE_NAME,SQL_FILE_NAME) )

def dump_sql():
    print "dumping sql"
    os.system( "echo .dump | sqlite3 %s > %s.sql"  % (SQL_FILE_NAME,SQL_FILE_NAME) )



def load_db():
    #loaddb(SQL_FILE_NAME, echo=False)
    global database
    #database        = loaddb(db_data_name=SQL_FILE_NAME)
    database        = db_controller(SQL_FILE_NAME, Base)

    global session
    session = database.get_session()
    print 'session', session


def create_db():
    if os.path.exists(SQL_FILE_NAME):
        os.remove(SQL_FILE_NAME)
    
    load_db()

    return database

    #engine   = create_engine('sqlite:///'+SQL_FILE_NAME  , echo=SQL_ECHO)
    
    #global session
    #Session   = sessionmaker(bind=engine, autoflush=True, autocommit=False, expire_on_commit=True)
    #session   = Session()
    #metadata  = MetaData()
    #inspector = reflection.Inspector.from_engine(engine)
    
    #Base.metadata.create_all(engine)
    
    #for t in metadata.sorted_tables:
    #    print t.name
    


    #os.system( "echo .schema | sqlite3 %s > %s.schema"  % (SQL_FILE_NAME,SQL_FILE_NAME) )
    
    #for table_name in inspector.get_table_names():
    #    print "dropping foreign keys", table_name
    #    for index in inspector.get_indexes(table_name):
    #        print " index", index

    #session.execute ('PRAGMA foreign_keys = ON;')
    #session.execute ('PRAGMA foreign_keys=OFF')
    #session.commit()
    
    
    #trans = session.begin()
    #r1 = session.execute(table1.select())
    #session.execute(table1.insert(), col1=7, col2='this is some data')
    #trans.commit()
    #session.close()







#class DataBase(Base):
#    __abstract__ = True
#    metadata = MetaData()


class loaddb(object):
    def __init__(self, db_data_name=None, db_index_name=None, db_meta_name=None, dbtype='SQLITE', echo=False, synchronous=False, inmemory=True, sql_user=None, sql_pass=None, sql_host=None, sql_port=None, sql_sock=None):
        print "creating engine", db_data_name

        #http://stackoverflow.com/questions/8831568/sqlalchemy-declarative-model-with-multiple-database-sharding

        self.dbtype        = dbtype
        self.db_data_name  = db_data_name
        self.db_index_name = db_index_name
        self.db_meta_name  = db_meta_name
        self.db_data       = None
        self.db_index      = None
        self.db_meta       = None

        if self.db_data_name:
            self.db_data  = db_controller( db_data_name , Base     , dbtype='SQLITE', echo=echo, synchronous=synchronous, inmemory=inmemory, sql_user=sql_user, sql_pass=sql_pass, sql_host=sql_host, sql_port=sql_port, sql_sock=sql_sock )
            #self.db_data  = db_controller( db_data_name , DataBase , dbtype='SQLITE', echo=echo, synchronous=synchronous, inmemory=inmemory, sql_user=sql_user, sql_pass=sql_pass, sql_host=sql_host, sql_port=sql_port, sql_sock=sql_sock )

        if self.db_index_name:
            self.db_index = db_controller( db_index_name, IndexBase, dbtype='SQLITE', echo=echo, synchronous=synchronous, inmemory=inmemory, sql_user=sql_user, sql_pass=sql_pass, sql_host=sql_host, sql_port=sql_port, sql_sock=sql_sock )

        if self.db_meta_name:
            self.db_meta  = db_controller( db_meta_name , MetaBase , dbtype='SQLITE', echo=echo, synchronous=synchronous, inmemory=inmemory, sql_user=sql_user, sql_pass=sql_pass, sql_host=sql_host, sql_port=sql_port, sql_sock=sql_sock )

        self.dbs = {
            'data' : self.db_data,
            'index': self.db_index,
            'meta' : self.db_meta
        }

        print "finished"

    def list_dbs(self):
        return sorted([ x for x in self.dbs.keys() if self.dbs[x] is not None ])

    def get_dbs(self):
        dbkeys = self.list_dbs()
        print dbkeys
        res    = namedtuple(*dbkeys)
        print res
        return res( [ self.dbs[x] for x in dbkeys ])

    def get_db(self, dbname):
        db = self.dbs.get(dbname, None)
        if db:
            return db

    def get_engines(self):
        dbkeys = self.list_dbs
        res    = namedtuple(*dbkeys)
        return res( [ self.dbs[x].get_engine() for x in dbkeys ])

    def get_engine(self, dbname):
        db = self.dbs.get(dbname, None)
        if db:
            return db.get_engine()

    def get_sessions(self):
        dbkeys = self.list_dbs()
        #res    = namedtuple(*dbkeys)
        #return res( [ self.dbs[x].get_session() for x in dbkeys ])
        return [ self.dbs[x].get_session() for x in dbkeys ]

    def get_session(self, dbname):
        db = self.dbs.get(dbname, None)
        if db:
            return db.get_session()

    def get_or_update_data(self, dbname, cls, att, val):
        db = self.dbs.get(dbname, None)
        if db:
            return db.get_or_update(cls, att, val)

    def list_indexes(self, dbname, table_name=None):
        db = self.dbs.get(dbname, None)
        if db:
            return db.list_indexes(table_name=table_name)

    def drop_indexes(self, dbname, table_name=None):
        db = self.dbs.get(dbname, None)
        if db:
            return db.drop_indexes(table_name=table_name)

    def drop_index(self, dbname, table_name, info):
        db = self.dbs.get(dbname, None)
        if db:
            db.drop_index(table_name, info)

    def drop_all_indexes(self):
        indexes = {}
        print "drop_all_indexes"
        for dbname in self.list_dbs():
            print "drop_all_indexes", dbname
            indexes[dbname] = []
            #for index in self.list_indexes(dbname):
            #    print "drop_all_indexes", dbname, "index", index
            #    indexes[dbname].append( index )
            #    self.drop_indexes(dbname)
            indexes[dbname] = self.drop_indexes(dbname)
        return indexes

    def restore_all_indexes(self):
        print "restore_all_indexes"
        for dbname in self.list_dbs():
            print "restore_all_indexes", dbname
            db = self.dbs.get(dbname, None)
            if db:
                db.restore_indexes()
    
    def add_indexes(self, dbname, indexes, table_name=None):
        db = self.dbs.get(dbname, None)
        if db:
            return db.add_indexes(indexes, table_name=table_name)

    def use(self, dbname):
        db = self.dbs.get(dbname, None)
        if db:
            return db.use()

class db_controller(object):
    def __init__(self, db_name, base, dbtype='SQLITE', echo=False, synchronous=False, inmemory=True, sql_user=None, sql_pass=None, sql_host=None, sql_port=None, sql_sock=None):
        self.cache   = {}
        self.dbtype  = dbtype
        self.db_name = db_name
        self.Base    = base

        self._last_dropped_indexes = None

        if self.dbtype == 'MYSQL':
            MYSQL_NAME = os.environ['MYSQL_NAME'] if 'MYSQL_NAME' in os.environ else None
            MYSQL_USER = os.environ['MYSQL_USER'] if 'MYSQL_USER' in os.environ else 'root'
            MYSQL_PASS = os.environ['MYSQL_PASS'] if 'MYSQL_PASS' in os.environ else None
            MYSQL_HOST = os.environ['MYSQL_HOST'] if 'MYSQL_HOST' in os.environ else '127.0.0.1'
            MYSQL_PORT = os.environ['MYSQL_PORT'] if 'MYSQL_PORT' in os.environ else '3306'
            MYSQL_SOCK = os.environ['MYSQL_SOCK'] if 'MYSQL_SOCK' in os.environ else None

            self.dialect  = mysql

            if sql_user:
                MYSQL_USER = sql_user
            if sql_pass:
                MYSQL_PASS = sql_pass
            if sql_host:
                MYSQL_HOST = sql_host
            if sql_port:
                MYSQL_PORT = sql_port
            if sql_sock:
                MYSQL_SOCK = sql_sock

            if MYSQL_SOCK:
                self.sql_add = 'mysql:///?unix_socket=%(mysql_sock)s' % {
                    'mysql_user': str(MYSQL_USER),
                    'mysql_pass': str(MYSQL_PASS),
                    'mysql_host': '127.0.0.1',
                    'mysql_sock': MYSQL_SOCK,
                    'mysql_db'  : self.db_name }

                print "sql add", self.sql_add

                if not all([MYSQL_USER, MYSQL_PASS]):
                    print "mysql not fully configured"
                    sys.exit(1)

            else:
                if MYSQL_NAME:
                    self.db_name = MYSQL_NAME + '/' + self.db_name

                self.sql_add = 'mysql://%(mysql_user)s:%(mysql_pass)s@%(mysql_host)s:%(mysql_port)s/%(mysql_db)s' % {
                    'mysql_user': str(MYSQL_USER),
                    'mysql_pass': str(MYSQL_PASS),
                    'mysql_host': str(MYSQL_HOST),
                    'mysql_port': str(MYSQL_PORT),
                    'mysql_db'  : self.db_name }

                print "sql add", self.sql_add

                if not all([MYSQL_USER, MYSQL_PASS, MYSQL_HOST, MYSQL_PORT]):
                    print "mysql not fully configured"
                    sys.exit(1)


        elif self.dbtype == 'SQLITE':
            self.sql_add  = 'sqlite:///' + self.db_name
            self.dialect  = sqlite

        else:
            print "unknown database", self.dbtype
            sys.exit(1)




        print "creating session"
        self.engine  = create_engine(self.sql_add, echo=echo)
        self.Session = scoped_session( sessionmaker(bind=self.engine, autocommit=False) )#, autoflush=False, expire_on_commit=False)
        self.session = self.Session()



        if self.sql_add == 'sqlite:///:memory:' or self.dbtype == 'MYSQL' or not os.path.exists(self.db_name):
            if self.dbtype == 'MYSQL':
                try:
                    self.engine.execute("DROP DATABASE " + self.db_name) #create db
                except:
                    pass
                print "CREATING DATABASE"
                self.engine.execute("CREATE DATABASE " + self.db_name) #create db
                print "SELECTING DATABASE"
                self.engine.execute("USE " + self.db_name) # select new db

            print "creating database"
            self.Base.metadata.create_all( self.engine )
        else:
            print "NOT creating database"




        if self.dbtype == 'MYSQL':
            print "SELECTING DATABASE"
            self.session.execute("USE " + self.db_name) # select new db


        if self.dbtype == 'SQLITE':
            if not synchronous:
                self.engine.execute("PRAGMA synchronous = OFF")

            if inmemory:
                #self.session.execute("PRAGMA journal_mode = OFF")
                #self.session.execute("PRAGMA journal_mode = WAL")
                self.engine.execute("PRAGMA journal_mode = MEMORY")

            #self.session.execute("PRAGMA locking_mode = EXCLUSIVE;" )
            self.session.execute("PRAGMA temp_store = MEMORY;"       )
            self.session.execute("PRAGMA count_changes = OFF;"       )
            self.session.execute("PRAGMA PAGE_SIZE = 40960;"         )
            self.session.execute("PRAGMA default_cache_size=7000000;")
            self.session.execute("PRAGMA cache_size=7000000;"        )
            self.session.execute("PRAGMA compile_options;"           )

            self.meta    = MetaData()
            self.meta.reflect(bind=self.engine)
            self.insp    = reflection.Inspector.from_engine( self.engine )


    def use(self):
        if self.dbtype == 'MYSQL':
            self.session.execute("USE " + self.db_name) # select new db

    def get_session(self):
        self.use()
        return self.session

    def get_engine(self):
        return self.engine

    def get_or_update(self, cls, att, val):
        if cls not in self.cache:
            self.cache[ cls ] = {}

        ccache = self.cache[ cls ]
        ckey   = (att, val)
        res    = ccache.get( ckey, None )

        if res is None:
            #print "get_or_update", att, val, 'NOT IN CACHE'
            res = self.session.query( cls ).filter(getattr(cls, att) == val).first()
            if res is None:
                #print "get_or_update", att, val, 'NOT IN CACHE', 'NOT IN DB'
                res = cls(**{att: val})
                self.session.add( res )
                self.session.commit()
                self.session.flush()
            ccache[ ckey ] = res

        else:
            #print "get_or_update", att, val, 'IN CACHE'
            pass

        return res

    def get_tables_names(self):
        return self.Base.metadata.sorted_tables


    def list_indexes(self, table_name=None):
        #http://stackoverflow.com/questions/5605019/listing-indices-using-sqlalchemy
        indexes = {}

        for name in sorted(self.insp.get_table_names()):
            if table_name is not None and table_name != name:
                continue

            if name not in indexes:
                indexes[ name ] = []

            for index in sorted(self.insp.get_indexes(name)):
                print name, index
                indexes[ name ].append( index )

        return indexes

    def drop_indexes(self, table_name=None):
        self.session.execute ('PRAGMA foreign_keys=OFF')
        self.session.commit()

        indexes = self.list_indexes(table_name=table_name)
        for tbl in indexes:
            for nfo in indexes[ tbl ]:
                self.drop_index( tbl, nfo )
        self._last_dropped_indexes = indexes
        return indexes

    def restore_indexes(self):
        self.session.execute ('PRAGMA foreign_keys = ON;')
        self.session.commit()

        indexes = self._last_dropped_indexes
        #for tbl in indexes:
        #    for nfo in indexes[ tbl ]:
        #        self.drop_index( tbl, nfo )
        self.add_indexes(indexes)

    def drop_index(self, table_name, info):
        #coords {'unique': 0, 'name': u'ix_coords_info_FQ', 'column_names': [u'info_FQ']}
        id_name    = info['name'        ]
        id_columns = info['column_names']

        print "droping index", id_name

        Index(id_name).drop( self.engine )

    def add_indexes(self, indexes, table_name=None):
        for tbl in sorted(indexes):
            if table_name is not None and table_name != tbl:
                continue

            for nfo in sorted(indexes[ tbl ]):
                self.add_index( tbl, nfo )

    def add_index(self, table_name, info ):
        id_name    = info['name'        ]
        id_columns = info['column_names']

        print "adding index", id_name

        table   = self.meta.tables[table_name]
        columns = table.columns
        colsO = []
        for coln in id_columns:
            col  = columns[ coln ]
            colsO.append( col )
        Index(id_name, *colsO).create( self.engine )


    #
    #
    #def list_indexes(self, table_name=None):
    #    #http://stackoverflow.com/questions/5605019/listing-indices-using-sqlalchemy
    #    indexes = {}
    #
    #    for name in sorted(self.insp.get_table_names()):
    #        if table_name is not None and table_name != name:
    #            continue
    #
    #        if name not in indexes:
    #            indexes[ name ] = []
    #
    #        for index in sorted(self.insp.get_indexes(name)):
    #            print name, index
    #            indexes[ name ].append( index )
    #
    #    return indexes
    #
    #def drop_indexes(self, table_name=None):
    #    indexes = self.list_indexes(table_name=table_name)
    #    for tbl in indexes:
    #        for nfo in indexes[ tbl ]:
    #            self.drop_index( tbl, nfo )
    #    self._last_dropped_indexes = indexes
    #    return indexes
    #
    #def restore_indexes(self):
    #    indexes = self._last_dropped_indexes
    #    #for tbl in indexes:
    #    #    for nfo in indexes[ tbl ]:
    #    #        self.drop_index( tbl, nfo )
    #    self.add_indexes(indexes)
    #
    #def drop_index(self, table_name, info):
    #    #coords {'unique': 0, 'name': u'ix_coords_info_FQ', 'column_names': [u'info_FQ']}
    #    id_name    = info['name'        ]
    #    id_columns = info['column_names']
    #
    #    print "droping index", id_name
    #
    #    Index(id_name).drop( self.engine )
    #
    #def add_indexes(self, indexes, table_name=None):
    #    for tbl in sorted(indexes):
    #        if table_name is not None and table_name != tbl:
    #            continue
    #
    #        for nfo in sorted(indexes[ tbl ]):
    #            self.add_index( tbl, nfo )
    #
    #def add_index(self, table_name, info ):
    #    id_name    = info['name'        ]
    #    id_columns = info['column_names']
    #
    #    print "adding index", id_name
    #
    #    table   = self.meta.tables[table_name]
    #    columns = table.columns
    #    colsO = []
    #    for coln in id_columns:
    #        col  = columns[ coln ]
    #        colsO.append( col )
    #    Index(id_name, *colsO).create( self.engine )













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
    top_level_category  = Column(String(20),                                                         ) #'A',
    species_level_taxid = Column(Integer  , ForeignKey('nodes.tax_id'),                   index=True) #1462428,
    taxid               = Column(Integer  , ForeignKey('nodes.tax_id'), primary_key=True            ) #1462428

    node                = relationship("db_nodes"  , order_by="db_nodes.tax_id", uselist=False, foreign_keys=taxid)#, primaryjoin="db_categories.taxid==db_nodes.tax_id")
    spp_node            = relationship("db_nodes"  , order_by="db_nodes.tax_id", uselist=False, foreign_keys=species_level_taxid)#, primaryjoin="db_categories.taxid==db_nodes.tax_id")

    def __repr__(self):
        return "<categories(top_level_category='%s', species_level_taxid=%d, taxid=%d)>" % (
            self.top_level_category , #'A',
            self.species_level_taxid, #1462428,
            self.taxid              , #1462428
        )
    #CATEGORIES(top_level_category='A', species_level_taxid=1462428, taxid=1462428)

class db_division(Base):
    __tablename__ = 'division'
    division_id   = Column(Integer    , ForeignKey('nodes.division_id'), primary_key=True) #0,
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
    base1         = Column(String(100)              ) #'TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG',
    base2         = Column(String(100)              ) #'TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG',
    base3         = Column(String(100)              ) #'TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG',
    ncbieaa       = Column(String(100)              ) #'FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"',
    sncbieaa      = Column(String(100)              ) #'M---------------M---------------M')

    def __repr__(self):
        return "<gc(id=%d, name='%s', name2='%s', base1='%s', base2='%s', base3='%s', ncbieaa='%s', sncbieaa='%s')>" % (
            self.id       ,
            self.name     ,
            self.name2    ,
            self.base1    ,
            self.base2    ,
            self.base3    ,
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
    genetic_code_id = Column(Integer    , primary_key=True) #1
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
    __tablename__ = 'taxid_prot'
    gi            = Column(Integer  ,                             primary_key=True            ) #1608297
    taxid         = Column(Integer  , ForeignKey('nodes.tax_id'),                   index=True) #1608297

    def __repr__(self):
        return "<db_taxid_prot(gi=%d, tax_id=%d)>" % (
            self.gi, #1608297,
            self.tax_id, #1608297,
        )

class db_citations(Base):
    __tablename__ = 'citations'
    cit_id        = Column(Integer    , primary_key=True            ) #5,
    cit_key       = Column(String(300)                              ) # 'The domestic cat: perspective on the nature and diversity of cats.',
    pubmed_id     = Column(Integer                      , index=True) # 0,
    medline_id    = Column(Integer                      , index=True) # 8603894,
    url           = Column(String(300)                              ) #'',
    text          = Column(String(300)                              ) #'',
    #taxid_list    = Column(String(300)                              ) # [9685]

    #def __init__(self, cit_id, cit_key, pubmed_id, medline_id, url, text, taxid_list):
    def __init__(self, cit_id, cit_key, pubmed_id, medline_id, url, text):
        self.cit_id     = cit_id
        self.cit_key    = cit_key
        self.pubmed_id  = pubmed_id
        self.medline_id = medline_id
        self.url        = url
        self.text       = text
        #self.taxid_list = ",".join([str(x) for x in taxid_list]) if taxid_list is not None else None

    def __repr__(self):
        return "<citations(cit_id=%d, cit_key='%s', pubmed_id=%d, medline_id=%d, url='%s', text='%s' )>" % (
            self.cit_id,
            self.cit_key,
            self.pubmed_id,
            self.medline_id,
            self.url,
            self.text,
            #self.taxid_list
        )
    #TAXDUMP_CITATIONS(cit_id=5, cit_key='The domestic cat: perspective on the nature and diversity of cats.',
    #pubmed_id=0, medline_id=8603894, url='', text='', taxid_list=[9685])

class db_citations_taxid(Base):
    __tablename__ = 'citations_taxid'
    cit_id        = Column(Integer  , ForeignKey('citations.cit_id'), primary_key=True, index=True) #1608297
    taxid         = Column(Integer  , ForeignKey('nodes.tax_id'    ), primary_key=True, index=True) #1608297

    citations     = relationship("db_citations", order_by="db_citations.cit_id", backref=backref("nodes"    ))
    nodes         = relationship("db_nodes"    , order_by="db_nodes.tax_id"    , backref=backref("citations"))

    #http://docs.sqlalchemy.org/en/rel_0_9/orm/extensions/associationproxy.html

    def __repr__(self):
        return "<merged(cit_id=%d, taxid=%d)>" % (
            self.cit_id, #1608297,
            self.taxid, #1608297,
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
    inherited_gc_flag             = Column(Boolean                                                              ) #False,
    mitochondrial_genetic_code_id = Column(Integer                                                  , index=True) #0,
    inherited_mgc_flag            = Column(Boolean                                                              ) #False,
    genbank_hidden_flag           = Column(Boolean                                                              ) #False,
    hidden_subtree_root_flag      = Column(Boolean                                                              ) #False,
    comments                      = Column(String(100)                                                          ) #''
    
    #http://docs.sqlalchemy.org/en/rel_0_9/orm/self_referential.html
    children = relationship("db_nodes",
                backref=backref('parent', remote_side=[tax_id])
            )
    
    nucleotides          = relationship("db_taxid_nuc"      , order_by="db_taxid_nuc.gi"          , backref=backref("nodes"        , uselist=False)               )
    proteins             = relationship("db_taxid_prot"     , order_by="db_taxid_prot.gi"         , backref=backref("nodes"        , uselist=False)               )
    name                 = relationship("db_names"          , order_by="db_names.unique_name"     , backref=backref("nodes"                       ), uselist=False)
    genetic_code         = relationship("db_gencode"        , order_by="db_gencode.name"          , backref=backref("nodes_genetic"               ), uselist=False, foreign_keys=genetic_code_id              , primaryjoin="db_nodes.genetic_code_id==db_gencode.genetic_code_id")
    mito_genetic_code    = relationship("db_gencode"        , order_by="db_gencode.name"          , backref=backref("nodes_mito"                  ), uselist=False, foreign_keys=mitochondrial_genetic_code_id, primaryjoin="db_nodes.mitochondrial_genetic_code_id==db_gencode.genetic_code_id")
    #gc_genetic_code      = relationship("db_gc"             , order_by="db_gc.name"               , backref=backref("nodes_genetic"               ), uselist=False, foreign_keys=genetic_code_id              , primaryjoin="db_nodes.genetic_code_id==db_gc.id")
    #gc_mito_genetic_code = relationship("db_gc"             , order_by="db_gc.name"               , backref=backref("nodes_mito"                  ), uselist=False, foreign_keys=mitochondrial_genetic_code_id, primaryjoin="db_nodes.mitochondrial_genetic_code_id==db_gc.id")
    division             = relationship("db_division"       , order_by="db_division.division_name", backref=backref("nodes"                       ), uselist=False)
    #citations            = relationship("db_citations_taxid", order_by="db_citations_taxid.cit_id", backref=backref("nodes"                       ))
    #citations            = relationship("db_citations"      , order_by="db_citations.cit_id"      , backref=backref("nodes"                       ), primaryjoin="db_nodes.tax_id==db_citations_taxid.taxid")


    #user = relationship("User", backref=backref('addresses', order_by=id))
    #addresses = relationship("Address", order_by="Address.id", backref="user")

    def __repr__(self):
        return "<names(tax_id=%d, parent_tax_id=%d, rank='%s', embl_code='%s', division_id=%d, inherited_div_flag=%s, genetic_code_id=%d, inherited_gc_flag=%s, mitochondrial_genetic_code_id=%d, inherited_mgc_flag=%s, genbank_hidden_flag=%s, hidden_subtree_root_flag=%s, comments='%s')>" % (
            self.tax_id                        ,
            self.parent_tax_id                 ,
            self.rank                          ,
            self.embl_code                     ,
            self.division_id                   ,
            str(self.inherited_div_flag)       ,
            self.genetic_code_id               ,
            str(self.inherited_gc_flag)        ,
            self.mitochondrial_genetic_code_id ,
            str(self.inherited_mgc_flag)       ,
            str(self.genbank_hidden_flag)      ,
            str(self.hidden_subtree_root_flag) ,
            self.comments                      
        )
    #TAXDUMP_NODES(tax_id=1, parent_tax_id=1, rank='no rank', embl_code='',
    #division_id=8, inherited_div_flag=False, genetic_code_id=1, inherited_gc_flag=False,
    #mitochondrial_genetic_code_id=0, inherited_mgc_flag=False, genbank_hidden_flag=False,
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

class db_delnodes(Base):
    __tablename__ = 'delnodes'
    tax_id        = Column(Integer  , primary_key=True) #1608297

    def __repr__(self):
        return "<delnodes(tax_id=%d)>" % (
            self.tax_id , #1608297,
        )
    #TAXDUMP_DELNODES(tax_id=1608297)


#ICODE(inst_id=1, inst_code='AEI', unique_name='AEI')
#CATEGORIES(top_level_category='A', species_level_taxid=1462428, taxid=1462428)
#CCODE(coll_id=7166, inst_id=362, coll_name='Herpetology Collection', coll_code='Herp', coll_size=0, collection_type='museum', coll_status=False, coll_url='', comments='', qualifier_type='specimen_voucher')
#COLL(inst_code='A', inst_type='s', inst_name='Arnold Arboretum, Harvard University')
#COWNER(inst_id=1, inst_code='AEI', aka='', inst_name='American Entomological Institute', country='USA', address='3005 SW 56th Avenue, Gainesville, Florida 32608-5047', phone='', fax='', record_source='', home_url='http://aei.tamu.edu/projects/17/public/site/aei/home', url_rule='', comments='', collection_type='museum', qualifier_type='specimen_voucher', unique_name='AEI')
#TAXDUMP_GENCODE(genetic_code_id=1, abbreviation='', name='Standard', cde='FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG', starts='---M---------------M---------------M----------------------------')
#TAXDUMP_GC(Base1='TTTTTTTTTTTTTTTTCCCCCCCCCCCCCCCCAAAAAAAAAAAAAAAAGGGGGGGGGGGGGGGG', Base2='TTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGGTTTTCCCCAAAAGGGG', Base3='TCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAGTCAG', id=1, name='Standard', name2='SGC0', ncbieaa='FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG"', sncbieaa='M---------------M---------------M')
#TAXDUMP_NODES(tax_id=1, parent_tax_id=1, rank='no rank', embl_code='', division_id=8, inherited_div_flag=False, genetic_code_id=1, inherited_gc_flag=False, mitochondrial_genetic_code_id=0, inherited_mgc_flag=False, genbank_hidden_flag=False, hidden_subtree_root_flag=False, comments='')
#TAXDUMP_MERGED(old_tax_id=12, new_tax_id=74109)
#TAXDUMP_CITATIONS(cit_id=5, cit_key='The domestic cat: perspective on the nature and diversity of cats.', pubmed_id=0, medline_id=8603894, url='', text='', taxid_list=[9685])
#TAXDUMP_DIVISION(division_id=0, division_cde='BCT', division_name='Bacteria', comments='')
#TAXDUMP_NAMES(tax_id=1, name_txt='all', unique_name='', name_class='synonym')
#TAXDUMP_DELNODES(tax_id=1608297)




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


#https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/DropEverything
#def drop_foreign_keys():
#    print "dropping foreign keys"
#    tbs     = []
#    all_fks = []
#    
#    for table_name in inspector.get_table_names():
#        print "dropping foreign keys", table_name
#        fks = []
#        for fk in inspector.get_foreign_keys(table_name):
#            print "dropping foreign keys", table_name, "name", fk
#            #if not fk['name']:
#            #    continue
#            
#            #print "dropping foreign keys", table_name, "name", fk['name']
#            
#            fks.append(
#                fk
#                #ForeignKeyConstraint((),(),name=fk['name'])
#                )
#        t = Table(table_name,metadata,*fks)
#        tbs.append(t)
#        all_fks.extend(fks)
#    
#    for fkc in all_fks:
#        session.execute(DropConstraint(fkc))
#        
#    session.commit()

#def compile_query(query):
#    dialect   = session.bind.dialect
#    statement = query.statement
#    comp      = compiler.SQLCompiler(dialect, statement)
#    comp.compile()
#    enc       = dialect.encoding
#    params    = {}
#    #for k,v in comp.params.iteritems():
#    #    if isinstance(v, unicode):
#    #        v = v.encode(enc)
#    #    params[k] = sqlescape(v)
#    return (comp.string.encode(enc) % params).decode(enc)
#    #return comp.string


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

