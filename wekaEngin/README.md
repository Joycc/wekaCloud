#THIS IS WEKA ENGIN SERVER

##How to publish it

###in unbuntu
1.download the virtualenv at <https://pypi.python.org/pypi/virtualenv>
    >cd virtualenv
    >python setup.py install
2.git clone ssh://user@devcloud.bj.intel.com:29418/mpf/wekacloud.git
3.run these command:
    >cd wekacloud/wekaEngin
    >virtualenv flask
    >flask/bin/pip install flask
    >flask/bin/pip install flask-restful
    >flask/bin/pip install pymongo
    >flask/bin/pip install liac-arff
    >chmod a+x weka-server.py
4.change the configuration in the weka-server.conf
5.sudo apt-get install mongodb
6.download the jre and set the env in bashrc
7.download weka:
    >wget http://prdownloads.sourceforge.net/weka/weka-3-6-13.zip
  unzip it and set the env like this:
    >export CLASSPATH=.:$WEKAROOT/weka.jar
    >export WEKAROOT=$wekapath(where you unzip it)
8.Then you can run this cmd and enjoy the service!
    >source flask/bin/activate
    >./weka-server.py

###in other system
todo
