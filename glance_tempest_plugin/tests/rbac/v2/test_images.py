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

import six

from tempest.api.image import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions

from glance_tempest_plugin.tests.rbac.v2 import base as rbac_base

CONF = config.CONF


class ImageV2RbacImageTest(rbac_base.ImageV2RbacBaseTests,
                           metaclass=abc.ABCMeta):

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

    @abc.abstractmethod
    def test_create_image(self):
        """Test add_image policy.

        This test must check:
          * whether the persona can create a private image
          * whether the persona can create a shared image
          * whether the persona can create a community image
          * whether the persona can create a public image
        """
        pass

    @abc.abstractmethod
    def test_get_image(self):
        """Test get_image policy.

        This test must check:
          * whether a persona can get a private image
          * whether a persona can get a shared image
          * whether a persona can get a community image
          * whether a persona can get a public image
        """
        pass

    @abc.abstractmethod
    def test_list_images(self):
        """Test get_images policy.

        This test must check:
          * whether the persona can list private images within their project
          * whether the persona can list shared images
          * whether the persona can list community images
          * whether the persona can list public images
        """
        pass

    @abc.abstractmethod
    def test_update_image(self):
        """Test modify_image policy.

        This test must check:
          * whether the persona can modify private images
          * whether the persona can modify shared images
          * whether the persona can modify community images
          * whether the persona can modify public images
        """
        pass

    @abc.abstractmethod
    def test_upload_image(self):
        """Test upload_image policy.

        This test must check:
          * whether the persona can upload private images
          * whether the persona can upload shared images
          * whether the persona can upload community images
          * whether the persona can upload public images
        """
        pass

    @abc.abstractmethod
    def test_download_image(self):
        """Test download_image policy.

        This test must check:
          * whether the persona can download private images
          * whether the persona can download shared images
          * whether the persona can download community images
          * whether the persona can download public images
        """
        pass

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
        pass


