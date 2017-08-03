#!flask/bin/python
import os, shutil
import arff, ConfigParser

ALLOWED_EXTENSIONS = set(['arff', 'txt'])
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'upload')
WEKA_FOLDER = os.path.join(os.getenv('WEKAROOT'), 'data')
TEMP_FOLDER = os.path.join(os.getcwd(), 'temp')
SERVER_CONFIG = os.path.join(os.getcwd(), 'wekaServer.conf')
DATASETS_FOLDER = os.path.join(os.getcwd(), 'datasets')
MODELS_FOLDER = os.path.join(os.getcwd(), 'models')
APP_FOLDER = os.path.join(os.getcwd(), 'app')
DOBATCH = os.path.join(os.getcwd(), 'dobatch.py')

def allowed_file(fileName):
    return '.' in fileName and \
        fileName.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

#TODO
def getFileList():
    fileList = {UPLOAD_FOLDER:os.listdir(UPLOAD_FOLDER),\
                DATASETS_FOLDER:os.listdir(DATASETS_FOLDER) }
    return fileList

def isSameFileName(fileName):
    fileList = getFileList() 
    for i in fileList:
        if fileName in fileList[i]:
            return (True, i) 
    return (False, '')

def rename(fileName):
    fileName = os.path.splitext(fileName)[0] + '.new' +\
               os.path.splitext(fileName)[1]

    isSame, path = isSameFileName(fileName)
    if isSame:
        fileName = rename(fileName)

    return fileName

def copy_file(filePath, toPath, fileName):
    toFile = os.path.join(toPath, fileName)
    shutil.copyfile(filePath, toFile)

def loadArff(fileName, include_data=True):
    return arff.load(open(fileName, 'rb'))

def makeArff(fileName, attributes, data):
    # { 'attributes':
    #       [('outlook',['sunny', 'overcast']),
    #        ('humudity', 'real')]
    #   'data':[
    #           ['sunny', 2],
    #           ['overcast', 3]
    #           ]
    #}
    # js devloper is a big hole , belive it or not, he sent a string to me ,not a list
    data = eval(data[0])
    udata = []
    for i in data:
        if not type(i) == int:
            i = unicode(i, 'utf-8')
        udata.append(i)

    less = 0
    for less in xrange(len(attributes) - len(udata)):
        udata.append(u'?')

    arffobj = {u'attributes':attributes, u'data':[udata], u'relation': fileName, u'description': u''}
    '''
    arffobj =   {  u'attributes': [
                    (u'outlook', [u'sunny', u'overcast', u'rainy']),
                    (u'temperature', u'REAL'),
                    (u'humidity', u'REAL'),
                    (u'windy', [u'TRUE', u'FALSE']),
                    (u'play', [u'yes', u'no'])],
                    u'data': [ [u'sunny', 85.0, 85.0, u'FALSE', u'no']],
                    u'relation': u'weather',
                    u'description': u'' }
    '''
    with open(fileName, 'w') as fp:
        fp.write(arff.dumps(arffobj))

def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        if cls not in instances:
            instanecs[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton

class cmdtype():
    CLASSIFY    = 0
    FILTER      = 1 
    CLUSTER     = 2

class ServerConfig(object):
    def __init__(self, config= SERVER_CONFIG):
        cf = ConfigParser.ConfigParser()
        cf.read(config)
        self.config = cf

    def __getattr__(self, attr):
        return Wrap(attr, self.config)

class Wrap(object):
    def __init__(self, attr, cf):
        self.config = cf
        self.attr = attr

    def __getattr__(self, attr):
        return self.config.get(self.attr, attr)
