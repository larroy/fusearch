from collections import namedtuple

Document = namedtuple('Document', ['url', 'filename', 'content', 'mtime'])


Result = namedtuple('Result', ['tok', 'tfidf', 'url'])
