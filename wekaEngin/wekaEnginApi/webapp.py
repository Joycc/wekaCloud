#!flask/bin/python
import os, time, shutil, threading
from flask_restful import Resource, Api, reqparse
from flask import jsonify as _
from flask import request, redirect, send_from_directory
from bson.objectid import ObjectId
from mongodb.mongoBase import close_db

import sys
sys.path.append('..')
from wekacommon import fileExt as _f
from wekacommon.response import Response as _r
from mongodb.mongoFile import MongoFile as _m

class CreateApp(Resource):
    '''
    {   classify_id:
        cluster_id:
        created:
        apk:
    }

    '''
    def __init__(self):
        model_parser = reqparse.RequestParser()
        model_parser.add_argument('model_id', type = str)
        model_parser.add_argument('cluster_id', type = str)
        self.args = model_parser.parse_args()
        self.mongo = _m()

    @close_db()
    def post(self):
        app_maker = BuildApp()

        created = time.time()
        appid = ''

        if self.args['cluster_id']:
            model = self.mongo.cluster.find_one(dict(_id=ObjectId(self.args['cluster_id'])))
            if model.has_key('appid'):
                self.mongo.addCluster(self.args['cluster_id'], created = created)
                appid = model['appid']
            else:
                objective_field_name = model['objective_field_name']
                appid = self.mongo.webapp.insert(dict(cluster_id = self.args['cluster_id'],
                                                         created = created,
                                                         objective_field_name = objective_field_name,
                                                         name = model['name'] + '&#39;app'))
                self.mongo.addCluster(self.args['cluster_id'], appid = str(appid))

        elif self.args['model_id']:
            model = self.mongo.model.find_one(dict(_id=ObjectId(self.args['model_id'])))
            if model.has_key('appid'):
                self.mongo.insertTree(self.args['model_id'], created = created)
                appid = model['appid']
            else:
                objective_field_name = model['objective_field_name']
                appid = self.mongo.webapp.insert(dict(classify_id = self.args['model_id'],
                                                         created = created,
                                                         objective_field_name = objective_field_name,
                                                         name = model['name'] + '&#39;app'))
                self.mongo.insertTree(self.args['model_id'], appid = str(appid))

        sc = _f.ServerConfig()
        server_url = sc.server.server_ip
        app_url = sc.app.app_server
        appurl = 'http://%s/app/question.html?app_id=%s&ip=%s'\
                    %(app_url, appid, server_url)
        self.mongo.add_apk(appid, path = app_maker.add_app(appid, appurl))
        return {'url':'/dashboard/apps'}, 201

class GetAppdata(Resource):

    @close_db()
    def get(self, _id):
        mongo = _m()
        dbApp = mongo.webapp.find_one(dict(_id=ObjectId(_id)))
        response = {}

        if dbApp.has_key('classify_id'):
            dbmodel = mongo.model.find_one(dict(_id=ObjectId(dbApp['classify_id'])))
            response['tree'] = dbmodel['tree']


        elif dbApp.has_key('cluster_id'):
            dbmodel = mongo.cluster.find_one(dict(_id=ObjectId(dbApp['cluster_id'])))
            response['cluster'] = dbmodel['cluster']

        response['appname'] = dbApp['name']
        response['attributes'] = []
        attr = mongo.dataset.find_one(dict(_id=ObjectId(dbmodel['datasetid'])))['attr']
        for i in attr:
           response['attributes'].append({'name':i[1], 'type':i[3]})

        return _(response)

class GetApp(Resource):

    @close_db()
    def post(self):
        mongo= _m()
        res = _r()
        appdb = mongo.webapp.find()
        return res.get_apps(appdb)

class DownloadApp(Resource):

    def __init__(self):
        parser = reqparse.RequestParser()
        parser.add_argument('app_id', type = str)
        self.args = parser.parse_args()

    def get(self, app_name):
        return send_from_directory(_f.APP_FOLDER, app_name)

class BuildApp(object):
    __se = None

    def __new__(cls):
        if cls.__se is None:
            global thread_lock
            thread_lock = threading.Lock()
            cls.__se = super(BuildApp, cls).__new__(cls)
        return cls.__se

    def __init__(self):
        self.appid = None

    def add_app(self, appid, appurl):
        self.appid = str(appid)
        DO_BUILD = 'a%s=Thread_build(appurl, self.appid, thread_lock);\
                   a%s.start()'%(self.appid, self.appid)
        exec(DO_BUILD)

class Thread_build(threading.Thread):

    def __init__(self, appurl, appid, thread_lock):
        super(Thread_build, self).__init__()
        self.appurl = appurl
        self.appid = appid
        self.tl = thread_lock

    @close_db()
    def run(self):
        self.tl.acquire()

        mongo = _m()
        scf = _f.ServerConfig()

        #make_path = scf.app.apk_build_dir
        #change_url = os.path.join(make_path, 'urlhttp.sh ')
        #os.system('sh %s "%s"' %(change_url, self.appurl))
        #cmdline = 'ant -f ' + make_path + '/build.xml -S clean debug > /tmp/heheda'
        #os.system(cmdline)

        #source = os.path.join(make_path, 'bin/wekaapp-debug.apk')
        #dest = os.path.join(_f.APP_FOLDER, self.appid+'.apk')
        #shutil.copyfile(source, dest)
        #mongo.add_apk(self.appid, path = dest)
        mongo.add_apk(self.appid)
        self.tl.release()


class DelApp(Resource):

    @close_db()
    def get(self, _id):
        mongo = _m()
        mongo.webapp.remove({'_id':ObjectId(_id)})
        return {'success': True}


