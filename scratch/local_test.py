import pprint

from pyaltium import PcbLib, SchLib

pp = pprint.PrettyPrinter(indent=4)


# Quick schlib test
sl = SchLib("test/files/SchLib1.SchLib")
pp.pprint(sl.list_items(as_dict=True))

# Quick PCBLib test
pl = PcbLib("test/files/PcbLib1.PcbLib")
pp.pprint(pl.list_items(as_dict=True))
