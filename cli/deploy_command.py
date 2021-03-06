#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
cli.deploy
'''

import requests

from cli.utils.output import output
from cli.namespace import jsonify
from cli.arguments import add_argument

from utils.dictionary import dictify

def add_parser(subparsers):
    parser = subparsers.add_parser('deploy')
    add_argument(parser, '-d', '--destinations')
    add_argument(parser, '-c', '--calls')
    add_argument(parser, '-v', '--verbose')
    add_argument(parser, 'cert_name_pns')
    parser.set_defaults(func=do_deploy)

def do_deploy(ns):
    response = requests.put(ns.api_url / 'autocert', json=jsonify(ns, destinations=dictify(ns.destinations)))
    if response.status_code == 200:
        certs = response.json().get('certs', [])
        output(certs)
    elif response.status_code == 201:
        certs = response.json().get('certs', [])
        output(certs)
    else:
        print(response)
        print(response.text)
        raise Exception('wtf do_deploy')

