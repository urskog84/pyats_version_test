from testbed_from_inventory import create_testbed


inventory_path = "/git/awx-site/inventorys/staging/inventory.ini"
group_name = "site-switches"
testbed = create_testbed(inventory_path, group_name)

sw1 = testbed.devices["tstipswi001"]
sw2 = testbed.devices["tstipswi002"]


# Conenct to the device
sw1.connect()
sw2.connect()

# Learn the vlans using Genie model
#vlans = device.parse("show vlan")

# Print out VLAN ids and names.
#print("Here are the vlans from device {}".format(device.name))
#for key, details in vlans["vlans"].items():
    #  Print details on vlans
#    if 'vlan_id' in details.keys():
##        print("VLAN ID {} with name {}".format(details["vlan_id"], details["name"]))
##    else:
#        print("VLAN {} have no key vlan_id".format(key))
#device.disconnect()

#ansible_inventory = get_ansibel_inventory(inventory_path)
 