class ProjectAdminTests(ImageV2RbacImageTest, base.BaseV2ImageTest):

    credentials = ['project_admin', 'system_admin']

    def test_create_image(self):
        image = self.do_request('create_image', expected_status=201,
                                **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

        image = self.do_request('create_image', expected_status=201,
                                **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

        image = self.do_request('create_image', expected_status=201,
                                **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 403)
        self.do_request('create_image', expected_status=201,
                        **self.image(visibility='public'))

    def test_get_image(self):
        # Ensure users can get private images owned by their project.
        project_id = self.persona.credentials.project_id
        project_member = self.setup_user_client(project_id=project_id)
        image = project_member.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image', image_id=image['id'])

        image = project_member.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image', image_id=image['id'])

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('show_image', image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('show_image', image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('show_image', image_id=image['id'])

        project_id = self.persona.credentials.project_id
        self.admin_client.image_member_client_v2.create_image_member(
            image['id'], member=project_id)
        self.addCleanup(
            self.admin_client.image_member_client_v2.delete_image_member,
            image['id'], project_id)

        self.do_request('show_image', image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image', image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image', image_id=image['id'])

        self.do_request('show_image', expected_status=exceptions.NotFound,
                        image_id=data_utils.rand_uuid())

    def test_list_images(self):
        project_id = self.persona.credentials.project_id
        project_member = self.setup_user_client(project_id=project_id)
        project_client = self.setup_user_client()

        # Create a private image in the project
        private_image_in_project = project_member.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        private_image_in_project['id'])

        # Create a private image without an owner
        private_image_no_owner = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        private_image_no_owner['id'])

        # Create a private image in another project
        private_image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        private_image['id'])

        # Create a public image
        public_image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image,
                        public_image['id'])

        resp = self.do_request('list_images', expected_status=200)
        image_ids = set(image['id'] for image in resp['images'])

        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and only include images relevant to the project.
        self.assertIn(private_image_no_owner['id'], image_ids)
        self.assertIn(private_image['id'], image_ids)
        self.assertIn(public_image['id'], image_ids)
        self.assertIn(private_image_in_project['id'], image_ids)

        # Create a shared image in another project
        shared_image_1 = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        shared_image_2 = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image,
                        shared_image_1['id'])
        self.addCleanup(self.admin_images_client.delete_image,
                        shared_image_2['id'])

        # Share the image from the other project with the user's project
        project_id = self.persona.credentials.project_id
        self.admin_client.image_member_client_v2.create_image_member(
            shared_image_1['id'], member=project_id)
        self.addCleanup(
            self.admin_client.image_member_client_v2.delete_image_member,
            shared_image_1['id'], project_id)

        # List images and assert the shared image is not in the list of images
        # because it hasn't been accepted, yet.
        resp = self.do_request('list_images', expected_status=200)
        image_ids = set(image['id'] for image in resp['images'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and only include accepted images.
        self.assertIn(shared_image_1['id'], image_ids)
        self.assertIn(shared_image_2['id'], image_ids)

        # Accept the image and ensure it's returned in the list of images
        project_member.image_member_client_v2.update_image_member(
            shared_image_1['id'], project_id, status='accepted')
        resp = self.do_request('list_images', expected_status=200)
        image_ids = set(image['id'] for image in resp['images'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and only include accepted images.
        self.assertIn(shared_image_1['id'], image_ids)
        self.assertIn(shared_image_2['id'], image_ids)

    def test_update_image(self):
        image = self.client.create_image(**self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=200,
                        image_id=image['id'], patch=patch_body)

        image = self.client.create_image(**self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=200,
                        image_id=image['id'], patch=patch_body)

        image = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('update_image', expected_status=200,
                        image_id=image['id'], patch=patch_body)

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('update_image', expected_status=200,
                        image_id=image['id'], patch=patch_body)

        image = self.client.create_image(**self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=200,
                        image_id=image['id'], patch=patch_body)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('update_image', expected_status=200,
                        image_id=image['id'], patch=patch_body)

        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 403)
        self.do_request('update_image', expected_status=200,
                        image_id=image['id'], patch=patch_body)

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 403)
        self.do_request('update_image', expected_status=200,
                        image_id=image['id'], patch=patch_body)

    def test_upload_image(self):
        file_contents = data_utils.random_bytes()
        image_data = six.BytesIO(file_contents)

        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)

        # upload file for private image - pass
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file', expected_status=204,
                        image_id=image['id'], data=image_data)

        # upload file for shared image - pass
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file', expected_status=204,
                        image_id=image['id'], data=image_data)

        image = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('store_image_file', image_id=image['id'],
                        expected_status=204, data=image_data)

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('store_image_file', expected_status=204,
                        image_id=image['id'], data=image_data)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('store_image_file', expected_status=204,
                        image_id=image['id'], data=image_data)

        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('store_image_file', expected_status=204,
                        image_id=image['id'], data=image_data)

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('store_image_file', expected_status=204,
                        image_id=image['id'], data=image_data)

    def test_download_image(self):
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('show_image_file', expected_status=204,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('show_image_file', expected_status=204,
                        image_id=image['id'])

        project_client = self.setup_user_client()

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('show_image_file', expected_status=204,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('show_image_file', expected_status=204,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('show_image_file', expected_status=204,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image_file', expected_status=204,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image_file', expected_status=204,
                        image_id=image['id'])

    def test_delete_image(self):

        image = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('delete_image', expected_status=204,
                        image_id=image['id'])

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('delete_image', expected_status=204,
                        image_id=image['id'])

        image = self.client.create_image(
            **self.image(visibility='private'))
        self.do_request('delete_image', expected_status=204,
                        image_id=image['id'])

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('delete_image', expected_status=204,
                        image_id=image['id'])

        image = self.client.create_image(
            **self.image(visibility='shared'))
        self.do_request('delete_image', expected_status=204,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='community'))
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('delete_image', expected_status=204,
                        image_id=image['id'])

        image = self.client.create_image(
            **self.image(visibility='community'))
        self.do_request('delete_image', expected_status=204,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('delete_image', expected_status=204,
                        image_id=image['id'])


class ProjectMemberTests(ProjectAdminTests, base.BaseV2ImageTest):

    credentials = ['project_member', 'project_admin', 'system_admin']

    def test_create_image(self):
        image = self.do_request('create_image', expected_status=201,
                                **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

        image = self.do_request('create_image', expected_status=201,
                                **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

        image = self.do_request('create_image', expected_status=201,
                                **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

        self.do_request('create_image', expected_status=exceptions.Forbidden,
                        **self.image(visibility='public'))

    def test_get_image(self):
        # Ensure users can get private images owned by their project.
        project_id = self.persona.credentials.project_id
        project_member = self.setup_user_client(project_id=project_id)
        image = project_member.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image', image_id=image['id'])

        image = project_member.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image', image_id=image['id'])

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image', expected_status=exceptions.NotFound,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image', expected_status=exceptions.NotFound,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image', expected_status=exceptions.NotFound,
                        image_id=image['id'])

        project_id = self.persona.credentials.project_id
        self.admin_client.image_member_client_v2.create_image_member(
            image['id'], member=project_id)
        self.addCleanup(
            self.admin_client.image_member_client_v2.delete_image_member,
            image['id'], project_id)

        self.do_request('show_image', image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image', image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image', image_id=image['id'])

        self.do_request('show_image', expected_status=exceptions.NotFound,
                        image_id=data_utils.rand_uuid())

    def test_list_images(self):
        project_id = self.persona.credentials.project_id
        project_member = self.setup_user_client(project_id=project_id)
        project_client = self.setup_user_client()

        # Create a private image in the project
        private_image_in_project = project_member.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        private_image_in_project['id'])

        # Create a private image without an owner
        private_image_no_owner = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        private_image_no_owner['id'])

        # Create a private image in another project
        private_image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        private_image['id'])

        # Create a public image
        public_image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image,
                        public_image['id'])

        resp = self.do_request('list_images', expected_status=200)
        image_ids = set(image['id'] for image in resp['images'])

        self.assertNotIn(private_image_no_owner['id'], image_ids)
        self.assertNotIn(private_image['id'], image_ids)
        self.assertIn(public_image['id'], image_ids)
        self.assertIn(private_image_in_project['id'], image_ids)

        # Create a shared image in another project
        shared_image_1 = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        shared_image_2 = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image,
                        shared_image_1['id'])
        self.addCleanup(self.admin_images_client.delete_image,
                        shared_image_2['id'])

        # Share the image from the other project with the user's project
        project_id = self.persona.credentials.project_id
        self.admin_client.image_member_client_v2.create_image_member(
            shared_image_1['id'], member=project_id)
        self.addCleanup(
            self.admin_client.image_member_client_v2.delete_image_member,
            shared_image_1['id'], project_id)

        # List images and assert the shared image is not in the list of images
        # because it hasn't been accepted, yet.
        resp = self.do_request('list_images', expected_status=200)
        image_ids = set(image['id'] for image in resp['images'])
        self.assertNotIn(shared_image_1['id'], image_ids)
        self.assertNotIn(shared_image_2['id'], image_ids)

        # Accept the image and ensure it's returned in the list of images
        project_member.image_member_client_v2.update_image_member(
            shared_image_1['id'], project_id, status='accepted')
        resp = self.do_request('list_images', expected_status=200)
        image_ids = set(image['id'] for image in resp['images'])
        self.assertIn(shared_image_1['id'], image_ids)
        self.assertNotIn(shared_image_2['id'], image_ids)

    def test_update_image(self):
        image = self.client.create_image(**self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=200,
                        image_id=image['id'], patch=patch_body)

        image = self.client.create_image(**self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=200,
                        image_id=image['id'], patch=patch_body)

        image = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=exceptions.NotFound,
                        image_id=image['id'], patch=patch_body)

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=exceptions.NotFound,
                        image_id=image['id'], patch=patch_body)

        image = self.client.create_image(**self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=200,
                        image_id=image['id'], patch=patch_body)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=exceptions.NotFound,
                        image_id=image['id'], patch=patch_body)

        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'], patch=patch_body)

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'], patch=patch_body)

    def test_upload_image(self):
        file_contents = data_utils.random_bytes()
        image_data = six.BytesIO(file_contents)

        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)

        # upload file for private image - pass
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file', expected_status=204,
                        image_id=image['id'], data=image_data)

        # upload file for shared image - pass
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file', expected_status=204,
                        image_id=image['id'], data=image_data)

        image = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'], data=image_data)

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'], data=image_data)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'], data=image_data)

        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'], data=image_data)

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'], data=image_data)

    def test_download_image(self):
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('show_image_file', expected_status=204,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('show_image_file', expected_status=204,
                        image_id=image['id'])

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('show_image_file', expected_status=exceptions.NotFound,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('show_image_file', expected_status=exceptions.NotFound,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image_file', expected_status=exceptions.NotFound,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image_file', expected_status=204,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image_file', expected_status=204,
                        image_id=image['id'])

    def test_delete_image(self):

        image = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.do_request('delete_image', expected_status=exceptions.NotFound,
                        image_id=image['id'])

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.do_request('delete_image', expected_status=exceptions.NotFound,
                        image_id=image['id'])

        image = self.client.create_image(
            **self.image(visibility='private'))
        self.do_request('delete_image', expected_status=204,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.do_request('delete_image', expected_status=exceptions.NotFound,
                        image_id=image['id'])

        project_id = self.persona.credentials.project_id
        project_member = self.setup_user_client(project_id=project_id)
        image = project_member.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.do_request('delete_image', expected_status=204,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='community'))
        self.do_request('delete_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        image = self.client.create_image(
            **self.image(visibility='community'))
        self.do_request('delete_image', expected_status=204,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.do_request('delete_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'])


class ProjectReaderTests(ProjectMemberTests, base.BaseV2ImageTest):

    credentials = ['project_reader', 'project_admin', 'system_admin']

    def test_create_image(self):
        # Project readers can't create images.
        self.do_request('create_image', expected_status=exceptions.Forbidden,
                        **self.image(visibility='private'))

        self.do_request('create_image', expected_status=exceptions.Forbidden,
                        **self.image(visibility='shared'))

        self.do_request('create_image', expected_status=exceptions.Forbidden,
                        **self.image(visibility='community'))

        self.do_request('create_image', expected_status=exceptions.Forbidden,
                        **self.image(visibility='public'))

    def test_update_image(self):
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'], patch=patch_body)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'], patch=patch_body)

        image = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        # This fails because getting an image outside the user's project
        # returns a 404.
        self.do_request('update_image', expected_status=exceptions.NotFound,
                        image_id=image['id'], patch=patch_body)

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        # FIXME(lbragstad): This is different from the status code for
        # project-admininstrators because the database layer allows users with
        # the admin role the ability to view images outside their project, and
        # returns a 403 because it checks tenancy later. IMO, this return code
        # shouldn't be any different from project users.
        self.do_request('update_image', expected_status=exceptions.NotFound,
                        image_id=image['id'], patch=patch_body)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        # Same comment as above with updating private images for other
        # projects.
        self.do_request('update_image', expected_status=exceptions.NotFound,
                        image_id=image['id'], patch=patch_body)

        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'], patch=patch_body)

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        name = data_utils.rand_name('new-image-name')
        patch_body = [dict(replace='/name', value=name)]
        self.do_request('update_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'], patch=patch_body)

    def test_upload_image(self):
        file_contents = data_utils.random_bytes()
        image_data = six.BytesIO(file_contents)

        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'], data=image_data)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'], data=image_data)

        image = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'], data=image_data)

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'], data=image_data)

        # This fails because the user can't actually see the image since it's
        # not shared with them.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'], data=image_data)

        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'], data=image_data)

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('store_image_file',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'], data=image_data)

    def test_download_image(self):
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('show_image_file',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('show_image_file',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        project_client = self.setup_user_client()

        # Fail to download an image for another project because we can't find
        # it.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('show_image_file',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'])

        # Fail to download an image for another project because we can't find
        # it.
        image = self.admin_images_client.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image,
                        image['id'])
        self.do_request('show_image_file',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'])

        # Fail to download an image for another project because we can't find
        # it.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image_file',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image_file',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('show_image_file',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

    def test_delete_image(self):
        # Project readers can't delete images outside their project. This is
        # returned as an HTTP 404 instead of an HTTP 403 because they can't
        # find the image they're trying to delete.
        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('delete_image', expected_status=exceptions.NotFound,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('delete_image', expected_status=exceptions.NotFound,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('delete_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        # Project readers can't delete images inside their project, regardless
        # of the image state (private, shared, community, or public).
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('delete_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('delete_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('delete_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        # Project readers can't delete public images.
        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('delete_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'])
