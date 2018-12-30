import logging
from typing import *
import collections.abc
import os
import filetype
import functools


def uniq(xs: List[Any]) -> List[Any]:
    result = []
    seen = set()
    for x in xs:
        if x not in seen:
            result.append(x)
        seen.add(x)
    return result

def file_extension(filepath) -> str:
    _, ext_ = os.path.splitext(filepath)
    ext = ext_.lower()
    return ext


def filetype_admissible(include_extensions: set, file):
    ext = file_extension(file)
    if ext in include_extensions:
        return True
    else:
        guess = filetype.guess(file)
        if guess and guess.extension in include_extensions:
            return True
    return False


def filename_without_extension(file):
    _, fname = os.path.split(file)
    base, _ = os.path.splitext(fname)
    return base


def file_generator(path: str) -> collections.abc.Iterable:
    for (dirpath, dirnames, files) in os.walk(path):
        for file in files:
            yield os.path.abspath(os.path.join(dirpath, file))


def file_generator_ext(path: str, extensions: list):
    desired_filetype = functools.partial(filetype_admissible, set(extensions))
    files = filter(desired_filetype, file_generator(path))
    return files


def bytes_to_str(text):
    import chardet
    if isinstance(text, str):
        return text
    else:
        try:
            result = text.decode('utf-8')
            return result
        except UnicodeDecodeError as e:
            logging.exception("UTF-8 decoding error")
        try:
            encoding = chardet.detect(text)
            return text.decode(encoding['encoding'])
        except UnicodeDecodeError as e:
            logging.exception("%s decoding (chardet detected) error", encoding)
            return u''


def mtime(url) -> int:
    """return modification time as seconds since epoch"""
    # TODO this can be made more generic if different protocols are supported, right now only works for local files
    stat_result = os.stat(url)
    return int(stat_result.st_mtime)


