from fusearch import tokenizer

from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords

import nltk
import re

from fusearch.util import compose

nltk.download('punkt')
from operator import methodcaller

class NLTKTokenizer(tokenizer.Tokenizer):
    def __init__(self):
        self.stemmer = PorterStemmer()
        # TODO: move to config
        self.tok = RegexpTokenizer(r'[\w\']+')
        self.stopWords = set(stopwords.words('english'))
        self.substitutions = [
            (re.compile("^'"), ''),
            (re.compile("'$"), ''),
            (re.compile("_+"), '_'),
            (re.compile("_+$"), ''),
            (re.compile("^_+"), '')
        ]
        self.token_normalize = compose(
            self.subst,
            lambda x: x.lower(),
        )

    def subst(self, x):
        for s in self.substitutions:
            x = s[0].sub(s[1], x)
        return x

    def tokenize(self, x):
        toks = map(self.stemmer.stem,
            filter(lambda x: x and x not in self.stopWords,
            filter(lambda x: set(x) != {'_'},
            map(self.token_normalize, self.tok.tokenize(x)
        ))))
        return toks


