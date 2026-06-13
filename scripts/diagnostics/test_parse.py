import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../engine')))
from search.query_parser import parse_query
print(parse_query('xyzzyplugh and the zorkmid of xyzzyplugh'))
