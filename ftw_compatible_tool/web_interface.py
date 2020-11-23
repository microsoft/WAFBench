import os
import time
import subprocess
import json
import shutil

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import sqlite3


app = Flask(__name__)
app.config['UPLOAD_PATH'] = '/tmp'


@app.route('/', methods=['GET'])
def execute():
    ''' Entrypoint for HTTP call

        Expect a HTTP GET request with multipart form contains two parameters: hostname and file.
        hostname is a string url of server to test and file is a YAML file

        Return an array of response object in JSON form
        Example:
            [
                {
                    "status": [403],
                    "title": "913100-1"
                },
                {
                    "status": [403],
                    "title": "913100-2"
                }
            ]
    '''
    hostname = request.values.get("hostname")
    result_name = 'result.db'

    if not hostname or not result_name:
        return 'Must include hostname', 400

    # handle uploaded YAML file
    yaml_path = os.path.join(app.config['UPLOAD_PATH'], str(time.time()))
    if not os.path.exists(yaml_path):
        os.makedirs(yaml_path)
    files = request.files.getlist('file')
    for file in files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(yaml_path, filename))

    # redirect db store path to yaml_path
    result_name = os.path.join(yaml_path, result_name)

    # compose request
    arguments = ['ftw_compatible_tool',
                 '-d', result_name,
                 '-x',
                 'load {} | gen | start {} | report | exit'.format(yaml_path, hostname)]

    # Use threading here is necessary because parameter 'exit'
    # in ftw-compatible will call sys.exit()
    p = subprocess.Popen(arguments)
    p.wait()

    if not os.path.exists(result_name):
        shutil.rmtree(yaml_path)
        return 'Failed to retrieve result files', 500

    # preparing json return
    json_result = []
    conn = sqlite3.connect(result_name)
    c = conn.cursor()
    c.execute('SELECT test_title, output FROM Traffic')
    for row in c:
        test_title, output = row
        # this is necessary because output col in db use
        # single quotation mark, which is not a valid json format
        output = output.replace("\'", "\"")
        payload = json.loads(output)
        payload['title'] = test_title
        json_result.append(payload)

    # clean up
    conn.close()
    shutil.rmtree(yaml_path)

    return jsonify(json_result)


if __name__ == "__main__":
    app.run()
