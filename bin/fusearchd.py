#!/usr/bin/env python3

"""Fusearch daemon"""

import argparse
import os
import signal
import sys
import logging
import textract
import functools
import progressbar
import tempfile
import pickle
import io
from fusearch.index import Index
from fusearch.model import Document
from fusearch.tokenizer import get_tokenizer, tokfreq, Tokenizer
from fusearch.util import bytes_to_str, file_generator_ext, filename_without_extension, mtime, pickle_loader
from fusearch.config import Config
from multiprocessing import Process, Queue, cpu_count
import collections.abc

progressbar_index_widgets_ = [
    " [",
    progressbar.Timer(format="Elapsed %(elapsed)s"),
    ", ",
    progressbar.SimpleProgress(),
    " files"
    #'count: ', progressbar.Counter(),
    "] ",
    progressbar.Bar(),
    " (",
    progressbar.ETA(),
    ") ",
]


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
    os.chdir("/")
    config_signal_handlers()
    os.umask(0o022)
    redirect_stream(sys.stdin, None)
    redirect_stream(sys.stdout, open("/tmp/fusearch.out", "a"))
    redirect_stream(sys.stderr, open("/tmp/fusearch.err", "a"))
    fusearch_main()


def config_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="fusearch daemon", epilog="")
    parser.add_argument("-f", "--foreground", action="store_true", help="Don't daemonize")
    parser.add_argument("-c", "--config", type=str, default="/etc/fusearch/config.yaml", help="config file")
    return parser


def to_text(file: str) -> str:
    assert os.path.isfile(file)
    try:
        txt_b = textract.process(file, method="pdftotext")
        # TODO more intelligent decoding? there be dragons
        txt = bytes_to_str(txt_b)
        # print(file)
        # print(len(txt))
        # print(txt[:80])
        # print('-------------------')
    except Exception as e:
        txt = ""
        logging.exception("Exception while extracting text from '%s'", file)
        # TODO mark it as failed instead of empty text
    return txt


def document_from_file(file: str, tokenizer: Tokenizer) -> Document:
    mtime_latest = mtime(file)
    filename = filename_without_extension(file)
    txt = filename + "\n" + to_text(file)
    # Detect language and check that the document makes sense, OCR returns garbage sometimes
    # TODO: add filename to content
    document = Document(url=file, filename=filename, content=txt, tokfreq=tokfreq(tokenizer(txt)), mtime=mtime_latest)
    return document


def needs_indexing(index: Index, file: str) -> bool:
    mtime_latest = mtime(file)
    # document = index.document_from_url(file)
    mtime_last_known = index.mtime(file)
    if not mtime_last_known or mtime_last_known and mtime_latest > mtime_last_known:
        # logging.debug("needs_indexing: need '%s'", file)
        return True
    else:
        # logging.debug("needs_indexing: NOT need '%s'", file)
        return False


def get_index(path: str, config: Config) -> Index:
    index_db = os.path.join(path, ".fusearch.db")
    index = Index({"provider": "sqlite", "filename": index_db, "create_db": True}, tokenizer=get_tokenizer(config))
    logging.debug("get_index: '%s' %d docs", index_db, index.doc_count)
    return index


class NeedsIndexFileGenerator(object):
    def __init__(self, path, config):
        self.path = path
        self.config = config
        self.index = get_index(path, config)
        assert os.path.isdir(path)

    def __call__(self) -> collections.abc.Iterable:
        """:returns a generator of files which are updated from the mtime in the index"""
        file_needs_indexing = functools.partial(needs_indexing, self.index)
        return filter(file_needs_indexing, file_generator_ext(self.path, self.config.include_extensions))


def file_producer(path: str, config: Config, file_queue: Queue, file_inventory: io.IOBase) -> None:
    for file in pickle_loader(file_inventory):
        # logging.debug("file_producer: %s", file)
        file_queue.put(file)
    logging.debug("file_producer is done")


def text_extract(config: Config, file_queue: Queue, document_queue: Queue):
    # logging.debug("text_extract started")
    tokenizer = get_tokenizer(config)
    while True:
        file = file_queue.get()
        if file is None:
            logging.debug("text_extract is done")
            return
        logging.debug(
            "text_extract: file_queue.qsize %d document_queue.qsize %d", file_queue.qsize(), document_queue.qsize()
        )
        logging.debug("text_extract: '%s'", file)
        # logging.debug("text_extract: %s", file)
        document = document_from_file(file, tokenizer)
        document_queue.put(document)


