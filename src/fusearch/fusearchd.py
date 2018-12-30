    #!/usr/bin/env python3

"""Fusearch daemon"""

import argparse
import os
import signal
import sys
import logging
import yaml
import textract
import filetype
import functools
import progressbar
from fusearch.index import Index
from fusearch.model import Document
from fusearch.nltk_tokenizer import NLTKTokenizer


def script_name() -> str:
    """:returns: script name with leading paths removed"""
    return os.path.split(sys.argv[0])[1]


def config_logging() -> None:
    import time
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.basicConfig(format='{}: %(asctime)sZ %(name)s %(levelname)s %(message)s'.
                        format(script_name()))
    logging.Formatter.converter = time.gmtime


def cleanup() -> None:
    pass


def reload_config() -> None:
    pass


def config_signal_handlers() -> None:
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGUSR1, reload_config)
    signal.signal(signal.SIGTTIN, signal.SIG_IGN)
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)
    signal.signal(signal.SIGTTOU, signal.SIG_IGN)


def redirect_stream(system_stream, target_stream):
    """ Redirect a system stream to a specified file.

        :param standard_stream: A file object representing a standard I/O
            stream.
        :param target_stream: The target file object for the redirected
            stream, or ``None`` to specify the null device.
        :return: ``None``.

        `system_stream` is a standard system stream such as
        ``sys.stdout``. `target_stream` is an open file object that
        should replace the corresponding system stream object.

        If `target_stream` is ``None``, defaults to opening the
        operating system's null device and using its file descriptor.

        """
    if target_stream is None:
        target_fd = os.open(os.devnull, os.O_RDWR)
    else:
        target_fd = target_stream.fileno()
    os.dup2(target_fd, system_stream.fileno())


def fork_exit_parent() -> None:
    pid = os.fork()
    if pid > 0:
        sys.exit(0)


def daemonize() -> None:
    fork_exit_parent()
    os.setsid()
    fork_exit_parent()
    os.chdir('/')
    config_signal_handlers()
    os.umask(0o022)
    redirect_stream(sys.stdin, None)
    redirect_stream(sys.stdout, open('/tmp/fusearch.out', 'a'))
    redirect_stream(sys.stderr, open('/tmp/fusearch.err', 'a'))
    fusearch_main()


# FIXME lockfile


class Config(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @staticmethod
    def from_file(conf_file):
        assert os.path.isfile(conf_file)
        with open(conf_file, 'r') as fd:
            cfg = yaml.safe_load(fd.read())
        if cfg:
            return Config(**cfg)
        return Config()

    def __str__(self):
        return self.__class__.__name__ + '(' + str(self.__dict__) + ')'


def config_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="fusearch daemon", epilog="")
    parser.add_argument('-f', '--foreground', action='store_true',
                        help="Don't daemonize")
    parser.add_argument('-c', '--config', type=str,
                        default='/etc/fusearch/config.yaml',
                        help="config file")
    return parser


def file_extension(filepath) -> str:
    _, ext_ = os.path.splitext(filepath)
    ext = ext_.lower()
    return ext


def filetype_admissible(include_extensions, file):
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


def file_generator(path):
    for (dirpath, dirnames, files) in os.walk(path):
        for file in files:
            yield os.path.abspath(os.path.join(dirpath, file))


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

def to_text(file) -> None:
    try:
        txt_b = textract.process(file, method='pdftotext')
        # TODO more intelligent decoding? there be dragons
        txt = bytes_to_str(txt_b)
        #print(file)
        #print(len(txt))
        #print(txt[:80])
        #print('-------------------')
    except Exception as e:
        txt = ''
        logging.exception("Exception while extracting text from '%s'", file)
    return txt


def text_extraction(url) -> Document:
    assert os.path.isfile(url)
    txt = to_text(url)
    return txt


def mtime(url) -> int:
    """return modification time as seconds since epoch"""
    # TODO this can be made more generic if different protocols are supported, right now only works for local files
    stat_result = os.stat(url)
    return int(stat_result.st_mtime)

def index_file(index, file) -> None:
    mtime_latest = mtime(file)
    document = index.document_from_url(file)
    if not document or document and mtime_latest > document['mtime']:
        txt = text_extraction(file)
        document = Document(url=file, filename=filename_without_extension(file), content=txt, mtime=mtime_latest)
        index.add_document(document)
    else:
        # Not changed
        logging.debug("file %s hasn't changed", file)


def index(path, config) -> None:
    if not os.path.isdir(path):
        logging.error("Not a directory: '%s', skipping indexing", path)
        return
    desired_filetype = functools.partial(filetype_admissible, set(config.include_extensions))
    logging.info("Indexing %s", path)
    index_db = os.path.join(path, '.fusearch.db')
    index = Index({
        'provider':'sqlite',
        'filename': index_db,
        'create_db': True
    }, tokenizer=NLTKTokenizer())
    logging.info("index initialized (%s)", index_db)

    logging.info("Calculating number of files to index (.=100files)")
    files = filter(desired_filetype, file_generator(path))
    file_count = 0
    for file in files:
        file_count += 1
        if config.verbose and (file_count % 100) == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
    if config.verbose:
        sys.stdout.write('\n')

    logging.info("%d files to process", file_count)

    widgets = [
        ' [', progressbar.Timer(), '] ',
        progressbar.Bar(),
        ' (', progressbar.ETA(), ') ',
    ]
    pbar = progressbar.ProgressBar(max_value=file_count, widgets=widgets)
    files = filter(desired_filetype, file_generator(path))
    file_i = 0
    for file in files:
        index_file(index, file)
        pbar.update(file_i)
        file_i += 1


def fusearch_main(args) -> int:
    logging.info("reading config from %s", args.config)
    config = Config.from_file(args.config)
    logging.info("%s", config)
    for path in config.index_dirs:
        index(path, config)


def main() -> int:
    config_logging()
    parser = config_argparse()
    args = parser.parse_args()
    if not args.foreground:
        return daemonize()
    fusearch_main(args)


if __name__ == '__main__':
    sys.exit(main())
