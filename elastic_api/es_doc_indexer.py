from elasticsearch import Elasticsearch
from elasticsearch import helpers
import json


class ESDocIndexer:
    """
    This class contains methods for uploading documents into ElasticSearch
    """
    CONFIG_ES_ADDRESS = "es_address"
    CONFIG_ES_INDEX = "es_index"
    CONFIG_ES_MAPPING = "es_mapping_name_prefix"

    def __init__(self, config=None):
        if config is None:
            config = {}
        self.config = config

        es_address = self.config.get(self.CONFIG_ES_ADDRESS) or "localhost:9200"
        self.mapping_name = self.config.get(self.CONFIG_ES_MAPPING) or 'comments-navalny'

        self.index_name = self.config.get(self.CONFIG_ES_INDEX) or "comments-navalny"

        self.es = Elasticsearch([es_address], timeout=10)

    def create_index(self):
        """
        This methods creates index and mapping for vacancies
        :return:
        """
        index_body = {
            'mappings': {
                self.mapping_name: {
                    # "numeric_detection": True,
                    'properties': {
                        'internal_user_id': {'type': 'keyword'},
                        'user_name': {'type': 'text'},
                        'comment': {"type": 'text', 'analyzer': "russian"},
                        'reply_to': {'type': 'keyword'},
                        'timestamp': {"type": "date"},
                        'source_type': {'type': 'keyword'},
                        'source': {'type': 'keyword'},
                        'likes': {'type': 'integer'}
                    }
                }
            }
        }
        return self.es.indices.create(
            index=self.index_name,
            body=index_body
        )

    def search_query(self, query):
        return self.es.search(
            index=self.index_name,
            doc_type=self.mapping_name,
            body=query
        )

    @classmethod
    def get_hits(cls, result):
        return result['hits']['hits']

    def search_by_fields(self, fields):
        """
        Searches by value of fields

        :param fields: Example
        {
            "comment": "Putin is a thief",
            "source_type": "twitter"
        }
        :return:
        """
        query = {
            "query": {
                "match": fields
            }
        }
        return self.search_query(query)

    def insert_document(self, record):
        return self.es.index(index=self.index_name, doc_type=self.mapping_name, body=record)

    def check_index_exists(self):
        return self.es.indices.exists(index=self.index_name)

    def delete_index(self):
        return self.es.indices.delete(index=self.index_name)

    def update_record(self, record_id, data):
        """
        Updates record in elastic with new data

        :param record_id: Internal elastic id. Example: `AV3Wl3IholiUnc4TtcYA`
        :param data:
        {
            "some_new_estimation": 42
        }
        :return:
        """
        self.es.update(
            index=self.index_name,
            doc_type=self.mapping_name,
            id=record_id,
            body={
                "doc": data
            }
        )

    def bulk_upload(self, docs):
        """
        Uploads pack of document into ES
        :param docs: list of documents represented as dicts
        :return:
        """
        actions = [
            {
                "_index": self.index_name,
                "_type": self.mapping_name,
                "_source": doc
            }
            for doc in docs
        ]

        helpers.bulk(self.es, actions, timeout="1000s")

        return self.es.count(index=self.index_name)
