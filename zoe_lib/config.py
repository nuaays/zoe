# Copyright (c) 2015, Daniele Venzano
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Configuration parsing."""

import logging

from zoe_lib.configargparse import ArgumentParser, Namespace

logging.getLogger('kazoo').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('docker').setLevel(logging.INFO)

_CONFIG_PATHS = [
    'zoe.conf',
    '/etc/zoe/zoe.conf'
]

_CONF = None


def get_conf() -> Namespace:
    """Returns the conf singleton."""
    return _CONF


def load_configuration(test_conf=None):
    """Parses command line arguments."""
    global _CONF
    if test_conf is None:
        argparser = ArgumentParser(description="Zoe - Container Analytics as a Service",
                                   default_config_files=_CONFIG_PATHS,
                                   auto_env_var_prefix="ZOE_",
                                   args_for_setting_config_path=["--config"],
                                   args_for_writing_out_config_file=["--write-config"])

        # Common options
        argparser.add_argument('--debug', action='store_true', help='Enable debug output')
        argparser.add_argument('--swarm', help='Swarm/Docker API endpoint (ex.: zk://zk1:2181,zk2:2181 or http://swarm:2380)', default='http://localhost:2375')
        argparser.add_argument('--deployment-name', help='name of this Zoe deployment', default='prod')

        argparser.add_argument('--dbname', help='DB name', default='zoe')
        argparser.add_argument('--dbuser', help='DB user', default='zoe')
        argparser.add_argument('--dbpass', help='DB password', default='')
        argparser.add_argument('--dbhost', help='DB hostname', default='localhost')
        argparser.add_argument('--dbport', type=int, help='DB port', default=5432)

        # Master options
        argparser.add_argument('--api-listen-uri', help='ZMQ API listen address', default='tcp://*:4850')
        argparser.add_argument('--influxdb-dbname', help='Name of the InfluxDB database to use for storing metrics', default='zoe')
        argparser.add_argument('--influxdb-url', help='URL of the InfluxDB service (ex. http://localhost:8086)', default='http://localhost:8086')
        argparser.add_argument('--influxdb-enable', action="store_true", help='Enable metric output toward influxDB')
        argparser.add_argument('--gelf-address', help='Enable Docker GELF log output to this destination (ex. udp://1.2.3.4:1234)', default='')
        argparser.add_argument('--workspace-base-path', help='Path where user workspaces will be created by Zoe. Must be visible at this path on all Swarm hosts.', default='/mnt/zoe-workspaces')
        argparser.add_argument('--overlay-network-name', help='Name of the Swarm overlay network Zoe should use', default='zoe')

        # API options
        argparser.add_argument('--listen-address', type=str, help='Address to listen to for incoming connections', default="0.0.0.0")
        argparser.add_argument('--listen-port', type=int, help='Port to listen to for incoming connections', default=5001)
        argparser.add_argument('--master-url', help='URL of the Zoe master process', default='tcp://127.0.0.1:4850')

        # API auth options
        argparser.add_argument('--auth-type', help='Authentication type (text or ldap)', default='text')

        argparser.add_argument('--auth-file', help='Path to the CSV file containing user,pass,role lines for text authentication', default='zoepass.csv')

        argparser.add_argument('--ldap-server-uri', help='LDAP server to use for authentication', default='ldap://localhost')
        argparser.add_argument('--ldap-base-dn', help='LDAP base DN for users', default='ou=something,dc=any,dc=local')
        argparser.add_argument('--ldap-admin-gid', type=int, help='LDAP group ID for admins', default=5000)
        argparser.add_argument('--ldap-user-gid', type=int, help='LDAP group ID for users', default=5001)
        argparser.add_argument('--ldap-guest-gid', type=int, help='LDAP group ID for guests', default=5002)

        opts = argparser.parse_args()
        if opts.debug:
            argparser.print_values()

        _CONF = opts
    else:
        _CONF = test_conf