def document_consumer(path: str, config: Config, document_queue: Queue, file_count: int) -> None:
    index = get_index(path, config)
    if config.verbose:
        pbar = progressbar.ProgressBar(max_value=file_count, widgets=progressbar_index_widgets_)
    file_i = 0
    while True:
        doc = document_queue.get()
        logging.debug("document_consumer(%d): document_queue.qsize %d", os.getpid(), document_queue.qsize())
        if doc is None:
            logging.debug("Document consumer, no more elements in the queue")
            if config.verbose:
                pbar.finish()
            return
        try:
            index.add_document(doc)
            logging.debug("document_consumer(%d): added %s", os.getpid(), doc.url)
        except Exception as e:
            logging.exception("document_consumer: index.add_document exception. Document[%s]", doc.url)
        if config.verbose:
            pbar.update(file_i)
        file_i += 1


def gather_files(path, config, file_inventory) -> int:
    """:returns file count"""
    if not os.path.isdir(path):
        logging.error("Not a directory: '%s', skipping indexing", path)
        return
    logging.info("Indexing %s", path)
    logging.info("Calculating number of files to index (.=100files)")
    if config.verbose:
        widgets = [
            " [",
            progressbar.Timer(format="Elapsed %(elapsed)s"),
            " ",
            "count: ",
            progressbar.Counter(),
            "] ",
            progressbar.BouncingBar(),
        ]
        pbar = progressbar.ProgressBar(widgets=widgets)
    file_count = 0
    for file in NeedsIndexFileGenerator(path, config)():
        pickle.dump(file, file_inventory)
        file_count += 1
        # if config.verbose and (file_count % 100) == 0:
        #    sys.stdout.write('.')
        #    sys.stdout.flush()
        if config.verbose:
            pbar.update(file_count)
    # if config.verbose:
    #    sys.stdout.write('\n')
    if config.verbose:
        pbar.finish()
    file_inventory.seek(0)
    return file_count


def index_do(path, config) -> None:
    file_inventory = tempfile.TemporaryFile()
    file_count = gather_files(path, config, file_inventory)
    logging.info("%d files to process", file_count)
    if config.parallel_extraction:
        index_parallel(path, config, file_count, file_inventory)
    else:
        index_serial(path, config, file_count, file_inventory)


def index_parallel(path: str, config: Config, file_count: int, file_inventory) -> None:
    #
    # file_producer -> N * test_extract -> document_consumer
    #
    # TODO: check that processes are alive to prevent deadlocks on exceptions in children
    file_queue = Queue(cpu_count() * 8)
    document_queue = Queue(256)
    text_extract_procs = []
    file_producer_proc = Process(
        name="file producer", target=file_producer, daemon=True, args=(path, config, file_queue, file_inventory)
    )
    file_producer_proc.start()

    document_consumer_proc = Process(
        name="document consumer", target=document_consumer, daemon=True, args=(path, config, document_queue, file_count)
    )

    for i in range(cpu_count()):
        p = Process(
            name="text extractor {}".format(i),
            target=text_extract,
            daemon=True,
            args=(config, file_queue, document_queue),
        )
        text_extract_procs.append(p)
        p.start()
    document_consumer_proc.start()

    logging.debug("child processes started")

    logging.debug("joining producer")
    file_producer_proc.join()
    logging.debug("joining text_extract")
    for p in text_extract_procs:
        file_queue.put(None)
    for p in text_extract_procs:
        logging.debug("joining text_extract %s", p)
        p.join()
    document_queue.put(None)
    logging.debug("joining document_consumer")
    document_consumer_proc.join()
    logging.info("Parallel indexing finished")


def index_serial(path, config, file_count, file_inventory):
    if config.verbose:
        pbar = progressbar.ProgressBar(max_value=file_count, widgets=progressbar_index_widgets_)
    file_i = 0
    tokenizer = get_tokenizer(config)
    logging.info("Indexing started")
    index = get_index(path, config)
    for file in pickle_loader(file_inventory):
        doc = document_from_file(file, tokenizer)
        try:
            index.add_document(doc)
        except Exception as e:
            logging.exception("index_serial: index.add_document exception. Document[%s]", doc.url)
        if config.verbose:
            pbar.update(file_i)
        file_i += 1
    if config.verbose:
        pbar.finish()


def fusearch_main(args) -> int:
    logging.info("reading config from %s", args.config)
    config = Config.from_file(args.config)
    logging.info("%s", config)
    for path in config.index_dirs:
        index_do(path, config)


def script_name() -> str:
    """:returns: script name with leading paths removed"""
    return os.path.split(sys.argv[0])[1]


def config_logging() -> None:
    import time

    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.basicConfig(format="{}: %(asctime)sZ %(name)s %(levelname)s %(message)s".format(script_name()))
    logging.Formatter.converter = time.gmtime


def main() -> int:
    config_logging()
    parser = config_argparse()
    args = parser.parse_args()
    if not args.foreground:
        return daemonize()
    fusearch_main(args)


if __name__ == "__main__":
    sys.exit(main())
