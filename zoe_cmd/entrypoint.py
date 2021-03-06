# Copyright (c) 2016, Daniele Venzano
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

"""
This module contains the entrypoint for the commandline Zoe client
"""

import datetime
import json
import logging
import os
import sys
from argparse import ArgumentParser, Namespace, FileType, RawDescriptionHelpFormatter
from typing import Tuple

from zoe_cmd import utils
from zoe_lib.info import ZoeInfoAPI
from zoe_lib.services import ZoeServiceAPI
from zoe_lib.statistics import ZoeStatisticsAPI
from zoe_lib.exceptions import ZoeAPIException, InvalidApplicationDescription
from zoe_lib.executions import ZoeExecutionsAPI
from zoe_lib.applications import app_validate


def info_cmd(args_):
    """Queries the info endpoint."""
    info_api = ZoeInfoAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    info = info_api.info()
    print("Zoe version: ", info['version'])
    print("Zoe API version: ", info['api_version'])
    print("ZApp format version: ", info['application_format_version'])
    print("Deployment name: ", info['deployment_name'])


def app_validate_cmd(args):
    """Validate an application description."""
    app_descr = json.load(args.jsonfile)
    try:
        app_validate(app_descr)
    except InvalidApplicationDescription as e:
        print(e)
    else:
        print("Static validation OK")


def app_get_cmd(args):
    """Extract an application description from an execution."""
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    execution = exec_api.get(args.id)
    if execution is None:
        print("no such execution")
    else:
        json.dump(execution['description'], sys.stdout, sort_keys=True, indent=4)


def exec_list_cmd(args_):
    """List executions"""
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    data = exec_api.list()
    for e in data.values():
        print('Execution {} (User: {}, ID: {}): {}'.format(e['name'], e['user_id'], e['id'], e['status']))


def exec_start_cmd(args):
    """Submit an execution."""
    app_descr = json.load(args.jsonfile)
    app_validate(app_descr)
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    ret = exec_api.start(args.name, app_descr)
    print("Application scheduled successfully with ID {}, use the exec-get command to check its status".format(ret))


def exec_get_cmd(args):
    """Gather information about an execution."""
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    cont_api = ZoeServiceAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    execution = exec_api.get(args.id)
    if execution is None:
        print('Execution not found')
    else:
        print('Execution {} (ID: {})'.format(execution['name'], execution['id']))
        print('Status: {}'.format(execution['status']))
        if execution['status'] == 'error':
            print('Last error: {}'.format(execution['error_message']))
        print('Time submit: {}'.format(datetime.datetime.fromtimestamp(execution['time_submit'])))

        if execution['time_start'] is None:
            print('Time start: {}'.format('not yet'))
        else:
            print('Time start: {}'.format(datetime.datetime.fromtimestamp(execution['time_start'])))

        if execution['time_end'] is None:
            print('Time end: {}'.format('not yet'))
        else:
            print('Time end: {}'.format(datetime.datetime.fromtimestamp(execution['time_end'])))

        app = execution['description']
        print('Application name: {}'.format(app['name']))
        for c_id in execution['services']:
            service = cont_api.get(c_id)
            print('Service {} (ID: {})'.format(service['name'], service['id']))
            print(' - zoe status: {}'.format(service['status']))
            print(' - docker status: {}'.format(service['docker_status']))
            if service['docker_status'] == 'started':
                ip = service['ip_address']
                for port in service['description']['ports']:
                    print(' - {}: {}://{}:{}{}'.format(port['name'], port['protocol'], ip, port['port_number'], port['path']))


def exec_kill_cmd(args):
    """Kill an execution."""
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    exec_api.terminate(args.id)


def exec_rm_cmd(args):
    """Delete an execution and kill it if necessary."""
    exec_api = ZoeExecutionsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    exec_api.delete(args.id)


