import argparse
import os
import socket
import sys
import time

from subprocess import call

import logging

logging.basicConfig()
logger = logging.getLogger(__name__)

TIMEOUT_DEFAULT = 20
WAIT_DEFAULT = 300


class HostPort:
    def __init__(self, hostport_str):
        badchars = set(hostport_str.lower()).difference(
            set("abcdefghijklmnopqrstuvwxyz0123456789.-:")
        )
        if badchars:
            msg = "Unacceptable characters in host: '{}'".format(str(list(badchars)))
            logger.fatal(msg)
            raise ValueError(msg)
        if ":" not in hostport_str:
            msg = "Expecting a host and port specification (e.g. 'host:port'). Found '{}'".format(
                hostport_str
            )
            raise ValueError(msg)
        parts = hostport_str.split(":")
        if len(parts) > 2:
            msg = "Unexpected additional ':' separators"
            logger.fatal(msg)
            raise ValueError(msg)
        host = parts[0]
        port = int(parts[1])
        self.host = host
        self.port = port
        self.working = False

    def __str__(self):
        return "{}:{}".format(self.host, self.port)

    def test_socket(self, timeout):
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                result = sock.connect_ex((self.host, self.port))
                if result == 0:
                    self.working = True
            except socket.gaierror as e:
                logger.error(
                    "'host={}' port={} e={}({})".format(
                        self.host, self.port, e, type(e)
                    )
                )
        return self.working


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Wait for host:port to be available. End with a '--' argument for full compatibility with the 'command' handling",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="provide detailed information (overrides --quiet)",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="suppress informational messages",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=TIMEOUT_DEFAULT,
        help="seconds to wait for a service test (default {})".format(TIMEOUT_DEFAULT),
    )
    parser.add_argument(
        "--wait",
        "-w",
        type=int,
        default=WAIT_DEFAULT,
        help="overall maximum seconds for all tests (default {})".format(WAIT_DEFAULT),
    )
    parser.add_argument(
        "hostport", metavar="HOST:PORT", nargs="+", help="what to watch 'host:port'"
    )
    args = parser.parse_args(sys.argv[1:])
    return args


def _set_logging(args):
    logger.setLevel(logging.INFO)
    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.WARNING)
    logger.debug("Args: {}".format(args))


def main():
    args = parse_arguments()
    _set_logging(args)
    timeout = args.timeout
    max_wait = args.wait
    options = args.hostport
    #
    hostports_left = []
    commands = []
    first_pass = True
    for optval in options:
        if ":" not in optval or commands:
            commands.append(optval)
            continue
        new_hostport = HostPort(optval)
        hostports_left.append(new_hostport)
        logger.info("[{} added]".format(new_hostport))
    left = len(hostports_left)
    start_time = time.time()
    end_time = start_time + max_wait
    logger.info(
        "Starting testing {} service(s) for up to {} seconds".format(left, max_wait)
    )
    while hostports_left and time.time() < end_time:
        retry_hostports = []
        for hostport in hostports_left:
            if hostport.test_socket(timeout):
                left -= 1
                logger.info("[{} ok, leaving {}]".format(hostport, left))
                continue
            retry_hostports.append(hostport)
        hostports_left = retry_hostports
        if not len(hostports_left):
            break
        time.sleep(1)
    if left:
        logger.fatal("{} unavailable: {}".format(left, hostports_left))
        exit(left)
    if commands:
        logger.info("Invoking command...")
        call(commands)
    exit()


if __name__ == "__main__":
    main()
