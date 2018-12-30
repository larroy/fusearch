import tokenizer

from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords

import nltk
import re

nltk.download('punkt')

class NLTKTokenizer(tokenizer.Tokenizer):
    def __init__(self):
        self.stemmer = PorterStemmer()
        # TODO: move to config
        self.tok = RegexpTokenizer(r'[\w\']+')
        self.stopWords = set(stopwords.words('english'))

    def tokenize(self, x):
        toks = filter(lambda x: x and x not in self.stopWords,
            map(lambda x: re.sub("^'", '', x),
            map(lambda x: re.sub("'$", '', x),
            map(lambda x: re.sub('_+', '_', x),
            map(lambda x: re.sub('_+$', '', x),
            map(lambda x: re.sub('^_+', '', x),
            map(lambda x: x.lower(),
            map(self.stemmer.stem,
                self.tok.tokenize(x)
            )))))))
        )
        toks_no_underscores = filter(lambda x: set(x) != {'_'}, toks)
        return toks_no_underscores


