import json
import datetime
from flask import Flask, render_template, request, make_response, jsonify, Response
from google.cloud import datastore

# security
import os
import logging


app = Flask(__name__)

datastore_client  = datastore.Client()

# Security
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
CW_DUPCHECK_TOKEN = os.environ.get('CW_DUPCHECK_TOKEN')
CORS_ALLOW_ORIGINS = os.environ.get('CORS_ALLOW_ORIGINS').split(',')

# Creates entity with given values and stores it in google datastore 
# if results is None : insert
# if results exists : reject / upsert
def store_entity(dt, h, p, u, d, results):

    if results:
        entity = datastore.Entity(key=datastore_client.key('dupcheck', results[0].id))     

    else:
        entity = datastore.Entity(key=datastore_client.key('dupcheck'))

    entity.update({
            'Timestamp': dt,
            'Hash_Value': h,
            'Project_ID': p,
            'User_ID': u,
            'Data_ID' : d
        })

    datastore_client.put(entity)


# Receives a list of queries and creates a json object for return
def json_creater(query):

    result_array = []

    for q in query:
        query_result = {}
        query_result['Timestamp'] = str(q['Timestamp'])
        query_result['Hash_Value'] = str(q['Hash_Value'])
        query_result['Project_ID'] = str(q['Project_ID'])
        query_result['User_ID'] = str(q['User_ID'])
        query_result['Data_ID'] = str(q['Data_ID'])
        result_array.append(query_result)

    queries_result = {"results" : result_array}

    json_result = jsonify(queries_result)
    
    return json_result

def check_processor(query, dt, h, p, u, d, hash_results, mode, act):
    # Query is full query at this time

    result = json_creater(hash_results)
    
    if p:
        query.add_filter('Project_ID', '=', p)

    if act == 'store':
        query.add_filter('Hash_Value', '=', h)
        if u:
            query.add_filter('User_ID', '=', u)
    else:

        query.add_filter('Data_ID', '=', d)

    # Read in query filterd based on parameters
    results = list(query.fetch(limit=5))

    if mode !='r':

        if act == 'store' and len(results) == 0:
            store_entity(dt, h, p, u, d, None)

            return app.make_response(json_creater(results))

        if act == 'update' and len(hash_results) == 0 and len(results) != 0:
            store_entity(dt, h, p, u, d, results)

            query.add_filter('User_ID', '=', d)
            query.add_filter('Hash_Value', '=', h)
            results = list(query.fetch(limit=5))

            return app.make_response(json_creater(results))

    return app.make_response(result)
       

# Actual duplicate-check process
def hash_check(h, mode, p = None, u = None, d = None):
    # Create query variable that stores the entire query of given kind
    query = datastore_client.query(kind='dupcheck')
    
    # Filter query by hash value to check if there are any original values that have the same hash
    # and store it as a variable for returnrning results
    query.add_filter('Hash_Value', '=', h)
    hash_results = list(query.fetch(limit=5)) # If there are existing matching values, at most 5 queries are stored for return


    dt = datetime.datetime.utcnow()

    # Process of filtering the query based on which information is passed
    # There are two modes -> 'w' : check duplications and write to the datastore storage
    #                        'r' : only read from the storage to check duplications

    query = datastore_client.query(kind='dupcheck')

    if d: # Data_ID exists -> a text data
        query.add_filter('Data_ID', '=', d)
        pos_result = list(query.fetch())

        if len(pos_result) != 0:

            query = datastore_client.query(kind='dupcheck')

            return check_processor(query, dt, h, p, u, d, hash_results, mode, 'update')

    return check_processor(query, dt, h, p, u, d, hash_results, mode, 'store')    


@app.route('/v1/dup-check', methods=['GET'])
def root():
        # Variables for each column of Datastore
        h = request.args['h'] # Gives an error if hash value does not exist
        
        p = request.args.get('p') # Ignores non-existance of input values
        u = request.args.get('u')
        d = request.args.get('d')
        mode = request.args.get('mode')

        resp = Response('')

        # Referer
        referer = request.headers.get("Referer")
        domain = None
        if referer:
            domain = referer[:referer.find('/', 10)]

        if not referer or not domain in CORS_ALLOW_ORIGINS:
            logger.info('ERR_REFERRER: {}'.format(referer))
            return resp

        # Token
        if request.method == 'GET':
            cwtoken = request.headers.get("cwtoken")

            if cwtoken != CW_DUPCHECK_TOKEN:
                logger.info('ERR_TOKEN: {}'.format(cwtoken))
                return resp


        # Cross Origin
        if request.headers['Origin'] in CORS_ALLOW_ORIGINS:
            resp = hash_check(h, mode, p, u, d)

            resp.headers.add_header('Access-Control-Allow-Origin', request.headers['Origin'])

            return resp

        return resp

if __name__ == '__main__':
        # This is used when running locally only. When deploying to Google App
        # Engine, a webserver process such as Gunicorn will serve the app. This
        # can be configured by adding an `entrypoint` to app.yaml.
        app.run(host='127.0.0.1', port=8080, debug=True)


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500