def logs_cmd(args):
    """Retrieves and streams the logs of a service."""
    service_api = ZoeServiceAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    try:
        for line in service_api.get_logs(args.service_id):
            if args.timestamps:
                print(line[0], line[1])
            else:
                print(line[1])
    except KeyboardInterrupt:
        print('CTRL-C detected, exiting...')


def stats_cmd(args_):
    """Prints statistics on Zoe internals."""
    stats_api = ZoeStatisticsAPI(utils.zoe_url(), utils.zoe_user(), utils.zoe_pass())
    sched = stats_api.scheduler()
    print('Scheduler queue length: {}'.format(sched['queue_length']))
    print('Termination threads count: {}'.format(sched['termination_threads_count']))

ENV_HELP_TEXT = '''To use this tool you need also to define three environment variables:
ZOE_URL: point to the URL of the Zoe Scheduler (ex.: http://localhost:5000/
ZOE_USER: the username used for authentication
ZOE_PASS: the password used for authentication'''


def process_arguments() -> Tuple[ArgumentParser, Namespace]:
    """Parse command line arguments."""
    parser = ArgumentParser(description="Zoe command-line client", epilog=ENV_HELP_TEXT, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('--debug', action='store_true', help='Enable debug output')

    subparser = parser.add_subparsers()

    argparser_info = subparser.add_parser('info', help="Queries the API for supported versions")
    argparser_info.set_defaults(func=info_cmd)

    argparser_app_validate = subparser.add_parser('app-validate', help='Validate an application description')
    argparser_app_validate.add_argument('jsonfile', type=FileType("r"), help='Application description')
    argparser_app_validate.set_defaults(func=app_validate_cmd)

    argparser_exec_start = subparser.add_parser('start', help="Start an application")
    argparser_exec_start.add_argument('name', help="Name of the execution")
    argparser_exec_start.add_argument('jsonfile', type=FileType("r"), help='Application description')
    argparser_exec_start.set_defaults(func=exec_start_cmd)

    argparser_app_list = subparser.add_parser('exec-ls', help="List all executions for the calling user")
    argparser_app_list.set_defaults(func=exec_list_cmd)

    argparser_execution_get = subparser.add_parser('exec-get', help="Get execution status")
    argparser_execution_get.add_argument('id', type=int, help="Execution id")
    argparser_execution_get.set_defaults(func=exec_get_cmd)

    argparser_app_get = subparser.add_parser('exec-app-get', help="Retrieve an already defined application description")
    argparser_app_get.add_argument('id', help='The ID of the application')
    argparser_app_get.set_defaults(func=app_get_cmd)

    argparser_execution_kill = subparser.add_parser('terminate', help="Terminates an execution")
    argparser_execution_kill.add_argument('id', type=int, help="Execution id")
    argparser_execution_kill.set_defaults(func=exec_kill_cmd)

    argparser_execution_kill = subparser.add_parser('exec-rm', help="Deletes an execution")
    argparser_execution_kill.add_argument('id', type=int, help="Execution id")
    argparser_execution_kill.set_defaults(func=exec_rm_cmd)

    argparser_logs = subparser.add_parser('logs', help="Streams the service logs")
    argparser_logs.add_argument('service_id', type=int, help="Service id")
    argparser_logs.add_argument('-t', '--timestamps', action='store_true', help="Prefix timestamps for each line")
    argparser_logs.set_defaults(func=logs_cmd)

    argparser_stats = subparser.add_parser('stats', help="Prints all available statistics")
    argparser_stats.set_defaults(func=stats_cmd)

    return parser, parser.parse_args()


def zoe():
    """Main entrypoint."""
    parser, args = process_arguments()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)

    if not hasattr(args, "func"):
        parser.print_help()
        return

    if 'ZOE_URL' not in os.environ or 'ZOE_USER' not in os.environ or 'ZOE_PASS' not in os.environ:
        parser.print_help()
        return

    try:
        args.func(args)
    except ZoeAPIException as e:
        print(e.message)
    sys.exit(0)
