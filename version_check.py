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
        genie_testbed = create_testbed(
            inventory_path, group_name, tacacs_user, tacacs_password)
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
                          headers=['Device', 'platform', 'version',
                                   'check_ver', 'Passed/Failed'],
                          tablefmt='orgtbl'
                          ))

        for device in mega_dict:
            for version in mega_dict[device]:

                if not mega_dict[device]['version_long'] == mega_dict[device]['check_ver']:
                    self.failed("switch {d} is on platform {p}. current running version is {current_version} shoud be: {check_ver}".format(
                        d=device, current_version=mega_dict[device]['version_long'], check_ver=mega_dict[device]['check_ver'], p=mega_dict[device]['platform']))

        self.passed("All devices have correct Version")

class NTP_check(aetest.Testcase):
    @ aetest.test
    def lear_ntp(self):
        
        self.ntp = {}
        for device in self.parent.parameters['dev']:
            log.info(banner("Gathering NTP Information from {}".format(
                device.name
            )))
            try:
                ntp = device.parse("show ntp associations")
            except:
                self.failed("No output off 'show ntp associations")
            self.ntp[device.name] = ntp

    @ aetest.test
    def check_ntp(self):
        mega_dict = {}
        mega_tabular = []
        for device, ntp in self.ntp.items():
            mega_dict[device] = {}
            if ntp:
                ntp_server_count = len(ntp['peer'].keys())
                first_ntp = list(ntp['peer'].keys())[0] 
                second_ntp= list(ntp['peer'].keys())[1]

                smaller_tabular = []
                # ['216.239.35.8', '193.228.143.12']

                if (ntp_server_count == 2) and (first_ntp == '216.239.35.8') and (second_ntp == '193.228.143.12'):
                    mega_dict[device]['ntp'] = True
                    smaller_tabular.append(device)
                    smaller_tabular.append(ntp_server_count)
                    smaller_tabular.append(first_ntp)
                    smaller_tabular.append(second_ntp)
                    smaller_tabular.append('Passed')
                else:
                    mega_dict[device]['ntp'] = False
                    smaller_tabular.append(device)
                    smaller_tabular.append(ntp_server_count)
                    smaller_tabular.append(first_ntp)
                    smaller_tabular.append(second_ntp)
                    smaller_tabular.append('Failed')
            mega_tabular.append(smaller_tabular)
        
        log.info(tabulate(mega_tabular,
                          headers=['Device', 'total amount',
                                   'first_ntp', 'second_ntp', 'Passed/Failed'],
                          tablefmt='orgtbl'
                          ))

        for dev in mega_dict:
            for logging_server in mega_dict[dev]:
                if not mega_dict[dev]['ntp']:
                    self.failed("{d}: have not correct ntp server".format(
                        d=dev, ))
        self.passed("All devices have the correct ntp server")

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
                          headers=['Device', 'status',
                                   'enabled', 'Passed/Failed'],
                          tablefmt='orgtbl'
                          ))

        for device in mega_dict:
            for lldp in mega_dict[device]:
                if not mega_dict[device]['lldp']:
                    self.failed("{d}: lldp is not enabeld shoud be: {check_ver}".format(
                        d=device, enabled=enabled, check_ver=enabled))

        self.passed("All devices have lldp enabeld")

# Testcase name : logging_server
class logging_server(aetest.Testcase):
    """ This thest check syslog server """

    # Collection data from show log command
    @ aetest.test
    def show_log(self):

        self.logging_server = {}
        for dev in self.parent.parameters['dev']:
            log.info(banner("Gather log data from {}".format(dev.name)))
            logout = dev.execute("show log")
            logout = logout.split("Log Buffer")[0]
            self.logging_server[dev.name] = logout

    @ aetest.test
    def check_logging_server(self):
        mega_dict = {}
        mega_tabular = []
        for device, logging_server in self.logging_server.items():
            mega_dict[device] = {}
            smaller_tabular = []
            if re.search("Logging to 10.115.1.44", logging_server):
                mega_dict[device]['logging_server'] = True
                smaller_tabular.append(device)
                smaller_tabular.append('Passed')
            else: 
                mega_dict[device]['logging_server'] = False
                smaller_tabular.append(device)
                smaller_tabular.append('Failed')
            mega_tabular.append(smaller_tabular)

        mega_tabular.append(['-'*sum(len(i) for i in smaller_tabular)])

        log.info(tabulate(mega_tabular,
                          headers=['Device', 'Passed/Failed'],
                          tablefmt='orgtbl'
                          ))

        for dev in mega_dict:
            for logging_server in mega_dict[dev]:
                if not mega_dict[dev]['logging_server']:
                    self.failed("{d}: have not correct logging server".format(
                        d=dev, ))

        self.passed("All devices have the correct logging server")
        
# Testcase name : interface_check_check
class interface_check(aetest.Testcase):
    """ This is user Testcases section """

    # Collection interface data
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

    # check_CRC
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
