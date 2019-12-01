
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

##################################################################
#                    TESTCASES SECTION                           #
##################################################################


class dot1x_interface_config(aetest.Testcase):

    @ aetest.test
    def gather_interface_data(self):
        """gather switchport data"""
        self.interface_list = {}
        for device in self.parent.parameters['dev']:
            log.info(
                banner(f"Gather output of show interfaces switchport from {device.name}"))
            switchports = device.parse("show interfaces switchport")
        self.interfaces = {}
        for device in self.parent.parameters['dev']:
            log.info(
                banner(f"Gather output of show interfaces from {device.name}"))
            interfaces = device.parse("show interfaces")

        tmp_list = {}
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
                    intf_obj[intf].update(
                        voice_vlan=switchports[intf]['voice_vlan'])
                else:
                    intf_obj[intf].update(voice_vlan=None)

                tmp_list.update(intf_obj)
            self.interface_list[device.name] = tmp_list

    @ aetest.test
    def check_dot1x_config(self):

        mega_dict = {}
        mega_tabular = []
        for device, intf in self.interface_list.items():
            mega_dict[device] = {}
            for intf_name, props in intf.items():
                mega_dict[device][intf_name] = {}
                smaller_tabular = []
                # Standard port
                if props['description'] is None and props['access_vlan'] == "200":
                    mega_dict[device][intf_name]['Faild'] = False
                    smaller_tabular.append(device)
                    smaller_tabular.append(intf_name)
                    smaller_tabular.append(props["description"])
                    smaller_tabular.append(props['access_vlan'])
                    smaller_tabular.append('Passed')
                # Accessport
                elif props['description'] == "CAPWAP" and props['access_vlan'] == "300":
                    mega_dict[device][intf_name]['Faild'] = False
                    smaller_tabular.append(device)
                    smaller_tabular.append(intf_name)
                    smaller_tabular.append(props["description"])
                    smaller_tabular.append(props['access_vlan'])
                    smaller_tabular.append('Passed')
                else:
                    mega_dict[device][intf_name]['Faild'] = True
                    smaller_tabular.append(device)
                    smaller_tabular.append(intf_name)
                    smaller_tabular.append(props["description"])
                    smaller_tabular.append(props['access_vlan'])
                    smaller_tabular.append('Faild')
                mega_tabular.append(smaller_tabular)

        mega_tabular.append(['--------', '---------  ', '---', '---', '---'])

        log.info(tabulate(mega_tabular,
                          headers=['Device', 'Interface',
                                   'description',
                                   'access_vlan',
                                   'Passed/Failed'],
                          tablefmt='orgtbl'))

        for device in mega_dict:
            for intf in mega_dict[device]:
                if mega_dict[device][intf]['Faild']:
                    self.failed(f"{device} interface {intf} in not compliant")

        self.passed("All devices' interfaces Description: 'Correct'")
