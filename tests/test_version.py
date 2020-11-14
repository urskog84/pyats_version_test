#!/bin/env python

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
                desierd_ver = '03.06.07.E'
            elif platform == 'Catalyst L3 Switch':
                desierd_ver = '03.06.08E'
            elif platform == 'C2960':
                desierd_ver = '15.0(2)SE11'
            else:
                desierd_ver = 'Uknown platform'

            if version_long:
                smaller_tabular = []
                if desierd_ver == version_long:
                    mega_dict[device]['version_long'] = version_long
                    mega_dict[device]['check_ver'] = desierd_ver
                    mega_dict[device]['platform'] = platform
                    smaller_tabular.append(device)
                    smaller_tabular.append(platform)
                    smaller_tabular.append(version_long)
                    smaller_tabular.append(desierd_ver)
                    smaller_tabular.append('Passed')
                else:
                    mega_dict[device]['version_long'] = version_long
                    mega_dict[device]['check_ver'] = desierd_ver
                    mega_dict[device]['platform'] = platform
                    smaller_tabular.append(device)
                    smaller_tabular.append(platform)
                    smaller_tabular.append(version_long)
                    smaller_tabular.append(desierd_ver)
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

        mega_tabular.append(['-'*len(smaller_tabular)])

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
            logout = dev.execute("show log | exclude Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec")
            logout = logout.split("Log Buffer")[0]
            self.logging_server[dev.name] = logout
    
    @ aetest.test
    def check_logging_server(self):
        mega_dict = {}
        mega_tabular = []
        for device, logging_server in self.logging_server.items():
            mega_dict[device] = {}
            smaller_tabular = []
            if re.search("Logging to 192.168.1.3", logging_server):
                mega_dict[device]['logging_server'] = True
                smaller_tabular.append(device)
                smaller_tabular.append('Passed')
            else: 
                mega_dict[device]['logging_server'] = False
                smaller_tabular.append(device)
                smaller_tabular.append('Failed')
            mega_tabular.append(smaller_tabular)
        
        mega_tabular.append(['--','--','--'])

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


# Testcase name: VTP_status_check
class VTP_status_check(aetest.Testcase):
    """ check vtp proprtys """

    @ aetest.test
    def learn_vtp(self):
        """ collect test data from command show vtp status """

        self.vtp = {}
        for device in self.parent.parameters['dev']:
            log.info(banner("Gathering VTP Information from {}".format(
                device.name
            )))
            try:
                vtp = device.parse("show vtp status")
            except:
                self.failed("No output off 'show vtp status")
            self.vtp[device.name] = vtp['vtp']

    @ aetest.test
    def check_vtp(self):
        desired_version = '1'
        mega_dict = {}
        mega_tabular = []
        for device, vtp in self.vtp.items():
            mega_dict[device] = {}
            if device[-1] == '1':  # Last char of devicename is 1
                desired_mode = "server"
            else:
                desired_mode = "client"
            smaller_tabular = []
            if (vtp['version'] == desired_version) and (vtp['operating_mode'] == desired_mode):
                mega_dict[device]['vtp'] = vtp
                mega_dict[device]['desired_mode'] = desired_mode
                mega_dict[device]['desired_version'] = desired_version
                smaller_tabular.append(device)
                smaller_tabular.append(vtp['version'])
                smaller_tabular.append(vtp['operating_mode'])
                smaller_tabular.append('Passed')
            else:
                mega_dict[device]['vtp'] = vtp
                mega_dict[device]['desired_mode'] = desired_mode
                mega_dict[device]['desired_version'] = desired_version
                smaller_tabular.append(device)
                smaller_tabular.append(vtp['version'])
                smaller_tabular.append(vtp['operating_mode'])
                smaller_tabular.append('Failed')
            mega_tabular.append(smaller_tabular)

        mega_tabular.append(['--','--'])

        log.info(tabulate(mega_tabular,
                          headers=['Device', 'version',
                                   'operating_mode', 'Passed/Failed'],
                          tablefmt='orgtbl'
                          ))

        for device in mega_dict:
            for vtp in mega_dict[device]:
                if not mega_dict[device]['vtp']['version'] == mega_dict[device]['desired_version']:
                    self.failed("{d}: is runing vtp version {ver} running: should be {d_ver} ".format(
                        d=device, ver=mega_dict[device]['vtp']['version'], d_ver=desired_version))

                elif not mega_dict[device]['vtp']['operating_mode'] == mega_dict[device]['desired_mode']:
                    self.failed("{d}: is runing vtp mode {mod} running: should be {d_mode} ".format(
                        d=device, mod=mega_dict[device]['vtp']['operating_mode'], d_mode=desired_mode))
        self.passed("All devices correct vtp settings")



# Testcase name : NTP_status_check
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
            smaller_tabular = []
            if ntp:
                ntp_server_count = len(ntp['peer'].keys())
                first_ntp = list(ntp['peer'].keys())[0] 
                second_ntp= list(ntp['peer'].keys())[1]
 
                smaller_tabular = []
                # ['216.239.35.8', '193.228.143.12']

                if (ntp_server_count == 2) and (first_ntp == '194.58.203.20') and (second_ntp == '91.209.0.20'):
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
        
        mega_tabular.append(['-','-','-'])

        log.info(tabulate(mega_tabular,
                          headers=['Device', 'tot',
                                   'first_ntp', 'second_ntp', 'Passed/Failed'],
                          tablefmt='orgtbl'
                          ))

        for dev in mega_dict:
            for logging_server in mega_dict[dev]:
                if not mega_dict[dev]['ntp']:
                    self.failed("{d}: have not correct ntp server".format(
                        d=dev, ))
        self.passed("All devices have the correct ntp server")

# Testcase name : VTP_status_check


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
