from fusearch import tokenizer

from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords

import nltk
import re

from fusearch.util import compose

nltk.download('punkt')

class NLTKTokenizer(tokenizer.Tokenizer):
    def __init__(self):
        self.stemmer = PorterStemmer()
        # TODO: move to config
        self.tok = RegexpTokenizer(r'[\w\']+')
        self.stopWords = set(stopwords.words('english'))
        self.substitutions = [
        ]
        self.token_normalize = compose(
            lambda x: re.sub("^'", '', x),
            lambda x: re.sub("'$", '', x),
            lambda x: re.sub('_+', '_', x),
            lambda x: re.sub('_+$', '', x),
            lambda x: re.sub('^_+', '', x),
            lambda x: x.lower(),
        )

    def tokenize(self, x):
        toks = map(self.stemmer.stem,
            filter(lambda x: x and x not in self.stopWords,
            filter(lambda x: set(x) != {'_'},
            map(self.token_normalize, self.tok.tokenize(x)
        ))))
        return toks


