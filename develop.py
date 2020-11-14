# from testbed_from_inventory import create_testbed
# import configparser
from genie.abstract import Lookup
from genie.libs import ops  # noqa
from genie.conf import Genie
from prettytable import PrettyTable
import re
import pprint

testbed = Genie.init('tests/testbed.yml')


device = testbed.devices['fspipswi001']


# Conenct to the device
device.connect()
interfaces = device.parse("show interfaces")
switchports = device.parse("show interfaces switchport")

ntp = device.parse("show ntp associations")

interface_list = {}
for intf, v in interfaces.items():
    if 'description' in v:
        decsc = v['description']
    else:
        decsc = None
    if not 'Vlan' in intf:
        intf_obj = {}
        intf_obj[intf] = {
            'description': decsc,
            'access_vlan': switchports[intf]['access_vlan'],

        }

        if 'voice_vlan' in switchports[intf]:
            intf_obj.update(voice_vlan=switchports[intf]['voice_vlan'])
        else:
            intf_obj.update(voice_vlan=None)

        interface_list.update(intf_obj)


pp = pprint.PrettyPrinter(indent=1)
pp.pprint(interface_list)
