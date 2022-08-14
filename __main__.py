import flask
import os
import sys
from flask import Flask, request, send_file
from flask_cors import CORS
import json
from redis_connection import Redis

redis = Redis()

# Relative path setup
cur_path = os.path.abspath(".")
sys.path.append(cur_path)

# Setup paths to the metadata and images directories
META_IMGS_PATH = os.path.abspath("./metadata")
IMGS_PATH = os.path.abspath("./images")

# Specify the URL of the React frontned
FRONTEND_URL = "http://localhost:3000"


app = Flask(__name__)
CORS(app, supports_credentials=True)


# Response Header Wrapper function, setting appropriate header permissions
def add_response_headers(response):
    response.headers.add('Access-Control-Allow-Origin', FRONTEND_URL)
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Headers',
                         'Content-Type,Authorization,Cache-Control')
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,DELETE,OPTIONS')
    return response


# Sample function for testing access to the backend
# To verify if the backend is running, go to http://localhost:6789/hello and see if it returns the below message
@app.route('/hello')
def say_hello_world():
    return flask.jsonify({'result': "Hello Connected React World!!!"})


# Load the image metadata information
@app.route('/api/load_img_data', methods=['GET'])
def load_img_data():
    try:
        if redis.peek('IMAGE_DATA'):
            img_data = redis.read('IMAGE_DATA')
            response = flask.jsonify(
                json.loads(img_data.decode('utf-8')))

        else:
            # Retrieve all metadata filenames
            meta_files = os.listdir(META_IMGS_PATH)

            # Load the metadata information into a dictionary of (image_id) --> (image metadata)
            data = {}
            for meta_file in meta_files:
                if meta_file.endswith(".json"):
                    meta_fpath = os.path.join(META_IMGS_PATH, meta_file)
                    with open(meta_fpath, 'r') as meta_file:
                        meta_data = json.load(meta_file)
                        data[meta_data["id"]] = meta_data

            # Retrieve all the group names in the data
            group_names = list(set([metadata['group']
                                    for metadata in data.values()]))
            # In this example, we expect exactly two group names: terminator and human
            assert set(group_names) == {'terminator', 'human'}

            # Send the data, together with the group names
            response_data = {'imgData': data, 'groupNames': group_names}
            response = flask.jsonify(response_data)
            redis.write('IMAGE_DATA', json.dumps(response_data))
    except Exception as e:
        response = flask.make_response(
            "Dataset screen display unsuccessful...", 403)

    response = add_response_headers(response)

    return response

# receive modified image metadata and write to redis


@app.route('/api/modify_img_data', methods=['POST'])
def modify_img_metadata():
    values = request.get_json()
    redis.write('IMAGE_DATA', json.dumps(values))
    img_data = redis.read('IMAGE_DATA')
    response = flask.jsonify(
        json.loads(img_data.decode('utf-8')))
    return response


# Load a specific image
@app.route('/api/images/<img_id>', methods=['GET'])
def get_image(img_id):

    # Load the metadata information of the image
    meta_path = os.path.join(META_IMGS_PATH, img_id+".json")
    with open(meta_path, 'r') as meta_file:
        meta_data = json.load(meta_file)

    # Send the appropriate file
    fpath = os.path.join(IMGS_PATH, meta_data["filepath"])
    if not os.path.isfile(fpath) or not os.path.exists(fpath):
        raise ValueError(f"No file found: {fpath}")

    return send_file(fpath)


# Check if the groupings have been grouped correctly
@app.route('/api/check_grouping', methods=['POST'])
def check_grouping():
    # NOTE: we realise that "hacking" this function (i.e. making it return 'success == true' all the time) is trivial.
    # This function is simply a sanity check.
    try:
        # Retrieve the image metadata groupings
        values = request.get_json()
        imgsMetadata = values["imgMetadata"]
        img_ids = imgsMetadata.keys()

        # Define the expected image groupings
        correct_h = {'11', '12', '13', '14', '15', '16',
                     '111', '112', '113', '114', '115', '116'}
        correct_t = {'0', '1', '2', '3', '4', '5',
                     '100', '101', '102', '103', '104', '105'}

        # Retrieve the sent groupings
        sent_h = set()
        sent_t = set()
        for img_id in img_ids:
            if imgsMetadata[img_id]['group'] == 'human':
                sent_h.add(img_id)
            elif imgsMetadata[img_id]['group'] == 'terminator':
                sent_t.add(img_id)

        # Check if they are equal
        success = ((sent_h == correct_h) and (correct_t == sent_t))

        response = flask.jsonify({"success": success})
    except Exception as e:
        print(f"Failed with message: {str(e)}")
        response = flask.make_response(
            "Dataset screen display unsuccessful...", 403)

    response = add_response_headers(response)

    return response


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=6789)
