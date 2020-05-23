# FUSEARCH

![Python package](https://github.com/larroy/fusearch/workflows/Python%20package/badge.svg)
![https://pypi.python.org/pypi/fusearch](https://img.shields.io/badge/python-3.6+-blue.svg?style=flat)
![https://twitter.com/plarroy](https://img.shields.io/twitter/follow/larroy.svg?style=social&label=Follow&maxAge=60)

A Python3, console based full-text search for document collections. It converts different types of
documents such as PDF, word files etc to text and creates a simple inverted index for queries.

The index is kept in a sqlite file in the indexed directory.

**This software is ALPHA status**


## How to run

Recommend to create and activate a venv

```
virtualenv -p(which python3) venv
source venv/bin/activate
```

Edit `fusearch.yaml` and add some directory to index.

Start the daemon in foreground mode (-f) and see the indexing process take place.

```
pip install -e .
fusearchd.py -f -c fusearch.yaml
```


## Dependencies

From textract:

apt-get install python-dev libxml2-dev libxslt1-dev antiword unrtf poppler-utils pstotext
tesseract-ocr \
flac ffmpeg lame libmad0 libsox-fmt-mp3 sox libjpeg-dev swig
