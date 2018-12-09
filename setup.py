from setuptools import setup, find_packages

from os import path

setup(
    name="fusearch",
    version="0.1",
    packages=find_packages('src'),
    install_requires=['textract'],
    tests_require=['nose'],
    package_data={},
    autho="Pedro Larroy",
    author_email="pedro.larroy.lists@gmail.com",
    description="fusearch is a local full text search engine",
    license="Apache 2",
    keywords="search console fulltext documents",
    url="https://github.com/larroy/fusearch",
    project_urls={
        "Source Code": "https://github.com/larroy/fusearch",
    }
)
