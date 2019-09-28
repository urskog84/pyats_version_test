
#!/bin/env python

from testbed_from_inventory import create_testbed
import logging
from tabulate import tabulate
from ats import aetest
from ats.log.utils import banner
from genie.conf import Genie
from genie.abstract import Lookup
from genie.libs import ops  # noqa
import configparser
import re
import copy

# Get your logger for your script
log = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read("config.ini")

inventory_path = config.get("inventory", "path")
group_name = config.get("inventory", "group_name")

tacacs_user = config.get("credential", "PYATS_USERNAME")
tacacs_password = config.get("credential", "PYATS_PASSWORD")


###################################################################
#                  COMMON SETUP SECTION                           #
###################################################################


class common_setup(aetest.CommonSetup):
    """ Common Setup section """

    # CommonSetup have subsection.
    # You can have 1 to as many subsection as wanted

    # Connect to each device in the testbed
    @aetest.subsection
    def connect(self, testbed):
        genie_testbed = Genie.init(testbed)
        self.parent.parameters['testbed'] = genie_testbed
        device_list = []
        for device in genie_testbed.devices.values():
            log.info(banner(
                "Connect to device '{d}'".format(d=device.name)))
            try:
                device.connect()
            except Exception as e:
                self.failed("Failed to establish connection to '{}'".format(
                    device.name))

            device_list.append(device)

        # Pass list of devices the to testcases
        self.parent.parameters.update(dev=device_list)


###################################################################
 #                    TESTCASES SECTION                           #
##################################################################

# Testcase name : interface_check_check
class interface_config_check(aetest.Testcase):
    """ This is user Testcases section """

    # Collection interface data
    @ aetest.test
    def show_interfaces_switchspor(self):
        """ Collect struted data from show interfaces switchport """

        self.all_interfaces = {}
        for dev in self.parent.parameters['dev']:
            log.info(banner("Gathering Interface Information from {}".format(
                dev.name)))
            switchport = dev.parse("show interfaces switchport")
            self.all_interfaces[dev.name] = switchport

    # check_CRC
    @ aetest.test
    def check_CRC(self):

        desierd_config = {'switchport_enable': True,
                          'switchport_mode': 'trunk',
                          'operational_mode': 'down',
                          'encapsulation': {'administrative_encapsulation': 'dot1q',
                                            'native_vlan': '1'},
                          'negotiation_of_trunk': True,
                          'access_vlan': '1',
                          'native_vlan_tagging': True,
                          'private_vlan': {'native_vlan_tagging': True, 'encapsulation': 'dot1q'},
                          'trunk_vlans': '5-8',
                          'pruning_vlans': '2-1001',
                          'capture_mode': False,
                          'capture_vlans': 'all',
                          'protected': False,
                          'unknown_unicast_blocked': False,
                          'unknown_multicast_blocked': False
                          }
        mega_dict = {}
        mega_tabular = []
        for device, interfaces in self.switchport.items():
            mega_dict[device] = {}
            interfaces_org = interface.copy()
            for interface, props in interfaces_org.items():
                if not props["switchport_mode"] == 'static_access':
                    interfaces.pop(interface)
                    
                
                if 
                counters = props.get('counters')
                if counters:
                    smaller_tabular = []
                    if 'in_crc_errors' in counters:
                        mega_dict[device][name] = counters['in_crc_errors']
                        smaller_tabular.append(device)
                        smaller_tabular.append(name)
                        smaller_tabular.append(str(counters['in_crc_errors']))
                        if counters['in_crc_errors']:
                            smaller_tabular.append('Failed')
                        else:
                            smaller_tabular.append('Passed')
                    else:
                        mega_dict[device][name] = None
                        smaller_tabular.append(device)
                        smaller_tabular.append(name)
                        smaller_tabular.append('N/A')
                        smaller_tabular.append('N/A')
                mega_tabular.append(smaller_tabular)

        mega_tabular.append(['-'*sum(len(i) for i in smaller_tabular)])

        log.info(tabulate(mega_tabular,
                          headers=['Device', 'Interface',
                                   'CRC Errors Counter',
                                   'Passed/Failed'],
                          tablefmt='orgtbl'))

        for dev in mega_dict:
            for intf in mega_dict[dev]:
                if mega_dict[dev][intf]:
                    self.failed("{d}: {name} CRC ERRORS: {e}".format(
                        d=dev, name=intf, e=mega_dict[dev][intf]))

        self.passed("All devices' interfaces CRC ERRORS Count is: 'Zero'")

    # description
    @ aetest.test
    def check_interface_description(self):

        mega_dict = {}
        mega_tabular = []
        for device, ints in self.all_interfaces.items():

            # Filter out
            filter_interfaces = dict()
            for (interface_name, props) in ints.items():
                if re.match(r"\w+Ethernet(\d\/\d\/\d+|\d\/\d+)", interface_name):
                    filter_interfaces[interface_name] = props

            mega_dict[device] = {}
            for name, props in filter_interfaces.items():
                smaller_tabular = []
                if "description" in props.keys():
                    description = props["description"]
                    oper_status = props["oper_status"]
                    mega_dict[device][name] = description
                    smaller_tabular.append(device)
                    smaller_tabular.append(name)
                    smaller_tabular.append(description)
                    smaller_tabular.append(oper_status)
                    if description == 'CAPWAP':
                        smaller_tabular.append('Passed')
                    if description == 'DP':
                        smaller_tabular.append('Passed')
                    if re.match(r"(To\s)((\w{3}(ipswi|ipsws|cis|nrkp|nrks|nrkt)\d+)|(nrkdist01))", description):
                        smaller_tabular.append('Passed')
                    else:
                        smaller_tabular.append('Faild')
                else:
                    mega_dict[device][name] = None
                    smaller_tabular.append(device)
                    smaller_tabular.append(name)
                    smaller_tabular.append('N/A')
                    smaller_tabular.append(oper_status)
                    smaller_tabular.append('Passed')
                mega_tabular.append(smaller_tabular)

        mega_tabular.append(['-'*sum(len(i) for i in smaller_tabular)])

        log.info(tabulate(mega_tabular,
                          headers=['Device', 'Interface',
                                   'description',
                                   'oper_status',
                                   'Passed/Failed'],
                          tablefmt='orgtbl'))

        for dev in mega_dict:
            for intf in mega_dict[dev]:
                if mega_dict[dev][intf]:
                    self.failed("{d}: {name} Description: {e}".format(
                        d=dev, name=intf, e=mega_dict[dev][intf]))

        self.passed("All devices' interfaces Description: 'Correct'")


# #####################################################################
# ####                       COMMON CLEANUP SECTION                 ###
# #####################################################################


# This is how to create a CommonCleanup
# You can have 0 , or 1 CommonCleanup.
# CommonCleanup can be named whatever you want :)
class common_cleanup(aetest.CommonCleanup):
    """ Common Cleanup for Sample Test """

    # CommonCleanup follow exactly the same rule as CommonSetup regarding
    # subsection
    # You can have 1 to as many subsections as wanted
    # here is an example of 1 subsection

    @aetest.subsection
    def clean_everything(self):
        """ Common Cleanup Subsection """
        log.info("Aetest Common Cleanup ")


if __name__ == '__main__':  # pragma: no cover
    aetest.main()
