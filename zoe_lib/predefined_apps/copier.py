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

from zoe_lib.predefined_frameworks.utils import copier_service


empty = {
    'host_path': 'CHANGEME',  # the path containing what to copy
    'cont_path': 'CHANGEME',  # the file or directory to copy from or to host_path
    'readonly': False
}


def copier_app(src_volume=empty, src_path='', dst_volume=empty, dst_path=''):
    """
    :type src_volume: dict
    :type src_path: str
    :type dst_volume: dict
    :type dst_path: str
    :rtype: dict
    """
    app = {
        'name': 'copier',
        'version': 1,
        'will_end': True,
        'priority': 512,
        'requires_binary': False,
        'services': [
            copier_service(src_volume, src_path, dst_volume, dst_path)
        ]
    }
    return app
