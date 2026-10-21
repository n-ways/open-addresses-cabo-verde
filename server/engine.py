"""The reference engine (engine/reference/cv_engine.py), loaded from this
repository, with the frozen register taken from the database.

The server never reimplements the code rules: parsing, check digits, forms,
plate names, Plus Codes, municipalities, Hilbert numbering and blocks all come
from the reference engine. Inside the Docker image the engine sits at
/app/engine/reference, next to /app/server.
"""
import os
import sys

_REF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine', 'reference')
if _REF not in sys.path:
    sys.path.insert(0, _REF)

import cv_engine as _cv  # noqa: E402
from cv_engine import *  # noqa: E402,F403

COUNTRY = 'CV'
COUNTRY_NAME = 'Cabo Verde'
CREDIT = 'Home code by N-Ways Addressing'
CREDIT_URL = 'https://github.com/n-ways/open-addresses-cabo-verde'
DATA_CREDIT = 'N-Ways Addressing for Cabo Verde, © N-WAYS LIMITED (nways.ng)'
LICENCES = {'code': 'Apache-2.0', 'data': 'ODbL-1.0', 'documents': 'CC-BY-4.0'}

use_register = _cv.use_register
names = _cv.names
zones = _cv.zones
names_by_index = _cv.names_by_index
zone_by_ref = _cv.zone_by_ref
SPEC = 'engine/SPEC.md'


def residential(use):
    """A home or its annexe: never named, nothing about the people inside."""
    return use.split('.')[0] in ('residencial', 'anexo')
