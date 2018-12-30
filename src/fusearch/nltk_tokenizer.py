import tokenizer

from nltk.stem import PorterStemmer
import nltk

nltk.download('punkt')

class NLTKTokenizer(tokenizer.Tokenizer):
    def __init__(self):
        self.stemmer = PorterStemmer()

    def tokenize(self, x):
        return list(map(self.stemmer.stem, nltk.word_tokenize(x)))

