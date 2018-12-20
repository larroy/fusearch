from fusearch.index import Index
from fusearch.tokenizer import Tokenizer
from pony.orm import *
import logging
from fusearch.model import Document
from nose.tools import *

class NaiveTokenizer(Tokenizer):
    def tokenize(self, x):
        return x.split()


def test_query():
    index = Index({'provider':'sqlite', 'filename':':memory:'}, NaiveTokenizer())
    docs = [
        Document('/path/doc.pdf', 'doc', 'this is an example document example'),
        Document('/path/doc2.pdf', 'doc', 'this is an another document days go by')
    ]
    for doc in docs:
        index.add_document(doc)
    res = set(index.query_token('example'))
    results = index.query('another days document')
    urls = index.rank(results)
    eq_(urls, ['/path/doc2.pdf', '/path/doc.pdf'])
    eq_(index.ranked('another'), ['/path/doc2.pdf'])
    eq_(index.ranked('nada'), [])


if __name__ == '__main__':
    import nose
    nose.run(defaultTest=__name__)
