from pony.orm import *


class Index:
    """Inverted index"""
    def __init__(self, bindargs):
        """
        :param bindargs: pony bind args such as {'provider':'sqlite', 'filename':':memory:'}
        """
        db = Database()
        set_sql_debug(True)

        class Document(db.Entity):
            path = Required(str)
            filename = Required(str)
            content = Required(LongStr)
            tokens = Set('Token')

        class Token(db.Entity):
            tok = Required(str)
            doc_freq = Required(int)
            documents = Set(Document)

        db.bind(**bindargs)
        db.generate_mapping(create_tables=True)

    def add_document(self, document):
        with db_session:
            Document(document.path, document.filename, document.content)


index = Index({'provider':'sqlite', 'filename':':memory:'})
index.add_document()
