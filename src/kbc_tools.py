# coding=utf-8
# Python 3

import csv
import itertools
import json
import sys

import requests

MAX_REQ_SIZE = 100 * 1024
CONNECT_TIMEOUT = 10.01
READ_TIMEOUT = 128

def slice_stream(iterator, size):
    while True:
        chunk = tuple(itertools.islice(iterator, size))
        if not chunk:
            return
        else:
            yield chunk

def read_csv(input_file):
    safe_input = (line.replace('\0', '') for line in input_file)
    reader = csv.DictReader(safe_input, dialect='kbc')
    while True:
        try:
            yield next(reader)
        except csv.Error as e:
            print('CSV read error: {e}'.format(e=e), file=sys.stderr)

def csv_writer(output_file, *, fields):
    writer = csv.DictWriter(output_file, fieldnames=fields, dialect='kbc')
    writer.writeheader()
    return writer

def make_batch_request(batch, req_obj, *, url, user_key, doc_id_key='id', docs_key='documents'):
    size = sum(len(doc[key]) for doc in batch for key in doc)
    if size > MAX_REQ_SIZE:
        if len(batch) == 1:
            print('document "{id}" is too large'.format(id=batch[0][doc_id_key]), file=sys.stderr)
            return []

        half = len(batch) // 2
        return itertools.chain(
            make_batch_request(batch[:half], req_obj, url=url, user_key=user_key, doc_id_key=doc_id_key, docs_key=docs_key),
            make_batch_request(batch[half:], req_obj, url=url, user_key=user_key, doc_id_key=doc_id_key, docs_key=docs_key)
        )

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'user_key ' + user_key
    }
    req = {}
    req.update(req_obj)
    req[docs_key] = list(batch)

    res = json_post(url, headers, req)
    if len(res) == 0:
        ids = ','.join(doc[doc_id_key] for doc in batch)
        print('failed to process documents [{ids}]'.format(ids=ids), file=sys.stdout)

    return res

def json_post(url, headers, data):
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
        if response.status_code >= 400:
            try:
                err = response.json()
                print('HTTP error {code}, {e}: {msg}'.format(
                    code=response.status_code, e=err['exception'], msg=err['message']
                ), file=sys.stderr)
            except ValueError:
                err = response.text
                print('HTTP error {code}\n{e}'.format(code=response.status_code, e=err), file=sys.stderr)

            return []
    except requests.RequestException as e:
        print('HTTP request exception\n{type}: {e}'.format(type=type(e).__name__, e=e), file=sys.stderr)
        return []

    return response.json()
