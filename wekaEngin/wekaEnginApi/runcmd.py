#!flask/bin/python
import os, time
from flask_restful import Resource, reqparse
from flask import jsonify as _
from bson.objectid import ObjectId

import sys
sys.path.append('..')
from wekacommon import fileExt as _f
from wekacommon.response import Response as _r
from mongodb.mongoFile import MongoFile as _m
from mongodb.mongoBase import close_db

class runCmd(object):
    def __init__(self, args):
        self.result = 'Request Error'
        self.args = args


    def simple_run_cmd(self, cmd):
        weka_text = os.popen(cmd).read()
        #return _({'weka_text':weka_text})
        return weka_text

    def make_cmd_line(self, cmdtype = _f.cmdtype.CLASSIFY, cmdAdd = ''):
        exist, path = _f.isSameFileName(self.args['file'])
        fileLinker = '-t'
        if cmdtype ==  _f.cmdtype.CLASSIFY:
            pass
        elif cmdtype ==  _f.cmdtype.FILTER:
           fileLinker = '-i'
        elif cmdtype ==  _f.cmdtype.CLUSTER:
            pass

        if self.args['algorithm'] and exist:
            mlpath = os.path.join(_f.MODELS_FOLDER, self.args['mid']+'.ml')
            return 'java ' + self.args['algorithm'] + ' ' + fileLinker +' ' +\
                    self.args['path'] + cmdAdd + ' -d ' + mlpath
        else:
            return

    def gettree(self):
        cmdline = self.make_cmd_line(cmdAdd = ' -x ')
        dataTree = self.simple_run_cmd(cmdline+' -g')
        dataTree = dataTree.replace('shape=box', '')
        dataTree = dataTree.replace('style=filled', '')
        #self.result = _({'weka_text':dataTree})
        return dataTree

    def getcluster(self, k):
        cmdline = self.make_cmd_line(cmdAdd = ' -N %s' %k)
        return self.simple_run_cmd(cmdline)

    def getresult(self):
        cmdline = self.make_cmd_line()
        self.result = _({'weka_text':self.simple_run_cmd(cmdline)})

    def getfilter(self):
        dateTime = str(time.time())
        fileName = self.args['file'] + '.' + dateTime + '.' + self.args['file'].split('.')[-1]
        filePath = os.path.join(_f.TEMP_FOLDER, fileName)
        cmdline = self.make_cmd_line(_f.cmdtype.FILTER, ' >' + filePath)
        self.simple_run_cmd(cmdline)
        self.result = _({'filter_file': fileName})

    def prediction(self):
        cmd = 'java ' + self.args['algorithm'] + ' -p ' + self.args['field'] + ' -l '\
              + self.args['modelPath'] + ' -T ' + self.args['sourcePath']
        return self.simple_run_cmd(cmd)

