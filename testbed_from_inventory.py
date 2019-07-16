import json
import pprint
import os.path
from sh import Command
from genie.conf import Genie
from genie.libs import ops # noqa
from pyats.topology import Testbed, Device

if 'PYATS_USERNAME' in os.environ:
    tacacs_user = os.environ.get('PYATS_USERNAME')
else:
    raise AssertionError('you are missing environmen variabel')

if 'PYATS_PASSWORD' in os.environ:
    tacacs_password = os.environ.get('PYATS_PASSWORD')
else:
    raise AssertionError('you are missing environmen variabel')
    

def get_ansibel_inventory(inventory_path):
    """Return full Ansible object `inventory_path`."""
    
    if not os.path.exists(inventory_path):
        raise AssertionError('File %r do not exist, check your path to the Ansible inventory file' % inventory_path)
    
    ansible_inventory = Command('ansible-inventory')
    json_inventory = json.loads(
        ansible_inventory('-i', inventory_path, '--list').stdout)
    return json_inventory

def get_hosts_from(inventory_path, group_name):
    """Return list of hosts from `group_name` in Ansible `inventory_path`."""
    json_inventory = get_ansibel_inventory(inventory_path)

    if group_name not in json_inventory:
        raise AssertionError('Group %r not found.' % group_name)

    hosts = []
    if 'hosts' in json_inventory[group_name]:
        return json_inventory[group_name]['hosts']
    else:
        children = json_inventory[group_name]['children']
        for child in children:
            if 'hosts' in json_inventory[child]:
                for host in json_inventory[child]['hosts']:
                    if host not in hosts:
                        hosts.append(host)
            else:
                grandchildren = json_inventory[child]['children']
                for grandchild in grandchildren:
                    if 'hosts' not in json_inventory[grandchild]:
                        raise AssertionError('Group nesting cap exceeded.')
                    for host in json_inventory[grandchild]['hosts']:
                        if host not in hosts:
                            hosts.append(host)
        return hosts

def get_hostvars(host, inventory):
    """Retruns host vars from a specific host"""
    host_vars = inventory['_meta']['hostvars'][host]
    return host_vars
    
    
def create_testbed(inventory_path, group_name):
    """Returns a pyats tesbed object"""
    hosts = get_hosts_from(inventory_path, group_name)
    testbed_obj = Testbed('my_testbed')
    
    device_list = []
    for host in hosts:
        host_vars = get_hostvars(host, 
                                 get_ansibel_inventory(inventory_path)
                                 )
        dev = Device(host,
                    type =  'ios',
                    os =  'ios',
                    tacacs={
                        'username': os.environ.get('PYATS_USERNAME'),
                        'login_prompt': 'login:',
                        'password_prompt': 'Password:',
                    },
                    passwords={
                        'tacacs': os.environ.get('PYATS_PASSWORD'),
                        'enable': 'lab',
                        'line': 'lab',
                    },
                    connections =  {
                        'ssh': { 
                            'protocol' : 'ssh',
                            'ip': host_vars['mgmt_ip']
                            }
                    })
        dev.os =  "ios"
        testbed_obj.add_device(dev)
        
    testbed = Genie.init(testbed_obj)    
    return testbed