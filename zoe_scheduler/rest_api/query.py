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

from werkzeug.exceptions import BadRequest
from flask_restful import Resource, request

from zoe_lib.exceptions import ZoeRestAPIException
from zoe_scheduler.state.manager import StateManager
from zoe_scheduler.platform_manager import PlatformManager
from zoe_scheduler.rest_api.utils import catch_exceptions
from zoe_scheduler.rest_api.auth.authentication import authenticate


class QueryAPI(Resource):
    """
    :type state: StateManager
    :type platform: PlatformManager
    """
    def __init__(self, **kwargs):
        self.state = kwargs['state']
        self.platform = kwargs['platform']

    @catch_exceptions
    def post(self):
        calling_user = authenticate(request, self.state)

        try:
            data = request.get_json()
        except BadRequest:
            raise ZoeRestAPIException('Error decoding JSON data')

        if 'what' not in data:
            raise ZoeRestAPIException('"what" is required in query object')

        what = data['what']
        if 'filters' not in data:
            filters = {}
        else:
            filters = data['filters']

        if not isinstance(filters, dict):
            raise ZoeRestAPIException('query filters should be a dictionary of {attribute: requested_value} entries')

        if not calling_user.can_see_non_owner_objects():
            filters['owner'] = calling_user

        if what == 'stats swarm':
            ret = self.platform.swarm_stats()
            return {'stats': ret.to_dict()}
        elif what == 'stats scheduler':
            ret = self.platform.scheduler_stats()
            return {'stats': ret.to_dict()}
        elif what == 'execution logs':
            pass  # TODO
        elif what == 'container logs':
            c_list = self.state.get('container', **filters)
            logs = self._get_container_logs(c_list)
            return logs
        elif what == 'container stats':
            c_list = self.state.get('container', **filters)
            stats = self._get_container_stats(c_list)
            return [s.to_dict() for s in stats]
        else:
            ret = self.state.get(what, **filters)
            return [o.to_dict(checkpoint=False) for o in ret]

    def _get_container_logs(self, c_list):
        logs = []
        for c in c_list:
            ret = self.platform.log_get(c.id)
            logs.append(ret)

        return logs

    def _get_container_stats(self, c_list):
        stats = []
        for c in c_list:
            s = self.platform.container_stats(c.id)
            stats.append(s)

        return stats
