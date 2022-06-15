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
import abc

from tempest.api.image import base
from tempest import clients
from tempest import config
from tempest.lib import auth
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils

CONF = config.CONF


class RbacBaseTests(base.BaseV2ImageTest):

    identity_version = 'v3'

    @classmethod
    def skip_checks(cls):
        super().skip_checks()
        if not CONF.enforce_scope.glance:
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


def namespace(name, owner, visibility='private', protected=False):
    return {'namespace': name, 'visibility': visibility,
            'description': data_utils.arbitrary_string(),
            'display_name': name, 'owner': owner, 'protected': protected}


class RbacMetadefBase(RbacBaseTests):
    def create_namespaces(self):
        """Create private and public namespaces for different projects."""
        project_namespaces = []
        alt_namespaces = []
        for visibility in ['public', 'private']:
            project_ns = "%s_%s_%s" % (
                self.project_id,
                visibility,
                self.__class__.__name__)

            alt_ns = "%s_%s_%s" % (self.alt_project_id, visibility,
                                   self.__class__.__name__)

            project_namespace = \
                self.os_project_admin.namespaces_client.create_namespace(
                    **namespace(project_ns, self.project_id,
                                visibility=visibility))
            project_namespaces.append(project_namespace)
            self.addCleanup(
                test_utils.call_and_ignore_notfound_exc,
                self.os_project_admin.namespaces_client.delete_namespace,
                project_ns)

            alt_namespace = \
                self.os_project_admin.namespaces_client.create_namespace(
                    **namespace(alt_ns, self.alt_project_id,
                                visibility=visibility))
            alt_namespaces.append(alt_namespace)
            self.addCleanup(
                test_utils.call_and_ignore_notfound_exc,
                self.os_project_admin.namespaces_client.delete_namespace,
                alt_ns)

        return project_namespaces + alt_namespaces


class ImageV2RbacImageTest(RbacBaseTests):

    @classmethod
    def setup_clients(cls):
        super().setup_clients()
        cls.persona = getattr(cls, f'os_{cls.credentials[0]}')
        cls.client = cls.persona.image_client_v2
        # FIXME(lbragstad): This should use os_system_admin when glance
        # supports system scope.
        cls.admin_client = cls.os_project_admin
        cls.admin_images_client = cls.admin_client.image_client_v2

    @classmethod
    def setup_credentials(cls):
        super().setup_credentials()
        cls.os_primary = getattr(cls, f'os_{cls.credentials[0]}')

    def image(self, visibility=None):
        image = {}
        image['name'] = data_utils.rand_name('image')
        image['container_format'] = CONF.image.container_formats[0]
        image['disk_format'] = CONF.image.disk_formats[0]
        image['visibility'] = visibility if visibility else 'private'
        image['ramdisk_uuid'] = '00000000-1111-2222-3333-444455556666'
        return image


class ImageV2RbacTemplate(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def test_create_image(self):
        """Test add_image policy.

        This test must check:
          * whether the persona can create a private image
          * whether the persona can create a shared image
          * whether the persona can create a community image
          * whether the persona can create a public image
        """

    @abc.abstractmethod
    def test_get_image(self):
        """Test get_image policy.

        This test must check:
          * whether a persona can get a private image
          * whether a persona can get a shared image
          * whether a persona can get a community image
          * whether a persona can get a public image
        """

    @abc.abstractmethod
    def test_list_images(self):
        """Test get_images policy.

        This test must check:
          * whether the persona can list private images within their project
          * whether the persona can list shared images
          * whether the persona can list community images
          * whether the persona can list public images
        """

    @abc.abstractmethod
    def test_update_image(self):
        """Test modify_image policy.

        This test must check:
          * whether the persona can modify private images
          * whether the persona can modify shared images
          * whether the persona can modify community images
          * whether the persona can modify public images
        """

    @abc.abstractmethod
    def test_upload_image(self):
        """Test upload_image policy.

        This test must check:
          * whether the persona can upload private images
          * whether the persona can upload shared images
          * whether the persona can upload community images
          * whether the persona can upload public images
        """

    @abc.abstractmethod
    def test_download_image(self):
        """Test download_image policy.

        This test must check:
          * whether the persona can download private images
          * whether the persona can download shared images
          * whether the persona can download community images
          * whether the persona can download public images
        """

    @abc.abstractmethod
    def test_delete_image(self):
        """Test delete_image policy.

        This test must check:
          * whether the persona can delete a private image
          * whether the persona can delete a shared image
          * whether the persona can delete a community image
          * whether the persona can delete a public image
          * whether the persona can delete an image outside their project
        """

    @abc.abstractmethod
    def test_add_image_member(self):
        pass

    @abc.abstractmethod
    def test_get_image_member(self):
        pass

    @abc.abstractmethod
    def test_list_image_members(self):
        pass

    @abc.abstractmethod
    def test_update_image_member(self):
        pass

    @abc.abstractmethod
    def test_delete_image_member(self):
        pass

    @abc.abstractmethod
    def test_deactivate_image(self):
        pass

    @abc.abstractmethod
    def test_reactivate_image(self):
        pass
