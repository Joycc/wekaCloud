#!flask/bin/python
from flask import Flask
from flask_restful import Api, Resource
from wekaEnginApi import runcmd, uploader, webapp
from wekacommon import fileExt as _f

import ConfigParser
import os

DEFAULT_IP = '0.0.0.0'
DEFAULT_PORT = 5000

def load_app(api, version):
    #api.add_resource(runcmd.runCmd, '/run/api/%s/<action>/<cmd>' %version)
    #api.add_resource(uploader.upLoader, '/file/api/%s/<action>/<filename>' %version)
    api.add_resource(uploader.CreateSource, '/dashboard/create_source')
    api.add_resource(uploader.CreateDataset, '/dashboard/create_dataset')
    api.add_resource(uploader.GetSource, '/dashboard/get_sources')
    api.add_resource(uploader.Detail, '/dashboard/json/source/<_id>')
    api.add_resource(uploader.Dataset, '/dashboard/get_datasets')
    api.add_resource(uploader.GetDataset, '/dashboard/json/dataset/<_id>')


    api.add_resource(uploader.DelSource, '/dashboard/delete_source/<_id>')
    api.add_resource(runcmd.DelDataset, '/dashboard/delete_dataset/<_id>')
    api.add_resource(runcmd.DelModel, '/dashboard/delete_model/<_id>')
    api.add_resource(runcmd.DelCluster, '/dashboard/delete_cluster/<_id>')
    api.add_resource(webapp.DelApp, '/dashboard/delete_app/<_id>')

    api.add_resource(runcmd.Models, '/dashboard/get_models')
    api.add_resource(runcmd.Clusters, '/dashboard/get_clusters')

    api.add_resource(runcmd.GetTree, '/dashboard/json/model/<_id>')
    api.add_resource(runcmd.GetCluster, '/dashboard/json/cluster/<_id>')

    api.add_resource(runcmd.CreateTree, '/dashboard/create_model')
    api.add_resource(runcmd.CreateCluster, '/dashboard/create_cluster')

    api.add_resource(runcmd.Prediction, '/dashboard/create_batchprediction/info')
    api.add_resource(runcmd.DoPrediction, '/dashboard/create_batchprediction/prediction')
    #api.add_resource(uploader.upLoader, '/dashboard/get_sources')

    api.add_resource(uploader.CreateBatch, '/dashboard/create_remote_source')
    #####################app#####################
    api.add_resource(webapp.CreateApp , '/dashboard/apps/create_app')
    api.add_resource(webapp.GetAppdata , '/dashboard/apps/get_appdata/<_id>')
    api.add_resource(webapp.GetApp, '/dashboard/get_apps')
    api.add_resource(webapp.DownloadApp, '/dashboard/apps/download_app/<app_name>')
    api.add_resource(runcmd.AppDoPredict, '/dashboard/apps/predict/<_id>')

if __name__ == '__main__':
    ###############load server config###############
    cf = ConfigParser.ConfigParser()
    cf.read(_f.SERVER_CONFIG)
    debug = cf.get('server', 'debug')
    server_ip = cf.get('server', 'server_ip') or DEFAULT_IP
    server_port = cf.get('server', 'server_port') or DEFAULT_PORT
    version = cf.get('server', 'version')

    ###############load server config###############

    if not os.path.exists(_f.UPLOAD_FOLDER):
        os.makedirs(_f.UPLOAD_FOLDER)
    if not os.path.exists(_f.TEMP_FOLDER):
        os.makedirs(_f.TEMP_FOLDER)
    app = Flask(__name__)
    api = Api(app)
    load_app(api, version)

    ###############js cross-border##################
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE')
        return response
    ###############js cross-border##################

    app.run(debug = debug, host = server_ip, port = int(server_port))
