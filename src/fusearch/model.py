from collections import namedtuple

Document = namedtuple('Document', ['url', 'filename', 'content', 'tokfreq', 'mtime'])


Result = namedtuple('Result', ['tok', 'tfidf', 'url'])
