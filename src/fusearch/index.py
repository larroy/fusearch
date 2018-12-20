from pony.orm import *
from .tokenizer import Tokenizer
from collections import defaultdict
from .util import uniq
import msgpack
import math
from .model import Result
import operator


class Index:
    """Inverted index"""
    def __init__(self, bindargs, tokenizer: Tokenizer):
        """
        :param bindargs: pony bind args such as {'provider':'sqlite', 'filename':':memory:'}
        :param tokenizer: A class implementing :class:`tokenizer.Tokenizer`
        """
        self.tokenizer = tokenizer
        # set_sql_debug(True)

        db = Database()

        class Token(db.Entity):
            tok = Required(str, unique=True)
            doc_freq = Required(int)
            documents = Set('Document')

        class Document(db.Entity):
            url = Required(str)
            filename = Required(str)
            content = Optional(LongStr)
            tokens = Set('Token')
            tokfreq = Required(bytes)


        self.Token = Token
        self.Document = Document
        db.bind(**bindargs)
        db.generate_mapping(create_tables=True)
        self.doc_count = 0

    def add_document(self, document):
        tokens = self.tokenizer.tokenize(document.content)
        tokfreq = defaultdict(int)
        for tok in tokens:
            tokfreq[tok] += 1
        with db_session:
            doc = self.Document(
                url=document.url,
                filename=document.filename,
                content=document.content,
                tokfreq=msgpack.packb(tokfreq))

            for tok, freq in tokfreq.items():
                token = self.Token.get(tok=tok)
                if token:
                    token.doc_freq += freq
                    token.documents += doc
                else:
                    self.Token(tok=tok, doc_freq=freq, documents=doc)
        self.doc_count += 1

    def query_token(self, token):
        result = []
        with db_session:
            tok = self.Token.get(tok=token)
            for doc in tok.documents:
                result.append(doc.url)
        return result

    def update(self):
        # TODO update doc_count
        pass


    def query(self, txt):
        """Given a query string, return a list of search results"""
        txt_tokens = uniq(self.tokenizer.tokenize(txt))
        results = []
        with db_session:
            tokens = self.Token.select(lambda x: x.tok in txt_tokens)
            for token in tokens:
                numdocs_t = len(token.documents)
                for document in token.documents:
                    tokfreq = msgpack.unpackb(document.tokfreq, raw=False)
                    tok = token.tok
                    tfidf = tokfreq[tok] * math.log(self.doc_count/numdocs_t) / len(tokfreq)
                    results.append(
                        Result(
                            tok=tok,
                            tfidf=tfidf,
                            url=document.url
                        )
                    )
        return results

    def rank(self, results):
        """Convert list of Result to a ranked list of urls"""
        by_doc = defaultdict(float)
        # Is this the best way to combine TFIDF? probably not
        for x in results:
            by_doc[x.url] += x.tfidf
        sorted_results = sorted(by_doc.items(), key=operator.itemgetter(1), reverse=True)
        urls = [x[0] for x in sorted_results]
        return urls

    def ranked(self, txt):
        return self.rank(self.query(txt))


#index = Index({'provider':'sqlite', 'filename':':memory:'})
#index.add_document()
