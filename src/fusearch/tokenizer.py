from abc import ABC, abstractmethod
from fusearch.config import Config
from collections import defaultdict

def get_tokenizer(config: Config):
    from fusearch.nltk_tokenizer import NLTKTokenizer
    return NLTKTokenizer()


def tokfreq(tokens: list) -> dict:
    tokfreq = defaultdict(int)
    for tok in tokens:
        tokfreq[tok] += 1
    return tokfreq


class Tokenizer(ABC):
    def __init__(self):
        pass

    def __call__(self, x):
        return self.tokenize(x)

    @abstractmethod
    def tokenize(self, x):
        pass
