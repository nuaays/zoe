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

from zoe_lib.configargparse import ArgumentParser, Namespace

config_paths = [
    'zoe-scheduler.conf',
    '/etc/zoe/zoe-scheduler.conf'
]

_conf = None


def load_configuration(test_conf=None):
    global _conf
    if test_conf is None:
        argparser = ArgumentParser(description="Zoe Scheduler - Container Analytics as a Service scheduling component",
                                   default_config_files=config_paths,
                                   auto_env_var_prefix="ZOE_SCHEDULER_",
                                   args_for_setting_config_path=["--config"],
                                   args_for_writing_out_config_file=["--write-config"])
        argparser.add_argument('--debug', action='store_true', help='Enable debug output')
        argparser.add_argument('--swarm', help='Swarm/Docker API endpoint (ex.: zk://zk1:2181,zk2:2181 or http://swarm:2380)', default='http://localhost:2375')
        argparser.add_argument('--private-registry', help='Docker private registry address (ex.: 10.0.0.1:5000)', default='10.0.0.1:5000')
        argparser.add_argument('--state-dir', help='Directory where state checkpoints are saved', default='/var/lib/zoe')
        argparser.add_argument('--listen-address', help='REST API listen address', default='0.0.0.0')
        argparser.add_argument('--listen-port', help='REST API listen port', default='5000')
        argparser.add_argument('--zoeadmin-password', help='Password used to login as the master Zoe administrator', default='changeme')

        opts = argparser.parse_args()
        if opts.debug:
            argparser.print_values()
        _conf = opts
    else:
        _conf = test_conf


def get_conf() -> Namespace:
    return _conf
