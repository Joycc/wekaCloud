#!flask/bin/python

import mongoBase
from bson.objectid import ObjectId
import sys, time, os
sys.path.append('..')
from wekacommon import fileExt as _f

class MongoFile(object):
    def __init__(self):
        mongo = mongoBase.Mongo()
        self.source = mongo.resource
        self.data = mongo.data
        self.dataset = mongo.dataset
        self.model = mongo.model
        self.cluster = mongo.cluster
        self.webapp = mongo.webapp
        self.batch = mongo.batch

    def insert_source(self, fpath, jsid='', add_data=True, source_name=''):
        #par:
        #fpath for upload fle path
        #jsid: It's come frome the client . in the page
        #prediction , the client cannot get a response from the server
        #so , this id one for communitcate.

        created = time.time()
        if os.path.exists(fpath) and add_data:
            name = os.path.basename(fpath)
            size = os.path.getsize(fpath)
            resources = []

            _id = self.source.insert(dict(name = name,
                                          created = created,
                                          size = size,
                                          resources = resources,
                                          path = fpath,
                                          jsid = jsid))

            data = self._parseArff(_f.loadArff(fpath))

            data['_id'] = _id
            self.data.insert(data)

        elif not add_data:
            size = 'database data'
            name = source_name
            resources = []
            self.source.insert(dict(name = name,
                                    created = created,
                                    size = size,
                                    resources = resources,
                                    path = fpath,
                                    jsid = jsid))


    def _add_array(self, collection, condition, key, value):
        try:
            collection.update(condition, {'$addToSet':{key: value}}, upsert = True)
        except:
            print 'add to array error!'

    def insertDataset(self, source):
        sourceId = source['_id']
        del source['_id']
        del source['resources']
        source['sid'] = sourceId
        source['clusters'] = []
        source['created'] = time.time()
        source['models'] = []
        source['ensembles'] = []
        source['anomalies'] = []
        source['name'] = source['name'] + '\'s dataset'
        source['attr'] = self._countArff(_f.loadArff(source['path']))
        _id = self.dataset.insert(source)

        _id = str(_id)
        _f.copy_file(source['path'], _f.DATASETS_FOLDER, _id+'.arff')
        newPath = os.path.join(_f.DATASETS_FOLDER, _id+'.arff')
        self.dataset.update({'_id':ObjectId(_id)}, {'$set':{'path':newPath}})
        self._add_array(self.source, {'_id':ObjectId(sourceId)}, 'resources', _id)
        return _id


    def _parseArff(self, arff):
        # return like this:
           #"000001" : {
           #    "field" : [
           #    "sepalwidth",
           #    "REAL"
           #    ],
           #    "data" : [
           #       3.5,
           #       3,
           #       3.2,
           #       3.3,
           #       3.4
           #        ]
           #    }
        field = {}
        count = 0
        for i in arff['attributes']:
            j = 0
            data = []
            while j < 25 and j < len(arff['data']):
                data.append(arff['data'][j][count])
                j += 1
            field['%06d' %count] = {'field':i, 'data':data}
            count += 1
        return dict(arff = field)

    def _countArff(self, arff):
        # return like this
        #"attr" : [
        #             [
        #             "000000",
        #             "sepallength",
        #             "numeric",
        #             "REAL",
        #             150(instance)
        #             ],


        field = []
        count = 0
        dataLen = len(arff['data'])
        for i in arff['attributes']:
            field.append(('%06d' %count, i[0],
                    (i[1] == 'NUMERIC'or i[1] == 'REAL') and 'numeric' or 'categorical',
                    i[1], dataLen))
            count += 1
        return field


    def insertModel(self,  _id):
        mid = str(self.model.insert(dict(datasetid=_id,
                                         created = time.time(),
                                        )))
        self._add_array(self.dataset, {'_id':ObjectId(_id)}, 'models', mid)
        return mid

    def insertTree(self,  _id, **arg):
        # actually , this for add the tree into model
        self.model.update({'_id':ObjectId(_id)}, {'$set':arg})

    def insertCluster(self, _id):
        mid = str(self.cluster.insert(dict(datasetid=_id,
                                         created = time.time(),
                                        )))
        self._add_array(self.dataset, {'_id':ObjectId(_id)}, 'models', mid)
        return mid

    def addCluster(self,  _id, **arg):
        self.cluster.update({'_id':ObjectId(_id)}, {'$set':arg})

    def add_apk(self, _id, **arg):
        self.webapp.update({'_id':ObjectId(_id)}, {'$set':arg})
