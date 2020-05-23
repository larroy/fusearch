from pony.orm import Database, LongStr, ObjectNotFound, Optional, PrimaryKey, Required, Set, db_session
from .tokenizer import Tokenizer
from collections import defaultdict
from .util import uniq
import math
from .model import Result, Document
import operator
import logging
import json
import hashlib
import typing

# TODO add typing


def sha1_mem(x):
    if type(x) is str:
        x = x.encode(errors="replace")
    ctx = hashlib.sha1()
    ctx.update(x)
    return ctx.hexdigest()


class Index:
    """Inverted index implemented with Pony ORM"""

    def __init__(self, bindargs, tokenizer: Tokenizer):
        """
        :param bindargs: pony bind args such as {'provider':'sqlite', 'filename':':memory:'}
        :param tokenizer: A class implementing :class:`tokenizer.Tokenizer`
        """
        self.tokenizer = tokenizer
        # set_sql_debug(True)

        db = Database()
        self.db = db

        @db.on_connect(provider="sqlite")
        def sqlite_sync_off(db, connection):
            cursor = connection.cursor()
            cursor.execute("PRAGMA synchronous = OFF")
            cursor.execute("PRAGMA cache_size = 64000")
            cursor.execute("PRAGMA journal_mode = OFF")

        class Token(db.Entity):
            tok = Required(str, unique=True)
            doc_freq = Required(int)
            documents = Set("Document")

        class Document(db.Entity):
            # url = pony.orm.core.Index(Required(str))
            url_sha = PrimaryKey(str)
            url = Required(str, unique=True)
            filename = Required(str)
            mtime = Required(int)
            content = Optional(LongStr)
            content_sha = Optional(str)
            tokens = Set("Token")
            tokfreq = Required(bytes)

        self.Token = Token
        self.Document = Document
        db.bind(**bindargs)
        db.generate_mapping(create_tables=True)
        self.update()

    def mtime(self, url: str) -> typing.Optional[int]:
        """:returns mtime of the given url or None if not found"""
        url_sha = sha1_mem(url)
        with db_session:
            res = self.db.select("mtime FROM Document WHERE url_sha=$url_sha")
        if res:
            return res[0]
        else:
            return None

    def document_from_url(self, url: str) -> dict:
        """Raises ObjectNotFound when there's no such document or a dictionary with the Document entity when found"""
        url_sha = None
        url_sha = sha1_mem(url)
        with db_session:
            try:
                document = self.Document[url_sha]
                return document.to_dict()
            except ObjectNotFound as ex:
                return None

    def add_document(self, document: Document):
        # tokens = self.tokenizer.tokenize(document.content)
        url_sha = sha1_mem(document.url)
        content_sha = sha1_mem(document.content)
        with db_session:
            doc = self.Document(
                url=document.url,
                url_sha=url_sha,
                filename=document.filename,
                mtime=document.mtime,
                content=document.content,
                content_sha=content_sha,
                tokfreq=json.dumps(document.tokfreq).encode(),
            )

            for tok, freq in document.tokfreq.items():
                token = self.Token.get(tok=tok)
                if token:
                    token.doc_freq += freq
                    token.documents += doc
                else:
                    self.Token(tok=tok, doc_freq=freq, documents=doc)
        self.doc_count += 1

    def update(self):
        with db_session:
            self.doc_count = self.Document.select().count()

    def query(self, txt):
        """Given a query string, return a list of search results"""
        txt_tokens = uniq(self.tokenizer.tokenize(txt))
        logging.debug("Query tokens: %s", txt_tokens)
        results = []
        with db_session:
            tokens = self.Token.select(lambda x: x.tok in txt_tokens)
            for token in tokens:
                numdocs_t = len(token.documents)
                logging.debug("token: %s in %d documents", token, numdocs_t)
                for document in token.documents:
                    try:
                        tokfreq = json.loads(document.tokfreq)
                    except RuntimeError as e:
                        logging.error("json.loads WTF?")
                    tok = token.tok
                    numtok = 1 if len(tokfreq) == 0 else len(tokfreq)
                    tfidf = tokfreq.get(tok, 0) * math.log(self.doc_count / numdocs_t) / numtok
                    results.append(Result(tok=tok, tfidf=tfidf, url=document.url))
        return results

    def rank(self, results):
        """Convert list of Result to a ranked list of urls"""
        by_doc = defaultdict(float)
        # Is this the best way to combine TFIDF? probably not
        for x in results:
            by_doc[x.url] += x.tfidf
        sorted_results = sorted(by_doc.items(), key=operator.itemgetter(1), reverse=True)
        # urls = [x[0] for x in sorted_results]
        return sorted_results

    def ranked(self, txt):
        return self.rank(self.query(txt))
