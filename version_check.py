#!/bin/env python

# To get a logger for the script
import logging

# To build the table at the end
from tabulate import tabulate

# Needed for aetest script
from ats import aetest
from ats.log.utils import banner

# Genie Imports
from genie.conf import Genie
from genie.abstract import Lookup

# import the genie libs
from genie.libs import ops  # noqa

# Get your logger for your script
log = logging.getLogger(__name__)

from testbed_from_inventory import create_testbed


inventory_path = "/git/awx-site/inventorys/staging/inventory.ini"
group_name = "site-switches"
#testbed = create_testbed(inventory_path, group_name)

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
        genie_testbed =  create_testbed(inventory_path, group_name)
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

# Testcase : version
class IOS_version_ceck(aetest.Testcase):
    
    @ aetest.test
    def learn_version(self):
        
        self.version_info = {}
        for ios_device in self.parent.parameters['dev']:
            log.info(banner("Gathering Version Information from {}".format(
                ios_device.name
                )))
            version_info = ios_device.parse("show version")
            self.version_info[ios_device.name] = version_info['version']

    
    @ aetest.test
    def check_version(self):
        
        mega_dict = {}
        mega_tabular = []
        for device, version in self.version_info.items():
            mega_dict[device] = {}
            version_long = version['version']
            platform = version['platform']

            if platform == 'Catalyst 4500 L3 Switch ':
                check_ver = '03.06.07.E'
            elif platform == 'Catalyst L3 Switch':
                check_ver = '03.06.08E'
            else:
                check_ver = 'Uknown platform'
            
            if version_long:
                smaller_tabular = []    
                if check_ver == version_long:
                    mega_dict[device]['version_long'] = version_long
                    mega_dict[device]['check_ver'] = check_ver
                    mega_dict[device]['platform'] = platform
                    smaller_tabular.append(device)
                    smaller_tabular.append(platform)
                    smaller_tabular.append(version_long)
                    smaller_tabular.append(check_ver)
                    smaller_tabular.append('Passed')
                else:
                    mega_dict[device]['version_long'] = version_long
                    mega_dict[device]['check_ver'] = check_ver
                    mega_dict[device]['platform'] = platform
                    smaller_tabular.append(device)
                    smaller_tabular.append(platform)
                    smaller_tabular.append(version_long)
                    smaller_tabular.append(check_ver)
                    smaller_tabular.append('Failed')
            mega_tabular.append(smaller_tabular)

        mega_tabular.append(['-'*sum(len(i) for i in smaller_tabular)])

        log.info(tabulate(mega_tabular,
                          headers=['Device', 'platform', 'version', 'check_ver', 'Passed/Failed'],
                          tablefmt='orgtbl'
                          ))
        
        for device in mega_dict:
            for version in mega_dict[device]:

                if not mega_dict[device]['version_long'] == mega_dict[device]['check_ver'] :
                    self.failed("switch {d} is on platform {p}. current running version is {current_version} shoud be: {check_ver}".format(
                        d=device, current_version=mega_dict[device]['version_long'], check_ver=mega_dict[device]['check_ver'], p=mega_dict[device]['platform']))

        self.passed("All devices have correct Version")


class LLDP_check(aetest.Testcase):
    
    @ aetest.test
    def learn_lldp(self):
        
        self.lldp = {}
        for ios_device in self.parent.parameters['dev']:
            log.info(banner("Gathering LLDP Information from {}".format(
                ios_device.name
                )))
            try:
                lldp = ios_device.parse("show lldp")
            except:
                self.failed("No output off 'show lldp commnad")
            self.lldp[ios_device.name] = lldp
        
            
    @ aetest.test
    def check_lldp(self):
        mega_dict = {}
        mega_tabular = []
        for device, lldp in self.lldp.items():
            mega_dict[device] = {}
            if lldp:
                status = lldp['status']
                enabled = lldp['enabled']
    
                smaller_tabular = []
                if enabled:
                    mega_dict[device]['lldp'] = lldp
                    smaller_tabular.append(device)
                    smaller_tabular.append(status)
                    smaller_tabular.append(enabled)
                    smaller_tabular.append('Passed')
                else:
                    mega_dict[device]['lldp'] = lldp
                    smaller_tabular.append(device)
                    smaller_tabular.append(status)
                    smaller_tabular.append(enabled)
                    smaller_tabular.append('Failed')
            mega_tabular.append(smaller_tabular)

    #    mega_tabular.append(['-'*sum(len(i) for i in smaller_tabular)])

        log.info(tabulate(mega_tabular,
                          headers=['Device', 'status', 'enabled', 'Passed/Failed'],
                          tablefmt='orgtbl'
                          ))
        
        for device in mega_dict:
            for lldp in mega_dict[device]:
                if not mega_dict[device]['lldp']:
                    self.failed("{d}: lldp is not enabeld shoud be: {check_ver}".format(
                        d=device, enabled=enabled, check_ver=enabled))

        self.passed("All devices have lldp enabeld")


# Testcase name : vxlan_consistency_check
class CRC_count_check(aetest.Testcase):
    """ This is user Testcases section """

    # First test section
    @ aetest.test
    def learn_interfaces(self):
        """ Sample test section. Only print """

        self.all_interfaces = {}
        for dev in self.parent.parameters['dev']:
            log.info(banner("Gathering Interface Information from {}".format(
                dev.name)))
            abstract = Lookup.from_device(dev)
            intf = abstract.ops.interface.interface.Interface(dev)
            intf.learn()
            self.all_interfaces[dev.name] = intf.info

    # Second test section
    @ aetest.test
    def check_CRC(self):

        mega_dict = {}
        mega_tabular = []
        for device, ints in self.all_interfaces.items():
            mega_dict[device] = {}
            for name, props in ints.items():
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
