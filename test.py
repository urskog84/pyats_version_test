from testbed_from_inventory import create_testbed
import configparser
from genie.abstract import Lookup
from genie.libs import ops  # noqa

from prettytable import PrettyTable

config = configparser.ConfigParser()
config.read("config.ini")

inventory_path = config.get("inventory", "path")
group_name = config.get("inventory", "group_name")
tacacs_user = config.get("credential", "PYATS_USERNAME")
tacacs_password = config.get("credential", "PYATS_PASSWORD")

testbed = create_testbed(inventory_path, group_name,
                         tacacs_user, tacacs_password)

sw1 = testbed.devices['fspipswi001']
#sw1 = testbed.devices["tstipswi001"]
#sw2 = testbed.devices["tstipswi002"]


# Conenct to the device
sw1.connect()
abstract = Lookup.from_device(sw1)
intf = abstract.ops.interface.interface.Interface(sw1)
intf.learn()
intf.info

tabel = PrettyTable(['name', 'desc', 'operstatus'])

for name, prop in intf.info.items():
    if "description" in prop.keys():
        tabel.add_row([name, prop["description"], prop["oper_status"]])
    else:
        tabel.add_row([name, "---", prop["oper_status"]])

print(tabel)

# sw2.connect()

# Learn the vlans using Genie model
#vlans = device.parse("show vlan")

# Print out VLAN ids and names.
#print("Here are the vlans from device {}".format(device.name))
# for key, details in vlans["vlans"].items():
#  Print details on vlans
#    if 'vlan_id' in details.keys():
##        print("VLAN ID {} with name {}".format(details["vlan_id"], details["name"]))
# else:
#        print("VLAN {} have no key vlan_id".format(key))
# device.disconnect()

#ansible_inventory = get_ansibel_inventory(inventory_path)
