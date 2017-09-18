# coding=utf-8
# Python 3

import itertools
import json
import os
import sys

import requests

from concurrent.futures import ThreadPoolExecutor

from keboola import docker

from kbc_tools import read_csv, csv_writer, slice_stream, make_batch_request, parallel_map

BASE_URL = 'https://api.geneea.com/keboola/v2/analysis'
BETA_URL = 'https://beta-api.geneea.com/keboola/v2/analysis'
DOC_BATCH_SIZE = 12
THREAD_COUNT = 1

ANALYSIS_TYPES = frozenset(['sentiment', 'entities', 'tags', 'relations'])

OUT_TAB_DOC = 'analysis-result-documents.csv'
OUT_TAB_ENT = 'analysis-result-entities.csv'
OUT_TAB_REL = 'analysis-result-relations.csv'

class Params:

    def __init__(self, config):
        self.config = config

        self.customer_id = os.getenv('KBC_PROJECTID')

        self.user_key = self.get_user_key()
        self.source_tab_path = self.get_source_tab_path()
        self.analysis_types = self.get_analysis_types()

        params = config.get_parameters()
        self.id_cols = params.get('columns', {}).get('id', [])
        self.text_cols = params.get('columns', {}).get('text', [])
        self.title_cols = params.get('columns', {}).get('title', [])
        self.lead_cols = params.get('columns', {}).get('lead', [])
        self.language = params.get('language')
        self.domain = params.get('domain')
        self.correction = params.get('correction')
        self.diacritization = params.get('diacritization')
        self.use_beta = params.get('use_beta', False)

        advanced_params = self.get_advanced_params()
        self.doc_batch_size = int(advanced_params.get('doc_batch_size', DOC_BATCH_SIZE))
        self.thread_count = int(advanced_params.get('thread_count', THREAD_COUNT))
        self.reference_date = advanced_params.get('reference_date')

        self.validate()

    def get_user_key(self):
        if 'user_key' in self.config.get_parameters():
            return self.config.get_parameters()['user_key']
        if 'image_parameters' in self.config.config_data and '#user_key' in self.config.config_data['image_parameters']:
            return self.config.config_data['image_parameters']['#user_key']
        else:
            return None

    def get_source_tab_path(self):
        in_tabs = self.config.get_input_tables()
        return in_tabs[0]['full_path'] if len(in_tabs) == 1 else None

    def get_analysis_types(self):
        types = self.config.get_parameters().get('analysis_types', [])
        return set(t.strip().lower() for t in types if isinstance(t, str))

    def get_advanced_params(self):
        advanced_params = self.config.get_parameters().get('advanced', {})
        return advanced_params if isinstance(advanced_params, dict) else {}

    def validate(self):
        if self.customer_id is None:
            raise ValueError('the "KBC_PROJECTID" environment variable needs to be set')
        if self.user_key is None:
            raise ValueError('the "user_key" parameter has to be provided')
        if self.source_tab_path is None:
            raise ValueError('exactly one INPUT table mapping needs to be specified')
        if not self.id_cols or not self.text_cols:
            raise ValueError('the "columns.id" and "columns.text" are required parameters')
        if self.analysis_types and len(self.analysis_types - ANALYSIS_TYPES) > 0:
            raise ValueError('invalid "analysisTypes" parameter, allowed values are {types}'.format(types=ANALYSIS_TYPES))
        for cols in (self.id_cols, self.text_cols, self.title_cols, self.lead_cols):
            if not isinstance(cols, list):
                raise ValueError('invalid "column" parameter, all values need to be an array of column names')
        for id_col in self.id_cols:
            if id_col in ('language', 'sentimentValue', 'sentimentPolarity', 'sentimentLabel', 'type', 'text', 'score', 'name', 'negated', 'subject', 'object', 'subjectType', 'objectType', 'usedChars'):
                raise ValueError('invalid "column.id" parameter, value "{col}" is a reserved name'.format(col=id_col))
        if self.thread_count > 32:
            raise ValueError('the "thread_count" parameter can not be greater than 32')

    def get_output_path(self, filename):
        return os.path.normpath(os.path.join(
                self.config.get_data_dir(), 'out', 'tables', filename
        ))

    def get_usage_path(self):
        return os.path.normpath(os.path.join(
                self.config.get_data_dir(), 'out', 'usage.json'
        ))

    @staticmethod
    def init(data_dir=''):
        return Params(docker.Config(data_dir))

