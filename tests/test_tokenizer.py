import nose
from nose.tools import *

from fusearch.nltk_tokenizer import NLTKTokenizer

def test_tokenizer():
    tok = NLTKTokenizer()
    toks = list(tok.tokenize('directed the movie long time don\'t complain OMG ___ $!&&#$'))
    eq_(toks, ['direct', 'movi', 'long', 'time', 'complain', 'omg'])

if __name__ == '__main__':
    import nose
    nose.run(defaultTest=__name__)