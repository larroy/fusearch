from fusearch.index import Index
from fusearch.nltk_tokenizer import NLTKTokenizer
import os
import logging
import sys
logging.getLogger().setLevel(logging.DEBUG)

path=os.path.join('/Users/pllarroy/docu')
index_file = os.path.join(path, '.fusearch.db')
index_file = '/Users/pllarroy/docu/software/programming/.fusearch.db'
index = Index({
    'provider':'sqlite',
    'filename': index_file,
    'create_db': True
}, tokenizer=NLTKTokenizer())
#print(index.document_from_url('/Users/pllarroy/docu/books/Ortografia.pdf'))
print(index.ranked('linear regression gradient descent'))
