#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.autocert: provides entry point main().
'''

import os
import imp
import sys
import logging
from subprocess import check_output
from argparse import ArgumentParser, RawDescriptionHelpFormatter

try:
    from ruamel import yaml
    from urlpath import URL
    from attrdict import AttrDict
    from packaging.version import parse as version_parse
except ImportError as ie:
    print(ie)
    print('perhaps you need to install cli/requirements.txt via pip3')

from cli.utils.importer import import_modules
from cli.utils.version import version as cli_version
from cli.utils.output import output
from cli.utils.format import fmt, pfmt
from cli import requests

from cli.config import CFG

VERSIONS = [
    'cli',
    'api'
]

SORTING = [
    'default',
    'timestamp',
    'expiry',
]

class VersionCheckFailedError(Exception):
    def __init__(self, version, required):
        msg = 'autocert/api {version} is not at least {required}'.format(**locals())
        super(VersionCheckFailedError, self).__init__(msg)

def api_version(ns):
    response = requests.get(ns.api_url / 'autocert/version')
    version = 'unknown'
    if response.status_code == 200:
        obj = response.json()
        version = obj['version']
    return version

def version_check(ns):
    if ns.version not in VERSIONS:
        version = api_version(ns)
        version = version.split('-')[0]
        if  version_parse(version) >= version_parse(cli_version()):
            logging.debug('version_check: PASSED')
            return
        raise VersionCheckFailedError(version, cli_version())
    if ns.version == VERSIONS[0]:
        output({'cli-version': cli_version()})
    elif ns.version == VERSIONS[1]:
        output({'api-version': api_version(ns)})
    sys.exit(0)

def add_subparsers(parser):
    '''
    add all files that end with _parser.py in the cli/ directory
    call 'add_parser', passing subparsers to each found module
    '''
    subparsers = parser.add_subparsers(
        dest='command',
        title='commands',
        description='choose a command to run')
    dirpath = os.path.dirname(__file__)
    endswith = '_command.py'
    [mod.add_parser(subparsers) for mod in import_modules(dirpath, endswith)]
    subparsers.required = True
    return subparsers

def main():
    parser = ArgumentParser(
        add_help=False)
    parser.add_argument(
        '-C', '--config',
        action='store_true',
        help='show loaded CFG values')
    parser.add_argument(
        '-D', '--debug',
        action='store_true',
        help='turn on debug mode')
    parser.add_argument(
        '-V', '--version',
        choices = VERSIONS,
        const=VERSIONS[0],
        nargs='?',
        help='default=%(const)s; show the version')
    parser.add_argument(
        '-U', '--api-url',
        metavar='URL',
        default='http://0.0.0.0',
        type=URL,
        help='default=%(default)s; set the api url to use')
    parser.add_argument(
        '-S', '--sort',
        dest='sorting',
        metavar='SORT',
        default=SORTING[0],
        choices=SORTING,
        help='default="%(default)s"; set the sorting method; choices=[%(choices)s]')

    parser.set_defaults(**CFG)
    ns, rem = parser.parse_known_args()
    if not any([h in rem for h in ('-h', '--help')]):
        version_check(ns)

    if ns.config:
        output(dict(CFG=dict(CFG)))
        sys.exit(0)

    parser = ArgumentParser(
        parents=[parser],
        description=__doc__,
        formatter_class=RawDescriptionHelpFormatter)

    add_subparsers(parser)
    parser.set_defaults(**CFG)

    ns = parser.parse_args()
    if ns.debug:
        print('ns =', ns)
    ns.func(ns)
