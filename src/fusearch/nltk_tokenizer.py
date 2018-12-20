from .tokenizer import Tokenizer

from nltk.stem import PorterStemmer
import nltk

class NLTKTokenizer(Tokenizer):
    def __init__(self):
        self.stemmer = PorterStemmer()

    def tokenize(self, x):
        return list(map(self.stemmer.stem, nltk.word_tokenize(x)))

