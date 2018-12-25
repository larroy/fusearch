from fusearch.index import Index
from fusearch.nltk_tokenizer import NLTKTokenizer
import os
import logging
import sys
logging.getLogger().setLevel(logging.DEBUG)

path=os.path.join('/Users/pllarroy/docu')
index_file = os.path.join(path, '.fusearch.db')
index = Index({
    'provider':'sqlite',
    'filename': index_file,
    'create_db': True
}, tokenizer=NLTKTokenizer())
print(index.ranked(sys.argv[1]))
