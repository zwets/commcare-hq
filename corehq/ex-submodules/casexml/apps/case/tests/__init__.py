from casexml.apps.case.mock import CaseBlock

# need all imports used by the doc tests here
from datetime import datetime                       # noqa: F401
from xml.etree import cElementTree as ElementTree   # noqa: F401

__test__ = {
    'caseblock': CaseBlock
}


def setUpModule():
    from corehq.elastic import get_es_new, debug_assert
    debug_assert(get_es_new())
