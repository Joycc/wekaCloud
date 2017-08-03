#THIS IS A DOC FOR THE RESTFUL-API OF THE WEKA ENGINE
version = v0.1

## Model operation API

###1.get weka 
    >url = 
    json=
    {
        algorithm = [string, required]
        file = [string, required]
    }

###2.get weka tree
    >url = $hostname:$port/run/api/$version/gettree/[classfier]
    json=
    {
        algorithm = [string, required]
        file = [string, required]
    }

## File operation API

###1.create source
    >url = /dashboard/create_source

###2.create dataset
    >url = $hostname:$port/file/api/$version/delete/[filename]

**DELETE SAMPLE FILE IS NOT ALLOWED**

###3.upload file
    >url= $hostname:$port/file/api/$version/upload/[filename]
    json= {file = [file]}

###1.get file text
    >url = $hostname:$port/file/api/$version/getfiles/list
