#!flask/bin/python
import os, werkzeug, subprocess
from flask_restful import Resource, Api, reqparse
from flask import jsonify as _
from flask import request, redirect, url_for
from bson.objectid import ObjectId

import sys
sys.path.append('..')
from wekacommon import fileExt as _f
from wekacommon.response import Response as _r
from mongodb.mongoFile import MongoFile as _m
from mongodb.mongoBase import close_db

class CreateSource(Resource):
    def __init__(self):
        post_parser = reqparse.RequestParser()
        post_parser.add_argument('file',\
                type=werkzeug.datastructures.FileStorage, location='files')
        post_parser.add_argument('fileFileName', type=str)
        post_parser.add_argument('resource_id', type=str)
        self.args = post_parser.parse_args()

    @close_db()
    def post(self):
        jsid = None
        if self.args['resource_id']:
            jsid = self.args['resource_id']
        upfile = self.args['file']
        fileName = upfile.filename
        isSame, path = _f.isSameFileName(fileName)
        res = _r()
        if _f.allowed_file(fileName) and upfile:
            fileName = werkzeug.secure_filename(fileName)
            if isSame:
                fileName = _f.rename(fileName)
            filePath = os.path.join(_f.UPLOAD_FOLDER, fileName)
            upfile.save(filePath)
            mongo = _m()
            mongo.insert_source(filePath, jsid)
            #return _({'file': fileName})
            return res.create_source(), 201
        else:
            return{'success':False}

class CreateBatch(Resource):
    def __init__(self):
        post_parser = reqparse.RequestParser()
        post_parser.add_argument('name', type=str)
        post_parser.add_argument('database_name', type=str)
        post_parser.add_argument('collection_name', type=str)
        post_parser.add_argument('field_name', type=str)
        post_parser.add_argument('source_url', type=str)
        self.args = post_parser.parse_args()

    @close_db()
    def post(self):
        mongo = _m()
        database = self.args['database_name']
        collection = self.args['collection_name']
        field = self.args['field_name']
        name = self.args['name']
        for i in mongo.batch.find():
            if i['name'] == name:
                return 'not allowed name', 502

        mongo.batch.insert(dict(name=name,
                                dbname = collection,
                                field=field,
                                database = database,
                                db_host=self.args['source_url'],
                                modelid = '',
                                datasetid = ''))
        mongo.insertResource('',add_data=False, source_name=collection)

        return {'message':'ok', 'code':'201'}, 200

class GetSource(Resource):
    @close_db()
    def post(self):
        mongo = _m()
        res = _r()
        return res.make_source(mongo.source.find())

class DelSource(Resource):

    @close_db()
    def get(self, _id):
        mongo = _m()
        mongo.source.remove({'_id':ObjectId(_id)})
        return {'success': True}

class Detail(Resource):
    @close_db()
    def get(self, _id):
        print _id
        mongo = _m()
        res = _r()
        source = mongo.source.find_one(dict(_id = ObjectId(_id)))
        data = mongo.data.find_one(dict(_id = ObjectId(_id)))
        return res.make_detail(_id, source, data)

class CreateDataset(Resource):
    def __init__(self):
        post_parser = reqparse.RequestParser()
        post_parser.add_argument('source_id', type=str)
        self.args = post_parser.parse_args()

    @close_db()
    def post(self):
        mongo = _m()
        res = _r()
        _id = self.args['source_id']
        source = mongo.source.find_one(dict(_id = ObjectId(_id)))
        dataId = mongo.insertDataset(source)
        #mongo.insertDatasetData(dataId)
        return res.create_dataset(dataId)

class Dataset(Resource):
    @close_db()
    def post(self):
        mongo = _m()
        res = _r()
        dataset = mongo.dataset.find()
        return res.make_dataset(dataset)

class GetDataset(Resource):
    @close_db()
    def get(self, _id):
        mongo = _m()
        res = _r()
        dataset = mongo.dataset.find_one(dict(_id = ObjectId(_id)))
        return res.get_dataset(dataset)
