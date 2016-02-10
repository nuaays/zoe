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

from zoe_lib.exceptions import ZoeRestAPIException


def authorization_error():
    raise ZoeRestAPIException('You do not have necessary permissions for the resource', 403)


def is_authorized(user, obj, action):
    # Zoeadmin and admins can do anything they want
    if user.role == "admin":
        return True
    # Anyone can work on his own objects
    if obj.owner == user:
        return True
    authorization_error()


QUOTA_MAX_APPS_GUESTS = 1
QUOTA_MAX_MEM_GUESTS = 16 * (2**30)
QUOTA_MAX_PROCS_GUESTS = 5


def check_quota(user, state):
    if user.role == "guest" and state.user_has_active_executions(user.id):
            raise ZoeRestAPIException('Quota exceeded', 402)
    return True
