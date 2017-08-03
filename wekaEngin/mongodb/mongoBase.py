#!flask/bin/python

from functools import wraps
from pymongo.database import Database
try:
    from pymongo import MongoClient
except ImportError:
    import warnings
    warnings.warn("Strongly recommend upgrading to the latest version pymongo version,Connection is DEPRECATED: Please use mongo_client instead.")
    from pymongo import Connection as MongoClient

import sys, ConfigParser
sys.path.append('..')
from wekacommon import fileExt as _f

class Mongo(object):

    def __init__(self, host='localhost', port=27017, database='test', max_pool_size=10, timeout=10, use_host = False):
        cf = ConfigParser.ConfigParser()
        cf.read(_f.SERVER_CONFIG)
        self.host = cf.get('db', 'db_ip') or host

        self.port = int(cf.get('db', 'db_port')) or port

        self.max_pool_size = max_pool_size
        self.timeout = timeout
        self.database = cf.get('db', 'db_base') or database
        if use_host:
            self.host = host
            self.database = database

    @property
    def connect(self):
        return MongoClient(self.host, self.port, maxPoolSize=self.max_pool_size, connectTimeoutMS=60 * 60 * self.timeout)

    def __getitem__(self, collection):
        return self.__getattr__(collection)

    def __getattr__(self, collection_or_func):
        db = self.connect[self.database]
        if collection_or_func in Database.__dict__:
            return getattr(db, collection_or_func)
        return Collection(db, collection_or_func)


class Collection(object):

    def __init__(self, db, collection):
        self.collection = getattr(db, collection)

    def __getattr__(self, operation):
            # some controlers, if not, raise it
            control_type = ['disconnect', 'insert', 'update', 'find', 'find_one', 'remove']
            if operation in control_type:
                return getattr(self.collection, operation)
            raise AttributeError(operation)


def close_db(dbs=['db']):
    '''
    Usage::
    >>>s_db = Mongo()
    >>>@close_db(['s_db'])
    ...: def test():
        ...:     print s_db.test.insert({'a': 1, 'b': 2})
        ...:
    '''
    def _deco(func):
        @wraps(func)
        def _call(*args, **kwargs):
            result = func(*args, **kwargs)
            for db in dbs:
                try:
                    func.func_globals[db].connect.close
                except KeyError:
                    pass
            return result
        return _call
    return _deco