class AnalysisApp:

    def __init__(self, *, data_dir=''):
        self.params = Params.init(data_dir)
        self.validate_input()

    def validate_input(self):
        with open(self.params.source_tab_path, 'r', encoding='utf-8') as in_tab:
            try:
                row = next(read_csv(in_tab))
            except StopIteration:
                print('WARN: could not read any data from the source table')
                sys.stdout.flush()
                return
            all_cols = self.params.id_cols + self.params.text_cols + self.params.title_cols + self.params.lead_cols
            for col in all_cols:
                if col not in row:
                    raise ValueError('the source table does not contain column "{col}"'.format(col=col))

    def run(self):
        print('starting NLP analysis with features {types}'.format(types=self.params.analysis_types))
        sys.stdout.flush()
        doc_count = 0
        used_chars = 0

        out_tab_doc_path = self.params.get_output_path(OUT_TAB_DOC)
        out_tab_ent_path = self.params.get_output_path(OUT_TAB_ENT)
        out_tab_rel_path = self.params.get_output_path(OUT_TAB_REL)
        with open(self.params.source_tab_path, 'r', encoding='utf-8') as in_tab, \
             open(out_tab_doc_path, 'w', encoding='utf-8') as out_tab_doc, \
             open(out_tab_ent_path, 'w', encoding='utf-8') as out_tab_ent, \
             open(out_tab_rel_path, 'w', encoding='utf-8') as out_tab_rel:
            doc_writer = csv_writer(out_tab_doc, fields=self.get_doc_tab_fields())
            ent_writer = csv_writer(out_tab_ent, fields=self.get_ent_tab_fields())
            rel_writer = csv_writer(out_tab_rel, fields=self.get_rel_tab_fields())

            for doc_analysis in self.analyze(read_csv(in_tab)):
                doc_writer.writerows(self.analysis_to_doc_result(doc_analysis))
                ent_writer.writerows(self.analysis_to_ent_result(doc_analysis))
                rel_writer.writerows(self.analysis_to_rel_result(doc_analysis))

                doc_count += 1
                used_chars += int(doc_analysis['usedChars'])
                if doc_count % 1000 == 0:
                    self.write_usage(doc_count=doc_count, used_chars=used_chars)
                    print('successfully analyzed {n} documents with {ch} characters'.format(n=doc_count, ch=used_chars))
                    sys.stdout.flush()

        self.write_usage(doc_count=doc_count, used_chars=used_chars)
        self.write_manifest(doc_tab_path=out_tab_doc_path, ent_tab_path=out_tab_ent_path, rel_tab_path=out_tab_rel_path)

        if self.params.analysis_types and not {'entities', 'tags'} & self.params.analysis_types:
            os.unlink(out_tab_ent_path)
            os.unlink(out_tab_ent_path + '.manifest')
        if self.params.analysis_types and not 'relations' in self.params.analysis_types:
            os.unlink(out_tab_rel_path)
            os.unlink(out_tab_rel_path + '.manifest')

        print('the analysis has finished successfully, {n} documents with {ch} characters were analyzed'.format(n=doc_count, ch=used_chars))
        sys.stdout.flush()

    def analyze(self, row_stream):
        url = BASE_URL if not self.params.use_beta else BETA_URL
        user_key = self.params.user_key
        req = self.get_request()

        batch_stream = self.doc_batch_stream(row_stream)

        with requests.Session() as session:
            with ThreadPoolExecutor(max_workers=self.params.thread_count) as executor:
                for batch_analysis in parallel_map(
                    executor, make_batch_request,
                    batch_stream, itertools.repeat(req), url=url, user_key=user_key,
                    session=session
                ):
                    yield from batch_analysis

    def get_request(self):
        req = {
            'customerId': self.params.customer_id
        }
        if self.params.analysis_types:
            req['analysisTypes'] = list(self.params.analysis_types)
        if self.params.language:
            req['language'] = self.params.language
        if self.params.domain:
            req['domain'] = self.params.domain
        if self.params.correction:
            req['correction'] = self.params.correction
        if self.params.diacritization:
            req['diacritization'] = self.params.diacritization
        if self.params.reference_date:
            req['referenceDate'] = self.params.reference_date
        return req

    def doc_batch_stream(self, row_stream):
        for rows in slice_stream(row_stream, self.params.doc_batch_size):
            yield list(map(self.row_to_doc, rows))

    def row_to_doc(self, row):
        def join_cols(columns):
            return '\n\n'.join(row[col] for col in columns if row[col])

        doc = {
            'id': json.dumps(list(row[id_col] for id_col in self.params.id_cols)),
            'text': join_cols(self.params.text_cols)
        }
        if self.params.title_cols:
            doc['title'] = join_cols(self.params.title_cols)
        if self.params.lead_cols:
            doc['lead'] = join_cols(self.params.lead_cols)
        return doc

    def analysis_to_doc_result(self, doc_analysis):
        doc_ids_vals = zip(self.params.id_cols, json.loads(doc_analysis['id']))
        doc_res = {
            'language': doc_analysis['language'],
            'usedChars': doc_analysis['usedChars']
        }
        for id_col, val in doc_ids_vals:
            doc_res[id_col] = val
        if 'sentiment' in doc_analysis:
            doc_res['sentimentValue'] = doc_analysis['sentiment']['value']
            doc_res['sentimentPolarity'] = doc_analysis['sentiment']['polarity']
            doc_res['sentimentLabel'] = doc_analysis['sentiment']['label']
        yield doc_res

    def analysis_to_ent_result(self, doc_analysis):
        if 'entities' in doc_analysis:
            doc_ids_vals = list(zip(self.params.id_cols, json.loads(doc_analysis['id'])))
            for ent in doc_analysis['entities']:
                ent_res = {
                    'type': ent['type'],
                    'text': ent['text'],
                    'score': ent['score']
                }
                for id_col, val in doc_ids_vals:
                    ent_res[id_col] = val
                yield ent_res

    def analysis_to_rel_result(self, doc_analysis):
        if 'relations' in doc_analysis:
            doc_ids_vals = list(zip(self.params.id_cols, json.loads(doc_analysis['id'])))
            for rel in doc_analysis['relations']:
                rel_res = {
                    'type': rel['type'],
                    'name': rel['name'],
                    'negated': rel['negated'],
                    'subject': rel.get('subjectName'),
                    'subjectType': rel.get('subjectType'),
                    'object': rel.get('objectName'),
                    'objectType': rel.get('objectType')
                }
                for id_col, val in doc_ids_vals:
                    rel_res[id_col] = val
                yield rel_res

    def get_doc_tab_fields(self):
        fields = self.params.id_cols + ['language']
        if not self.params.analysis_types or 'sentiment' in self.params.analysis_types:
            fields += ['sentimentValue', 'sentimentPolarity', 'sentimentLabel']
        fields += ['usedChars']
        return fields

    def get_ent_tab_fields(self):
        return self.params.id_cols + ['type', 'text', 'score']

    def get_rel_tab_fields(self):
        return self.params.id_cols + ['type', 'name', 'negated', 'subject', 'object', 'subjectType', 'objectType']

    def write_manifest(self, *, doc_tab_path, ent_tab_path, rel_tab_path):
        with open(doc_tab_path + '.manifest', 'w', encoding='utf-8') as manifest_file:
            json.dump({
                'primary_key': self.params.id_cols,
                'incremental': True
            }, manifest_file, indent=4)
        with open(ent_tab_path + '.manifest', 'w', encoding='utf-8') as manifest_file:
            json.dump({
                'primary_key': self.params.id_cols + ['type', 'text'],
                'incremental': True
            }, manifest_file, indent=4)
        with open(rel_tab_path + '.manifest', 'w', encoding='utf-8') as manifest_file:
            json.dump({
                'primary_key': self.params.id_cols + ['type', 'name', 'negated', 'subject', 'object'],
                'incremental': True
            }, manifest_file, indent=4)

    def write_usage(self, *, doc_count, used_chars):
        usage_path = self.params.get_usage_path()
        with open(usage_path, 'w', encoding='utf-8') as usage_file:
            json.dump([
                {'metric': 'documents', 'value': doc_count},
                {'metric': 'characters', 'value': used_chars},
                {'metric': 'processing_threads', 'value': self.params.thread_count}
            ], usage_file, indent=4)
