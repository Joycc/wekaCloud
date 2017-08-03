#!flask/bin/python
import time
import fileExt as _f
import sys, ConfigParser
sys.path.append('..')
from mongodb import mongoBase as _m
from mongodb.mongoBase  import close_db

class Response(object):
    def __init__(self):
        cf = ConfigParser.ConfigParser()
        cf.read(_f.SERVER_CONFIG)
        self.host = cf.get('server', 'server_ip') or '0.0.0.0'

    def make_source(self, source = {}):
        now = time.time()
        source_res = []
        for value in source:
            created = value['created']
            dataset_list = value['resources']
            source_body = dict(
                source_id = str(value['_id']),
                file_type = 'arff',
                age = '%dd %dh' %((now - created)/(60*60*24), (now - created)/(60*60)%24),
                size = value['size'],
                number_dataset = len(dataset_list),
                name = value['name']
            )

            source_res.append(source_body)

        return source_res

    def create_source(self):
        return {"success": True}

    def make_detail(self, _id, source, data):

        name = source['name']
        created = source['created']
        arff = data['arff']
        total = len(arff)
        limit = 25
        query_total = total > limit and limit or total
        count = query_total

        detail_res = []
        fields_preview = {}
        fields = {}
        for fid, i in arff.iteritems():
            fname = i['field'][0]
            type = i['field'][1]
            initValue = ((type == 'NUMERIC' or type =='REAL')\
                         and 'numeric' or 'categorical')

            detail_res.append({'name':fname,
                               'type':initValue,
                               'list':i['data']})

        return {'name': name, 'list':detail_res}

    def create_dataset(self, _id):
        return {"url": "/dashboard/dataset/%s" %_id,
                "code": 201}

    def create_tree(self, _id):
        return {"url": "/dashboard/model/%s" %_id,
                "code": 201}

    def create_cluster(self, _id):
        return {"url": "/dashboard/cluster/%s" %_id,
                "code": 201}

    def make_dataset(self, sources):
        dataset_res = []
        for source in sources:
            try:
                _id = source['_id']
                created = source['created']
                now = time.time()
                age = '%dd %dh' %((now - created)/(60*60*24), (now - created)/(60*60)%24)
                dataset_res.append(dict(
                        source_id= str(source['sid']),
                        dataset_id= str(_id),
                        name= source['name'],
                        created= created,
                        number_cluster= len(source['clusters']),
                        age = age,
                        number_model= len(source['models']),
                        size= source['size']
                        ))
            except:
                print '[ERROR DATA] source _id = %s' %_id
                continue

        return dataset_res

    def make_models(self, models):
        model_res = []
        now = time.time()
        for model in models:
            try:
                created = model['created']
                user = model.has_key('uid') and model('uid') or ''
                model_res.append(
                        {
                        "model_id": str(model['_id']),
                        "age":'%dd %dh' %((now - created)/(60*60*24), (now - created)/(60*60)%24),
                        "number_prediction": len(model['number_of_predictions']),
                        "name":model['name'],
                        "dataset_id": str(model['datasetid']),
                        "size":model['size'],
                        "objective": model['objective_field_name'],
                        "user":user
                        }
                )
            except:
                continue

        return model_res

    def get_dataset(self, dataset):
        attr = dataset['attr']
        dataset_res = []
        for i in attr:
            try:
                type = (i[3]== 'NUMERIC' or i[3]=='REAL')\
                         and 'numeric' or 'categorical'
                dataset_res.append({
                    'name':i[1],
                    'type':type,
                    'count':0,
                    'missing':0,
                    'errors':0
                })
            except:
                continue
                print '[ERROR DATA] in data set . id = %s' %i[_id]

        return {'name': dataset['name'], 'list':dataset_res}

    def make_modelinfo(self, model):
        return {"name":model["name"]}

    def get_clusters(self, model):
        cluster_res = []
        now = time.time()
        for i in model:
            _id = str(i['_id'])
            try:
                created = i['created']
                cluster_res.append({
                            "name": i["name"],
                            "algorithm":'k_means',
                            "created": i['created'],
                            "number_centroids":len(i['number_of_predictions']),
                            "k": i['k'],
                            "size": i['size'],
                            "age": '%dd %dh' %((now - created)/(60*60*24), (now - created)/(60*60)%24),
                            "dataset_id":i['datasetid'],
                            "cluster_id":_id
                            })
            except :
                print 'error data!%s' %i['_id']
                continue

        return cluster_res

    def get_apps(self, appdb):

        app_res = []
        count=0
        now = time.time()
        for i in appdb:
            size = (i.has_key('path') and not i['path'] is None)and 'done'  or 'building...'
            try:
                created = i['created']
                atype = i.has_key('cluster_id') and 'cluster' or 'classify'
                modelid = i.has_key('cluster_id') and i['cluster_id'] or i['classify_id']
                count += 1
                app_res.append({
                                "dataset":'',
                                "objective":i['objective_field_name'],
                                "type": atype,
                                "size": size,
                                "app_id": str(i['_id']),
                                "created": created,
                                "age": '%dd %dh' %((now - created)/(60*60*24), (now - created)/(60*60)%24),
                                "name": i['name'],
                                "path": i['path']
                                })
            except:
                continue

        return app_res

