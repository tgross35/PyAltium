import pprint

from pyaltium import PcbLib, SchLib

pp = pprint.PrettyPrinter(indent=4)

import pdb

# pdb.set_trace()

# Quick schlib test
sl = SchLib("tests/files/SchLib1.SchLib")
pp.pprint(sl.list_items())

# Quick PCBLib test
pl = PcbLib("tests/files/PcbLib1.PcbLib")
pp.pprint(pl.list_items())
