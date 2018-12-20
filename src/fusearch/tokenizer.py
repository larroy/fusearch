from abc import ABC, abstractmethod

class Tokenizer(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def tokenize(self, x):
        pass
