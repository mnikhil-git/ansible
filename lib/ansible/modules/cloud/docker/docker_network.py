#!/usr/bin/python
#
# Copyright 2016 Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: docker_network
version_added: "2.2"
short_description: Manage Docker networks
description:
  - Create/remove Docker networks and connect containers to them.
  - Performs largely the same function as the "docker network" CLI subcommand.
options:
  name:
    description:
      - Name of the network to operate on.
    required: true
    aliases:
      - network_name

  connected:
    description:
      - List of container names or container IDs to connect to a network.
    aliases:
      - containers

  driver:
    description:
      - Specify the type of network. Docker provides bridge and overlay drivers, but 3rd party drivers can also be used.
    default: bridge

  driver_options:
    description:
      - Dictionary of network settings. Consult docker docs for valid options and values.

  force:
    description:
      - With state I(absent) forces disconnecting all containers from the
        network prior to deleting the network. With state I(present) will
        disconnect all containers, delete the network and re-create the
        network.  This option is required if you have changed the IPAM or
        driver options and want an existing network to be updated to use the
        new options.
    type: bool
    default: 'no'

  appends:
    description:
      - By default the connected list is canonical, meaning containers not on the list are removed from the network.
        Use C(appends) to leave existing containers connected.
    type: bool
    default: 'no'
    aliases:
      - incremental

  enable_ipv6:
    version_added: 2.8
    description:
      - Enable IPv6 networking.
    type: bool
    default: null
    required: false

  ipam_driver:
    description:
      - Specify an IPAM driver.

  ipam_options:
    description:
      - Dictionary of IPAM options.
      - Deprecated in 2.8, will be removed in 2.12. Use parameter C(ipam_config) instead. In Docker 1.10.0, IPAM
        options were introduced (see L(here,https://github.com/moby/moby/pull/17316)). This module parameter addresses
        the IPAM config not the newly introduced IPAM options.

  ipam_config:
    version_added: 2.8
    description:
      - List of IPAM config blocks. Consult
        L(Docker docs,https://docs.docker.com/compose/compose-file/compose-file-v2/#ipam) for valid options and values.
        Note that I(iprange) is spelled differently here (we use the notation from the Docker Python SDK).
    type: list
    default: null
    required: false
    suboptions:
      subnet:
        description:
          - IP subset in CIDR notation.
        type: str
      iprange:
        description:
          - IP address range in CIDR notation.
        type: str
      gateway:
        description:
          - IP gateway address.
        type: str
      aux_addresses:
        description:
          - Auxiliary IP addresses used by Network driver, as a mapping from hostname to IP.
        type: dict

  state:
    description:
      - I(absent) deletes the network. If a network has connected containers, it
        cannot be deleted. Use the C(force) option to disconnect all containers
        and delete the network.
      - I(present) creates the network, if it does not already exist with the
        specified parameters, and connects the list of containers provided via
        the connected parameter. Containers not on the list will be disconnected.
        An empty list will leave no containers connected to the network. Use the
        C(appends) option to leave existing containers connected. Use the C(force)
        options to force re-creation of the network.
    default: present
    choices:
      - absent
      - present

  internal:
    version_added: 2.8
    description:
      - Restrict external access to the network.
    type: bool
    default: null
    required: false

  scope:
    version_added: 2.8
    description:
      - Specify the network's scope.
    type: str
    default: null
    required: false
    choices:
      - local
      - global
      - swarm

  attachable:
    version_added: 2.8
    description:
      - If enabled, and the network is in the global scope, non-service containers on worker nodes will be able to connect to the network.
    type: bool
    default: null
    required: false

extends_documentation_fragment:
    - docker

author:
    - "Ben Keith (@keitwb)"
    - "Chris Houseknecht (@chouseknecht)"
    - "Dave Bendit (@DBendit)"

requirements:
    - "python >= 2.6"
    - "docker-py >= 1.10.0"
    - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
       module has been superseded by L(docker,https://pypi.org/project/docker/)
       (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
       For Python 2.6, C(docker-py) must be used. Otherwise, it is recommended to
       install the C(docker) Python module. Note that both modules should I(not)
       be installed at the same time. Also note that when both modules are installed
       and one of them is uninstalled, the other might no longer function and a
       reinstall of it is required."
    - "The docker server >= 1.10.0"
'''

EXAMPLES = '''
- name: Create a network
  docker_network:
    name: network_one

- name: Remove all but selected list of containers
  docker_network:
    name: network_one
    connected:
      - container_a
      - container_b
      - container_c

- name: Remove a single container
  docker_network:
    name: network_one
    connected: "{{ fulllist|difference(['container_a']) }}"

- name: Add a container to a network, leaving existing containers connected
  docker_network:
    name: network_one
    connected:
      - container_a
    appends: yes

- name: Create a network with driver options
  docker_network:
    name: network_two
    driver_options:
      com.docker.network.bridge.name: net2

- name: Create a network with custom IPAM config
  docker_network:
    name: network_three
    ipam_config:
      - subnet: 172.3.27.0/24
        gateway: 172.3.27.2
        iprange: 172.3.27.0/26
        aux_addresses:
          host1: 172.3.27.3
          host2: 172.3.27.4

- name: Create a network with IPv6 IPAM config
  docker_network:
    name: network_ipv6_one
    enable_ipv6: yes
    ipam_config:
      - subnet: fdd1:ac8c:0557:7ce1::/64

- name: Create a network with IPv6 and custom IPv4 IPAM config
  docker_network:
    name: network_ipv6_two
    enable_ipv6: yes
    ipam_config:
      - subnet: 172.4.27.0/24
      - subnet: fdd1:ac8c:0557:7ce2::/64

- name: Delete a network, disconnecting all containers
  docker_network:
    name: network_one
    state: absent
    force: yes
'''

RETURN = '''
facts:
    description: Network inspection results for the affected network.
    returned: success
    type: dict
    sample: {}
'''

import re

from distutils.version import LooseVersion

from ansible.module_utils.docker_common import (
    AnsibleDockerClient,
    DockerBaseClass,
    docker_version,
    DifferenceTracker,
)

try:
    from docker import utils
    from docker.errors import NotFound
    if LooseVersion(docker_version) >= LooseVersion('2.0.0'):
        from docker.types import IPAMPool, IPAMConfig
except Exception as dummy:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass


class TaskParameters(DockerBaseClass):
    def __init__(self, client):
        super(TaskParameters, self).__init__()
        self.client = client

        self.network_name = None
        self.connected = None
        self.driver = None
        self.driver_options = None
        self.ipam_driver = None
        self.ipam_options = None
        self.ipam_config = None
        self.appends = None
        self.force = None
        self.internal = None
        self.debug = None
        self.enable_ipv6 = None
        self.scope = None
        self.attachable = None

        for key, value in client.module.params.items():
            setattr(self, key, value)


def container_names_in_network(network):
    return [c['Name'] for c in network['Containers'].values()] if network['Containers'] else []


CIDR_IPV4 = re.compile(r'^([0-9]{1,3}\.){3}[0-9]{1,3}/([0-9]|[1-2][0-9]|3[0-2])$')
CIDR_IPV6 = re.compile(r'^[0-9a-fA-F:]+/([0-9]|[1-9][0-9]|1[0-2][0-9])$')


def get_ip_version(cidr):
    """Gets the IP version of a CIDR string

    :param cidr: Valid CIDR
    :type cidr: str
    :return: ``ipv4`` or ``ipv6``
    :rtype: str
    :raises ValueError: If ``cidr`` is not a valid CIDR
    """
    if CIDR_IPV4.match(cidr):
        return 'ipv4'
    elif CIDR_IPV6.match(cidr):
        return 'ipv6'
    raise ValueError('"{0}" is not a valid CIDR'.format(cidr))


def get_driver_options(driver_options):
    # TODO: Move this and the same from docker_prune.py to docker_common.py
    result = dict()
    if driver_options is not None:
        for k, v in driver_options.items():
            # Go doesn't like 'True' or 'False'
            if v is True:
                v = 'true'
            elif v is False:
                v = 'false'
            else:
                v = str(v)
            result[str(k)] = v
    return result


class DockerNetworkManager(object):

    def _get_minimal_versions(self):
        # TODO: Move this and the same from docker_container.py to docker_common.py
        self.option_minimal_versions = dict()
        for option, data in self.client.module.argument_spec.items():
            self.option_minimal_versions[option] = dict()
        self.option_minimal_versions.update(dict(
            scope=dict(docker_py_version='2.6.0', docker_api_version='1.30'),
            attachable=dict(docker_py_version='2.0.0', docker_api_version='1.26'),
        ))

        for option, data in self.option_minimal_versions.items():
            # Test whether option is supported, and store result
            support_docker_py = True
            support_docker_api = True
            if 'docker_py_version' in data:
                support_docker_py = self.client.docker_py_version >= LooseVersion(data['docker_py_version'])
            if 'docker_api_version' in data:
                support_docker_api = self.client.docker_api_version >= LooseVersion(data['docker_api_version'])
            data['supported'] = support_docker_py and support_docker_api
            # Fail if option is not supported but used
            if not data['supported']:
                # Test whether option is specified
                if 'detect_usage' in data:
                    used = data['detect_usage']()
                else:
                    used = self.client.module.params.get(option) is not None
                    if used and 'default' in self.client.module.argument_spec[option]:
                        used = self.client.module.params[option] != self.client.module.argument_spec[option]['default']
                if used:
                    # If the option is used, compose error message.
                    if 'usage_msg' in data:
                        usg = data['usage_msg']
                    else:
                        usg = 'set %s option' % (option, )
                    if not support_docker_api:
                        msg = 'docker API version is %s. Minimum version required is %s to %s.'
                        msg = msg % (self.client.docker_api_version_str, data['docker_api_version'], usg)
                    elif not support_docker_py:
                        if LooseVersion(data['docker_py_version']) < LooseVersion('2.0.0'):
                            msg = ("docker-py version is %s. Minimum version required is %s to %s. "
                                   "Consider switching to the 'docker' package if you do not require Python 2.6 support.")
                        elif self.client.docker_py_version < LooseVersion('2.0.0'):
                            msg = ("docker-py version is %s. Minimum version required is %s to %s. "
                                   "You have to switch to the Python 'docker' package. First uninstall 'docker-py' before "
                                   "installing 'docker' to avoid a broken installation.")
                        else:
                            msg = "docker version is %s. Minimum version required is %s to %s."
                        msg = msg % (docker_version, data['docker_py_version'], usg)
                    else:
                        # should not happen
                        msg = 'Cannot %s with your configuration.' % (usg, )
                    self.client.fail(msg)

    def __init__(self, client):
        self.client = client
        self.parameters = TaskParameters(client)
        self.check_mode = self.client.check_mode
        self.results = {
            u'changed': False,
            u'actions': []
        }
        self.diff = self.client.module._diff
        self.diff_tracker = DifferenceTracker()
        self.diff_result = dict()

        self._get_minimal_versions()

        self.existing_network = self.get_existing_network()

        if not self.parameters.connected and self.existing_network:
            self.parameters.connected = container_names_in_network(self.existing_network)

        if (self.parameters.ipam_options['subnet'] or self.parameters.ipam_options['iprange'] or
                self.parameters.ipam_options['gateway'] or self.parameters.ipam_options['aux_addresses']):
            self.parameters.ipam_config = [self.parameters.ipam_options]

        if self.parameters.driver_options:
            self.parameters.driver_options = get_driver_options(self.parameters.driver_options)

        state = self.parameters.state
        if state == 'present':
            self.present()
        elif state == 'absent':
            self.absent()

        if self.diff or self.check_mode or self.parameters.debug:
            if self.diff:
                self.diff_result['before'], self.diff_result['after'] = self.diff_tracker.get_before_after()
            self.results['diff'] = self.diff_result

    def get_existing_network(self):
        try:
            return self.client.inspect_network(self.parameters.network_name)
        except NotFound:
            return None

    def has_different_config(self, net):
        '''
        Evaluates an existing network and returns a tuple containing a boolean
        indicating if the configuration is different and a list of differences.

        :param net: the inspection output for an existing network
        :return: (bool, list)
        '''
        differences = DifferenceTracker()
        if self.parameters.driver and self.parameters.driver != net['Driver']:
            differences.add('driver',
                            parameter=self.parameters.driver,
                            active=net['Driver'])
        if self.parameters.driver_options:
            if not net.get('Options'):
                differences.add('driver_options',
                                parameter=self.parameters.driver_options,
                                active=net.get('Options'))
            else:
                for key, value in self.parameters.driver_options.items():
                    if not (key in net['Options']) or value != net['Options'][key]:
                        differences.add('driver_options.%s' % key,
                                        parameter=value,
                                        active=net['Options'].get(key))

        if self.parameters.ipam_driver:
            if not net.get('IPAM') or net['IPAM']['Driver'] != self.parameters.ipam_driver:
                differences.add('ipam_driver',
                                parameter=self.parameters.ipam_driver,
                                active=net.get('IPAM'))

        if self.parameters.ipam_config is not None and self.parameters.ipam_config:
            if not net.get('IPAM') or not net['IPAM']['Config']:
                differences.add('ipam_config',
                                parameter=self.parameters.ipam_config,
                                active=net.get('IPAM', {}).get('Config'))
            else:
                for idx, ipam_config in enumerate(self.parameters.ipam_config):
                    net_config = dict()
                    try:
                        ip_version = get_ip_version(ipam_config['subnet'])
                        for net_ipam_config in net['IPAM']['Config']:
                            if ip_version == get_ip_version(net_ipam_config['Subnet']):
                                net_config = net_ipam_config
                    except ValueError as e:
                        self.client.fail(str(e))

                    for key, value in ipam_config.items():
                        if value is None:
                            # due to recursive argument_spec, all keys are always present
                            # (but have default value None if not specified)
                            continue
                        camelkey = None
                        for net_key in net_config:
                            if key == net_key.lower():
                                camelkey = net_key
                                break
                        if not camelkey or net_config.get(camelkey) != value:
                            differences.add('ipam_config[%s].%s' % (idx, key),
                                            parameter=value,
                                            active=net_config.get(camelkey) if camelkey else None)

        if self.parameters.enable_ipv6 is not None and self.parameters.enable_ipv6 != net.get('EnableIPv6', False):
            differences.add('enable_ipv6',
                            parameter=self.parameters.enable_ipv6,
                            active=net.get('EnableIPv6', False))

        if self.parameters.internal is not None and self.parameters.internal != net.get('Internal', False):
            differences.add('internal',
                            parameter=self.parameters.internal,
                            active=net.get('Internal'))

        if self.parameters.scope is not None and self.parameters.scope != net.get('Scope'):
            differences.add('scope',
                            parameter=self.parameters.scope,
                            active=net.get('Scope'))

        if self.parameters.attachable is not None and self.parameters.attachable != net.get('Attachable', False):
            differences.add('attachable',
                            parameter=self.parameters.attachable,
                            active=net.get('Attachable'))

        return not differences.empty, differences

    def create_network(self):
        if not self.existing_network:
            params = dict(
                driver=self.parameters.driver,
                options=self.parameters.driver_options,
            )

            ipam_pools = []
            if self.parameters.ipam_config:
                for ipam_pool in self.parameters.ipam_config:
                    if LooseVersion(docker_version) >= LooseVersion('2.0.0'):
                        ipam_pools.append(IPAMPool(**ipam_pool))
                    else:
                        ipam_pools.append(utils.create_ipam_pool(**ipam_pool))

            if self.parameters.ipam_driver or ipam_pools:
                # Only add ipam parameter if a driver was specified or if IPAM parameters
                # were specified. Leaving this parameter away can significantly speed up
                # creation; on my machine creation with this option needs ~15 seconds,
                # and without just a few seconds.
                if LooseVersion(docker_version) >= LooseVersion('2.0.0'):
                    params['ipam'] = IPAMConfig(driver=self.parameters.ipam_driver,
                                                pool_configs=ipam_pools)
                else:
                    params['ipam'] = utils.create_ipam_config(driver=self.parameters.ipam_driver,
                                                              pool_configs=ipam_pools)

            if self.parameters.enable_ipv6 is not None:
                params['enable_ipv6'] = self.parameters.enable_ipv6
            if self.parameters.internal is not None:
                params['internal'] = self.parameters.internal
            if self.parameters.scope is not None:
                params['scope'] = self.parameters.scope
            if self.parameters.attachable is not None:
                params['attachable'] = self.parameters.attachable

            if not self.check_mode:
                resp = self.client.create_network(self.parameters.network_name, **params)

                self.existing_network = self.client.inspect_network(resp['Id'])
            self.results['actions'].append("Created network %s with driver %s" % (self.parameters.network_name, self.parameters.driver))
            self.results['changed'] = True

    def remove_network(self):
        if self.existing_network:
            self.disconnect_all_containers()
            if not self.check_mode:
                self.client.remove_network(self.parameters.network_name)
            self.results['actions'].append("Removed network %s" % (self.parameters.network_name,))
            self.results['changed'] = True

    def is_container_connected(self, container_name):
        return container_name in container_names_in_network(self.existing_network)

    def connect_containers(self):
        for name in self.parameters.connected:
            if not self.is_container_connected(name):
                if not self.check_mode:
                    self.client.connect_container_to_network(name, self.parameters.network_name)
                self.results['actions'].append("Connected container %s" % (name,))
                self.results['changed'] = True
                self.diff_tracker.add('connected.{0}'.format(name),
                                      parameter=True,
                                      active=False)

    def disconnect_missing(self):
        if not self.existing_network:
            return
        containers = self.existing_network['Containers']
        if not containers:
            return
        for c in containers.values():
            name = c['Name']
            if name not in self.parameters.connected:
                self.disconnect_container(name)

    def disconnect_all_containers(self):
        containers = self.client.inspect_network(self.parameters.network_name)['Containers']
        if not containers:
            return
        for cont in containers.values():
            self.disconnect_container(cont['Name'])

    def disconnect_container(self, container_name):
        if not self.check_mode:
            self.client.disconnect_container_from_network(container_name, self.parameters.network_name)
        self.results['actions'].append("Disconnected container %s" % (container_name,))
        self.results['changed'] = True
        self.diff_tracker.add('connected.{0}'.format(container_name),
                              parameter=False,
                              active=True)

    def present(self):
        different = False
        differences = DifferenceTracker()
        if self.existing_network:
            different, differences = self.has_different_config(self.existing_network)

        self.diff_tracker.add('exists', parameter=True, active=self.existing_network is not None)
        if self.parameters.force or different:
            self.remove_network()
            self.existing_network = None

        self.create_network()
        self.connect_containers()
        if not self.parameters.appends:
            self.disconnect_missing()

        if self.diff or self.check_mode or self.parameters.debug:
            self.diff_result['differences'] = differences.get_legacy_docker_diffs()
            self.diff_tracker.merge(differences)

        if not self.check_mode and not self.parameters.debug:
            self.results.pop('actions')

        self.results['ansible_facts'] = {u'docker_network': self.get_existing_network()}

    def absent(self):
        self.diff_tracker.add('exists', parameter=False, active=self.existing_network is not None)
        self.remove_network()


def main():
    argument_spec = dict(
        network_name=dict(type='str', required=True, aliases=['name']),
        connected=dict(type='list', default=[], aliases=['containers'], elements='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        driver=dict(type='str', default='bridge'),
        driver_options=dict(type='dict', default={}),
        force=dict(type='bool', default=False),
        appends=dict(type='bool', default=False, aliases=['incremental']),
        ipam_driver=dict(type='str'),
        ipam_options=dict(type='dict', default={}, removed_in_version='2.12', options=dict(
            subnet=dict(type='str'),
            iprange=dict(type='str'),
            gateway=dict(type='str'),
            aux_addresses=dict(type='dict'),
        )),
        ipam_config=dict(type='list', elements='dict', options=dict(
            subnet=dict(type='str'),
            iprange=dict(type='str'),
            gateway=dict(type='str'),
            aux_addresses=dict(type='dict'),
        )),
        enable_ipv6=dict(type='bool'),
        internal=dict(type='bool'),
        debug=dict(type='bool', default=False),
        scope=dict(type='str', choices=['local', 'global', 'swarm']),
        attachable=dict(type='bool'),
    )

    mutually_exclusive = [
        ('ipam_config', 'ipam_options')
    ]

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        supports_check_mode=True,
        min_docker_version='1.10.0',
        min_docker_api_version='1.22'
        # "The docker server >= 1.10.0"
    )

    cm = DockerNetworkManager(client)
    client.module.exit_json(**cm.results)


if __name__ == '__main__':
    main()
