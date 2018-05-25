search_project_response = """
{
    "took": 17,
    "timed_out": false,
    "_shards": {
        "total": 5,
        "successful": 5,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": 1,
        "max_score": 1.8232156,
        "hits": [
            {
                "_index": "readthedocs",
                "_type": "project",
                "_id": "6",
                "_score": 1.8232156,
                "_source": {
                    "name": "Pip",
                    "description": "",
                    "lang": "en",
                    "url": "/projects/pip/",
                    "slug": "pip"
                },
                "highlight": {
                    "name": [
                        "<em>Pip</em>"
                    ]
                }
            }
        ]
    },
    "aggregations": {
        "language": {
            "doc_count_error_upper_bound": 0,
            "sum_other_doc_count": 0,
            "buckets": [
                {
                    "key": "en",
                    "doc_count": 1
                }
            ]
        }
    }
}
"""

search_file_response = """
{
    "took": 27,
    "timed_out": false,
    "_shards": {
        "total": 5,
        "successful": 5,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": 3,
        "max_score": 6.989019,
        "hits": [
            {
                "_index": "readthedocs",
                "_type": "page",
                "_id": "AWKuy4jp-H7vMtbTbHP5",
                "_score": 6.989019,
                "_routing": "prova",
                "_source": {
                    "path": "_docs/cap2",
                    "project": "prova",
                    "title": "Capitolo 2",
                    "version": "latest"
                },
                "highlight": {
                    "headers": [
                        "<em>Capitolo</em> 2"
                    ],
                    "title": [
                        "<em>Capitolo</em> 2"
                    ],
                    "content": [
                        "<em>Capitolo</em> 2  In questo <em>capitolo</em>, vengono trattate"
                    ]
                }
            },
            {
                "_index": "readthedocs",
                "_type": "page",
                "_id": "AWKuy4jp-H7vMtbTbHP4",
                "_score": 6.973402,
                "_routing": "prova",
                "_source": {
                    "path": "_docs/cap1",
                    "project": "prova",
                    "title": "Capitolo 1",
                    "version": "latest"
                },
                "highlight": {
                    "headers": [
                        "<em>Capitolo</em> 1"
                    ],
                    "title": [
                        "<em>Capitolo</em> 1"
                    ],
                    "content": [
                        "<em>Capitolo</em> 1  In questo <em>capitolo</em>, le funzioni principali"
                    ]
                }
            },
            {
                "_index": "readthedocs",
                "_type": "page",
                "_id": "AWKuy4jp-H7vMtbTbHP3",
                "_score": 0.2017303,
                "_routing": "prova",
                "_source": {
                    "path": "index",
                    "project": "prova",
                    "title": "Titolo del documento",
                    "version": "latest"
                },
                "highlight": {
                    "content": [
                        "Titolo del documento  Nel <em>Capitolo</em> 1 Nel <em>Capitolo</em> 2"
                    ]
                }
            }
        ]
    },
    "aggregations": {
        "project": {
            "doc_count_error_upper_bound": 0,
            "sum_other_doc_count": 0,
            "buckets": [
                {
                    "key": "prova",
                    "doc_count": 3
                }
            ]
        },
        "taxonomy": {
            "doc_count_error_upper_bound": 0,
            "sum_other_doc_count": 0,
            "buckets": []
        },
        "version": {
            "doc_count_error_upper_bound": 0,
            "sum_other_doc_count": 0,
            "buckets": [
                {
                    "key": "latest",
                    "doc_count": 3
                }
            ]
        }
    }
}
"""
