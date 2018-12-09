#!/usr/bin/env python3

"""Fusearch daemon"""

import argparse
import os
import signal
import sys
import logging
import time
import yaml


def script_name() -> str:
    """:returns: script name with leading paths removed"""
    return os.path.split(sys.argv[0])[1]


def config_logging() -> None:
    import time
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.basicConfig(format='{}: %(asctime)sZ %(levelname)s %(message)s'.
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
        with open(conf_file, 'r') as fd:
            cfg = yaml.safe_load(fd.read())
        return Config(cfg)


def config_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="fusearch daemon", epilog="")
    parser.add_argument('-f', '--foreground', action='store_true',
                        help="Don't daemonize")
    parser.add_argument('-c', '--config', type=str,
                        default='/etc/fusearch/config.yaml',
                        help="config file")
    return parser


def fusearch_main() -> int:
    while True:
        print('hi')
        time.sleep(1)


def main() -> int:
    config_logging()
    parser = config_argparse()
    args = parser.parse_args()
    if not args.foreground:
        return daemonize()
    fusearch_main()


if __name__ == '__main__':
    sys.exit(main())
