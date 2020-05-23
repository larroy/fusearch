from fusearch.index import Index
from fusearch.tokenizer import Tokenizer, tokfreq
from pony.orm import *
from fusearch.model import Document
from nose.tools import *
from fusearch.util import compose


class NaiveTokenizer(Tokenizer):
    def tokenize(self, x):
        return x.split()


def test_query():
    index = Index({"provider": "sqlite", "filename": ":memory:"}, NaiveTokenizer())
    contents = ["this is an example document example", "this is an another document days go by"]
    tk = compose(tokfreq, index.tokenizer.tokenize)
    docs = [
        Document("/path/doc.pdf", "doc", contents[0], tk(contents[0]), 0),
        Document("/path/doc2.pdf", "doc2", contents[1], tk(contents[1]), 0),
    ]
    for doc in docs:
        index.add_document(doc)

    results = index.query("another days document")
    urls = [x[0] for x in index.rank(results)]
    eq_(urls, ["/path/doc2.pdf", "/path/doc.pdf"])
    eq_([x[0] for x in index.ranked("another")], ["/path/doc2.pdf"])
    eq_([x[0] for x in index.ranked("nada")], [])
    eq_(set([x[0] for x in index.ranked("document")]), set(["/path/doc2.pdf", "/path/doc.pdf"]))


if __name__ == "__main__":
    import nose

    nose.run(defaultTest=__name__)
