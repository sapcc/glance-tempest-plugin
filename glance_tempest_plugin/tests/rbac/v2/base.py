# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest import clients
from tempest import config
from tempest.lib import auth
from tempest.lib.common.utils import data_utils

CONF = config.CONF


class ImageV2RbacBaseTests(object):

    identity_version = 'v3'

    @classmethod
    def skip_checks(cls):
        super().skip_checks()
        if not CONF.image_feature_enabled.enforce_scope:
            raise cls.skipException("enforce_scope is not enabled for "
                                    "glance, skipping RBAC tests")

    def do_request(self, method, expected_status=200, client=None, **payload):
        if not client:
            client = self.client
        if isinstance(expected_status, type(Exception)):
            self.assertRaises(expected_status,
                              getattr(client, method),
                              **payload)
        else:
            response = getattr(client, method)(**payload)
            self.assertEqual(response.response.status, expected_status)
            return response

    def setup_user_client(self, project_id=None):
        """Set up project user with its own client.

        This is useful for testing protection of resources in separate
        projects.

        Returns a client object and the user's ID.
        """
        user_dict = {
            'name': data_utils.rand_name('user'),
            'password': data_utils.rand_password(),
        }
        user_id = self.os_system_admin.users_v3_client.create_user(
            **user_dict)['user']['id']
        self.addCleanup(self.os_system_admin.users_v3_client.delete_user,
                        user_id)

        if not project_id:
            project_id = self.os_system_admin.projects_client.create_project(
                data_utils.rand_name())['project']['id']
            self.addCleanup(
                self.os_system_admin.projects_client.delete_project,
                project_id)

        member_role_id = self.os_system_admin.roles_v3_client.list_roles(
            name='member')['roles'][0]['id']
        self.os_system_admin.roles_v3_client.create_user_role_on_project(
            project_id, user_id, member_role_id)
        creds = auth.KeystoneV3Credentials(
            user_id=user_id,
            password=user_dict['password'],
            project_id=project_id)
        auth_provider = clients.get_auth_provider(creds)
        creds = auth_provider.fill_credentials()
        client = clients.Manager(credentials=creds)
        return client
