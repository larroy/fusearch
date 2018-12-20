import nose

from fusearch.nltk_tokenizer import NLTKTokenizer

def test_tokenizer():
    tok = NLTKTokenizer()
    toks = tok.tokenize('directed the movie long time')
    print(toks)

if __name__ == '__main__':
    import nose
    nose.run(defaultTest=__name__)