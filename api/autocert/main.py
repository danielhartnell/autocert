#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pwd
import sys
import requests

from fnmatch import fnmatch

from flask import Flask, jsonify
from flask import request, render_template
from ruamel import yaml
from subprocess import check_output
from attrdict import AttrDict

from pdb import set_trace as breakpoint

from logging.config import dictConfig
from logging import (
    CRITICAL,
    ERROR,
    WARNING,
    INFO,
    DEBUG,
    NOTSET)

from autocert.config import CFG
from autocert.utils import version
from autocert.utils.dictionary import merge
from autocert.utils.version import version as api_version

LOGGING_MAP = {
    'CRITICAL': CRITICAL,
    'ERROR':    ERROR,
    'WARNING':  WARNING,
    'INFO':     INFO,
    'DEBUG':    DEBUG,
    'NOTSET':   NOTSET,
}

INVALID_STATUS = [
    'expired',
    'rejected',
]

# the following statements have to be in THIS specfic order: 1, 2, 3
app = Flask('api')                  #1
app.logger                          #2

def log(*msgs):
    app.logger.log(app.logger.getEffectiveLevel(), ' '.join(msgs))


@app.before_first_request
def initialize():
    if sys.argv[0] != 'venv/bin/pytest':
        dictConfig(CFG.logging)     #3
        PID = os.getpid()
        PPID = os.getppid()
        USER = pwd.getpwuid(os.getuid())[0]
        app.logger.info('starting api with pid={PID}, ppid={PPID} by user={USER}'.format(**locals()))

def is_valid_cert(status):
    return status not in INVALID_STATUS

@app.route('/version', methods=['GET'])
def version():
    app.logger.info('/version called')
    version = api_version()
    return jsonify({'version': version})

@app.route('/hello', methods=['GET'])
@app.route('/hello/<string:target>', methods=['GET'])
def hello(target='world'):
    app.logger.info('/hello called with target={target}'.format(**locals()))
    return jsonify({'msg': 'hello %(target)s' % locals()})

def digicert_list_certs():
    app.logger.info('digicert_list_certs called')
    response = requests.get(
        CFG.authorities.digicert.baseurl / 'order/certificate',
        auth=CFG.authorities.digicert.auth,
        headers=CFG.authorities.digicert.headers)
    if response.status_code == 200:
        from pprint import pformat
        obj = AttrDict(response.json())
        certs = [cert for cert in obj.orders if is_valid_cert(cert.status)]
        return {
            'certs': list(certs),
        }
    else:
        app.logger.error('failed request to /list/certs with status_code={0}'.format(response.status_code))

def letsencrypt_list_certs():
    app.logger.info('letsencrypt_list_certs called')
    return {
        'certs': []
    }

AUTHORITIES = {
    'digicert': digicert_list_certs,
    'letsencrypt': letsencrypt_list_certs,
}

@app.route('/list/certs', methods=['GET'])
@app.route('/list/certs/<string:pattern>', methods=['GET'])
def list_certs(pattern='*'):
    app.logger.info('/list/certs called with pattern="{pattern}"'.format(**locals()))
    authorities = [authority for authority in AUTHORITIES.keys() if fnmatch(authority, pattern)]
    app.logger.debug('authorities="{authorities}"'.format(**locals()))
    return jsonify(merge(*[AUTHORITIES[a]() for a in authorities]))