class CreateTree(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()
        parser.add_argument('algorithm', type=str, required=True, help=\
                'you must choose a algorithm')
        parser.add_argument('dataset_id', type=str, required=True, help=\
                'you must give a dataset id')
        parser.add_argument('model_id', type=str)
        self.args = parser.parse_args()

    @close_db()
    def post(self):
        mongo = _m()
        res = _r()
        _id = self.args['dataset_id']
        mid = ''
        if self.args['model_id']:
            mid = self.args['model_id']
        else:
            mid = mongo.insertModel(_id)

        dataset = mongo.dataset.find_one(dict(_id = ObjectId(_id)))
        filePath = dataset['path']
        #TODO get it from mongoDB
        objective_field_name =\
        dataset.has_key('objective_field_name') and\
        dataset['objective_field_name'] or\
        _f.loadArff(filePath, False)['attributes'][-1][0]

        self.args['file'] = os.path.basename(filePath)
        self.args['path'] = filePath
        self.args['mid'] = mid

        self.run = runCmd(self.args)
        dataTree = self.run.gettree()

        mlpath = os.path.join(_f.MODELS_FOLDER, self.args['mid']+'.ml')
        mongo.insertTree(mid, tree=dataTree,
                            model = mlpath,
                            size = os.path.getsize(mlpath),
                            number_of_evaluations = [],
                            number_of_predictions = [],
                            number_of_batchpredictions = [],
                            name = dataset['name'] + '\'s model',
                            objective_field_name = objective_field_name,
                        )
        return res.create_tree(mid)

class GetTree(Resource):

    @close_db()
    def get(self, _id):
        mongo = _m()
        model = mongo.model.find_one(dict(_id = ObjectId(_id)))
        dataTree = model['tree']
        name = model['name']
        log = ''
        return _({'file':dataTree, 'name':name, 'log': log})

class Models(Resource):

    @close_db()
    def post(self):
        mongo = _m()
        models = mongo.model.find()
        res = _r()
        return res.make_models(models)

class Prediction(Resource):
    def __init__(self):
        post_parser = reqparse.RequestParser()
        post_parser.add_argument('model_id', type=str)
        post_parser.add_argument('cluster_id', type=str)
        self.args = post_parser.parse_args()


    @close_db()
    def get(self):
        mid = self.args['model_id']
        cid = self.args['cluster_id']
        mongo = _m()
        res = _r()
        if mid:
            model = mongo.model.find_one(dict(_id = ObjectId(mid)))
        elif cid:
            model = mongo.cluster.find_one(dict(_id = ObjectId(cid)))
        return res.make_modelinfo(model)

class AppDoPredict(Resource):
    def __init__(self):
        post_parser = reqparse.RequestParser()
        post_parser.add_argument('data', type=str)
        self.args = post_parser.parse_args()

    def post(self, _id):
        mongo = _m()
        model = None
        predict_obj = {}

        webapp = mongo.webapp.find_one(dict(_id=ObjectId(_id)))
        if webapp.has_key('classify_id'):
            model = mongo.model.find_one(dict(_id=ObjectId(webapp['classify_id'])))
        elif webapp.has_key('cluster_id'):
            model = mongo.cluster.find_one(dict(_id=ObjectId(webapp['cluster_id'])))

        if not model:
            return {'message':'db error!'}, 404


        dataset = mongo.dataset.find_one(dict(_id=ObjectId(model['datasetid'])))
        attr_list = []
        for attr in dataset['attr']:
            attr_list.append((attr[1], attr[3]))
            if model['objective_field_name'] == attr[1]:
                predict_obj['field'] = str(int(attr[0]) + 1)

        sourcePath = os.path.join(_f.TEMP_FOLDER, str(time.time())+'.arff')
        predict_obj['algorithm'] = model.has_key('algorithm') and\
                                    model['algorithm'] or 'weka.classifiers.trees.J48'
        predict_obj['modelPath'] = model['model']
        _f.makeArff(sourcePath, attr_list, [self.args['data']])
        predict_obj['sourcePath'] = sourcePath

        run = runCmd(predict_obj)
        result = run.prediction()
        if not result == '':
            result = filter(None, filter(None, result.split('\n'))[-1].split(' '))
            if len(result)  ==  3:
                prediction = result[1]
                confidence = '100%'

            elif len(result) == 4:
                prediction = result[2].split(':')[-1]
                confidence = str((float(result[-1]) * 100)) + u'%'
            else:
                return {'message':' result error'}, 500
            return {'prediction': prediction, 'confidence': confidence}
        else:
            return {'message':'internal error!'}, 500

class DoPrediction(Resource):
    def __init__(self):
        post_parser = reqparse.RequestParser()
        post_parser.add_argument('field', type=str)
        post_parser.add_argument('algorithm', type=str)
        post_parser.add_argument('model_id', type=str)
        post_parser.add_argument('resource_id', type=str)
        post_parser.add_argument('cluster_id', type=str)
        self.args = post_parser.parse_args()

    def get(self):
        add_title = ''
        mongo = _m()
        model = None
        if self.args['model_id']:
            model = mongo.model.find_one(dict(_id=ObjectId(self.args['model_id'])))
        elif self.args['cluster_id']:
            model = mongo.cluster.find_one(dict(_id=ObjectId(self.args['cluster_id'])))
            add_title = 'instace cluster actual\n'

        if not model:
            return 'cannot find the model!'

        self.args['field'] = str(int(mongo.dataset.find_one(dict(_id=ObjectId\
                            (model['datasetid'])))['attr'][int(self.args['field'])][0]) + 1)
        self.args['modelPath'] = model['model']
        self.args['sourcePath']\
            = mongo.source.find_one(dict(jsid = self.args['resource_id']))['path']
        run = runCmd(self.args)
        result = run.prediction()
        if not result == '':
            return {"result":add_title + result}
        else:
            return {"result":\
                    'Test file cannot be predicted, but we help you to save it'
                    }

class CreateCluster(Resource):
    def __init__(self):
        parser = reqparse.RequestParser()
        parser.add_argument('algorithm', type=str, required=True, help=\
                'you must choose a algorithm')
        parser.add_argument('dataset_id', type=str, required=True, help=\
                'you must give a dataset id')
        parser.add_argument('k', type=str, help=\
                'you must give a k')
        parser.add_argument('cluster_id', type=str)
        self.args = parser.parse_args()

    @close_db()
    def post(self):
        mongo = _m()
        res = _r()
        _id = self.args['dataset_id']
        mid = mongo.insertCluster(_id)
        dataset = mongo.dataset.find_one(dict(_id = ObjectId(_id)))
        filePath = dataset['path']
        #TODO get it from mongoDB
        objective_field_name =\
        dataset.has_key('objective_field_name') and\
        dataset['objective_field_name'] or\
        _f.loadArff(filePath, False)['attributes'][-1][0]

        self.args['file'] = os.path.basename(filePath)
        self.args['path'] = filePath
        self.args['mid'] = mid

        self.run = runCmd(self.args)
        dataCluster = self.run.getcluster(self.args['k'] or '3')

        mlpath = os.path.join(_f.MODELS_FOLDER, self.args['mid']+'.ml')
        mongo.addCluster(mid, cluster=dataCluster,
                            model = mlpath,
                            size = os.path.getsize(mlpath),
                            number_of_evaluations = [],
                            number_of_predictions = [],
                            number_of_batchpredictions = [],
                            name = dataset['name'] + '\'s cluster',
                            objective_field_name = objective_field_name,
                            k = self.args['k'] or '3',
                            algorithm = self.args['algorithm']
                        )
        return res.create_cluster(mid)

class Clusters(Resource):

    @close_db()
    def post(self):
        mongo = _m()
        models = mongo.cluster.find()
        res = _r()
        return res.get_clusters(models)

class GetCluster(Resource):

    def __init__(self):
        parser = reqparse.RequestParser()
        parser.add_argument('k', type=str, help='you must give a k')
        self.args = parser.parse_args()


    @close_db()
    def get(self, _id):
        mongo = _m()
        res = _r()
        model = mongo.cluster.find_one(dict(_id = ObjectId(_id)))

        if not self.args['k'] == 'undefined':
            did = model['datasetid']
            mid = _id
            dataset = mongo.dataset.find_one(dict(_id = ObjectId(did)))
            filePath = dataset['path']
            #TODO get it from mongoDB
            objective_field_name = _f.loadArff(filePath, False)['attributes'][-1][0]

            self.args['algorithm'] = model['algorithm']
            self.args['file'] = os.path.basename(filePath)
            self.args['path'] = filePath
            self.args['mid'] = mid

            self.run = runCmd(self.args)
            dataCluster = self.run.getcluster(self.args['k'] or '3')

            mlpath = os.path.join(_f.MODELS_FOLDER, self.args['mid']+'.ml')

            mongo.addCluster(mid, cluster=dataCluster,
                                model = mlpath,
                                size = os.path.getsize(mlpath),
                                name = dataset['name'] + '\'s cluster',
                                objective_field_name = objective_field_name,
                                k = self.args['k'] or '3',
                            )
            model = mongo.cluster.find_one(dict(_id = ObjectId(_id)))


        dataCluster = model['cluster']
        name = model['name']
        dataset = mongo.dataset.find_one(dict(_id = ObjectId(model['datasetid'])))
        return _({'file':dataCluster,
                  'cluster':name,
                  #'source_id':dataset['sid']
                  })

class DelDataset(Resource):
    @close_db()
    def get(self, _id):
        mongo = _m()
        mongo.dataset.remove({'_id':ObjectId(_id)})
        return {'success': True}

class DelModel(Resource):
    @close_db()
    def get(self, _id):
        mongo = _m()
        mongo.model.remove({'_id':ObjectId(_id)})
        return {'success': True}

class DelCluster(Resource):
    @close_db()
    def get(self, _id):
        mongo = _m()
        mongo.cluster.remove({'_id':ObjectId(_id)})
        return {'success': True}


