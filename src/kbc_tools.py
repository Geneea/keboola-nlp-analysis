# coding=utf-8
# Python 3

import base64
import bz2
import csv
import itertools
import json
import pickle
import sys

from collections import deque

import requests

MAX_REQ_SIZE = 100 * 1024
CONNECT_TIMEOUT = 10.01
READ_TIMEOUT = 128

csv.field_size_limit(1024 * MAX_REQ_SIZE)


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
            print(
                'could not properly read some row(s) for the input data',
                'CSV read error, {type}: {e}'.format(type=type(e).__name__, e=e),
                sep='\n', file=sys.stderr
            )
            sys.stderr.flush()


def csv_writer(output_file, *, fields):
    writer = csv.DictWriter(output_file, fieldnames=fields, dialect='kbc')
    writer.writeheader()
    return writer


def make_batch_request(batch, req_obj, *, url, user_key, doc_id_key='id', docs_key='documents', session=None):
    size = sum(len(doc[key]) for doc in batch for key in doc)
    if size > MAX_REQ_SIZE:
        if len(batch) == 1:
            print(
                'skipping too large document with ID={id}'.format(id=batch[0][doc_id_key]),
                'the maximum allowed size is {max} bytes'.format(max=MAX_REQ_SIZE),
                sep='\n', file=sys.stderr
            )
            sys.stderr.flush()
            return []

        half = len(batch) // 2
        return itertools.chain(
            make_batch_request(batch[:half], req_obj, url=url,
                user_key=user_key, doc_id_key=doc_id_key, docs_key=docs_key, session=session),
            make_batch_request(batch[half:], req_obj, url=url,
                user_key=user_key, doc_id_key=doc_id_key, docs_key=docs_key, session=session)
        )

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'user_key ' + user_key
    }
    req = {}
    req.update(req_obj)
    req[docs_key] = list(batch)

    res = json_post(url, headers, req, session=session)
    if len(res) == 0:
        ids = ' '.join(doc[doc_id_key] for doc in batch)
        print('failed to process documents: {ids}'.format(ids=ids), file=sys.stdout)
        print('if the problems persist, please contact our support at support@geneea.com', file=sys.stderr)
        sys.stderr.flush()

    return res


def json_post(url, headers, data, session=None):
    post = session.post if session else requests.post
    try:
        response = post(url, headers=headers, data=json.dumps(data), timeout=(CONNECT_TIMEOUT, READ_TIMEOUT))
        code = response.status_code
        if code >= 400:
            try:
                err = response.json()
                print(
                    'Internal error while communicating with the analysis API.',
                    'HTTP error {code}, {e}: {msg}'.format(code=code, e=err['exception'], msg=err['message']),
                    sep='\n', file=sys.stderr
                )
            except ValueError:
                print(
                    'Internal error while communicating with the analysis API.',
                    'HTTP error {code}'.format(code=code),
                    '{body}'.format(body=response.text),
                    sep='\n', file=sys.stderr
                )

            return []
    except requests.RequestException as e:
        print(
            'Internal error while communicating with the analysis API.',
            'HTTP request exception, {type}: {e}'.format(type=type(e).__name__, e=e),
            sep='\n', file=sys.stderr
        )
        return []

    return response.json()


def parallel_map(pool, fn, *iterables, **kwargs):
    argStream = zip(*iterables)
    buffer = deque([pool.submit(fn, *args, **kwargs) for args in list(itertools.islice(argStream, 2 * pool._max_workers))])
    def result_iterator():
        try:
            while buffer:
                future = buffer.popleft()
                yield future.result()
                try:
                    args = next(argStream)
                    buffer.append(pool.submit(fn, *args, **kwargs))
                except StopIteration:
                    pass
        finally:
            for future in buffer:
                future.cancel()
    return result_iterator()


def serialize_data(obj, compress=True):
    bin_data = pickle.dumps(obj)
    if compress:
        bin_data = bz2.compress(bin_data)
    return base64.encodebytes(bin_data).decode('ascii')


def deserialize_data(ser_value, decompress=True):
    bin_data = base64.decodebytes(ser_value.encode('ascii'))
    if decompress:
        bin_data = bz2.decompress(bin_data)
    return pickle.loads(bin_data)
