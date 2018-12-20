from collections import namedtuple

Document = namedtuple('Document', ['url', 'filename', 'content'])


Result = namedtuple('Result', ['tok', 'tfidf', 'url'])
