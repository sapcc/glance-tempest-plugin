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

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions

from glance_tempest_plugin.tests.rbac.v2 import base as rbac_base

CONF = config.CONF


class ImageV2RbacImageTest(rbac_base.RbacBaseTests):

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


class ProjectAdminTests(ImageV2RbacImageTest,
                        ImageV2RbacTemplate):

    credentials = ['project_admin', 'system_admin', 'project_alt_admin']

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
        image = self.do_request('create_image', expected_status=201,
                                **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

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

    def test_add_image_member(self):
        # Create a user with the member role in a separate project.
        other_project_member_client = self.setup_user_client()
        other_project_id = other_project_member_client.credentials.project_id

        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

        # Make sure the persona user can add image members to images they
        # create.
        self.do_request('create_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=200, image_id=image['id'],
                        member=other_project_id)

    def test_get_image_member(self):
        # Create a user with the member role in a separate project.
        project_one_client = self.setup_user_client()
        project_one_id = project_one_client.credentials.project_id

        # Create an image and share it with the other project.
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_member_client_v2.create_image_member(
            image['id'], member=project_one_id)
        self.do_request('show_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=200, image_id=image['id'],
                        member_id=project_one_id)

        # Create an image associated to a separate project and make project_one
        # a member.
        project_two_client = self.setup_user_client()
        image = project_two_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_two_client.image_member_client_v2.create_image_member(
            image['id'], member=project_one_id)
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404). We're a
        # project-admin in this case, which allows us to do this. Once
        # system-scope is implemented, project-admins shouldn't be allowed to
        # view image members for images outside their scope.
        self.do_request('show_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=200, image_id=image['id'],
                        member_id=project_one_id)

    def test_list_image_members(self):
        # Stash the project_id for this persona
        project_id = self.persona.credentials.project_id

        other_member_client = self.setup_user_client()
        other_member_project_id = other_member_client.credentials.project_id

        # Create an image as another user in a separate project and share that
        # image with this user and the other member.
        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        for p_id in [project_id, other_member_project_id]:
            project_client.image_member_client_v2.create_image_member(
                image['id'], member=p_id)
        resp = self.do_request('list_image_members',
                               client=self.persona.image_member_client_v2,
                               expected_status=200, image_id=image['id'])
        members = set(m['member_id'] for m in resp['members'])
        self.assertIn(project_id, members)
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and exclude members from other projects because the
        # image was shared with the other_member_project_id.
        self.assertIn(other_member_project_id, members)

    def test_update_image_member(self):
        project_client = self.setup_user_client()
        # Create a shared image in a separate project and share the with the
        # persona project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_member_client_v2.create_image_member(
            image['id'], member=self.persona.credentials.project_id)

        # Make sure the persona user can accept the image.
        self.do_request('update_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=200, image_id=image['id'],
                        member_id=self.persona.credentials.project_id,
                        status='accepted')

        # Make sure the persona user can reject the image.
        self.do_request('update_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=200, image_id=image['id'],
                        member_id=self.persona.credentials.project_id,
                        status='rejected')

        # Create another shared image in a separate project (not the persona
        # user's project).
        member_client = self.setup_user_client()
        member_project_id = member_client.credentials.project_id
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

        # Share the image with another project.
        project_client.image_member_client_v2.create_image_member(
            image['id'], member=member_project_id)

        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404). Project
        # users shouldn't be able to update shared status for shared images in
        # other projects, but here this is possible because the persona is the
        # almighty project-admin.
        self.do_request('update_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=200, image_id=image['id'],
                        member_id=member_project_id, status='accepted')

        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404). Project
        # users shouldn't be able to update shared status for shared images in
        # other projects, but here this is possible because the persona is the
        # almighty project-admin.
        self.do_request('update_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=200, image_id=image['id'],
                        member_id=member_project_id, status='rejected')

    def test_delete_image_member(self):
        # Create a user with authorization on another project.
        member_client = self.setup_user_client()
        member_project_id = member_client.credentials.project_id

        # Create a separate user with authorization on the persona project.
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)

        # Create an image in the persona project and share it with the member.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_member_client_v2.create_image_member(
            image['id'], member=member_project_id)

        # Make sure we, as the image owners, can remove membership to that
        # image.
        self.do_request('delete_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=204,
                        image_id=image['id'], member_id=member_project_id)

        # Create a new user with authorization on a separate project.
        project_client = self.setup_user_client()

        # Create an image in that project and share it with the member project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_member_client_v2.create_image_member(
            image['id'], member=member_project_id)

        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404). When
        # glance supports system-scope and updates the default policies
        # accordingly, project-admins shouldn't be able to delete image members
        # outside for images outside their project.
        self.do_request('delete_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=204, image_id=image['id'],
                        member_id=member_project_id)

    def test_deactivate_image(self):
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)
        file_contents = data_utils.random_bytes()
        image_data = six.BytesIO(file_contents)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        self.do_request('deactivate_image', expected_status=204,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        self.do_request('deactivate_image', expected_status=204,
                        image_id=image['id'])

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('deactivate_image', expected_status=204,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('deactivate_image', expected_status=204,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.admin_images_client.store_image_file(image['id'], image_data)
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 403)
        self.do_request('deactivate_image', expected_status=204,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.admin_images_client.store_image_file(image['id'], image_data)
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 403)
        self.do_request('deactivate_image', expected_status=204,
                        image_id=image['id'])

    def test_reactivate_image(self):
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)
        file_contents = data_utils.random_bytes()
        image_data = six.BytesIO(file_contents)

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        project_client.image_client_v2.deactivate_image(image['id'])
        self.do_request('reactivate_image', expected_status=204,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        project_client.image_client_v2.deactivate_image(image['id'])
        self.do_request('reactivate_image', expected_status=204,
                        image_id=image['id'])

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        project_client.image_client_v2.deactivate_image(image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('reactivate_image', expected_status=204,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        project_client.image_client_v2.deactivate_image(image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 404)
        self.do_request('reactivate_image', expected_status=204,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.admin_images_client.store_image_file(image['id'], image_data)
        self.admin_images_client.deactivate_image(image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 403)
        self.do_request('reactivate_image', expected_status=204,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.admin_images_client.store_image_file(image['id'], image_data)
        self.admin_images_client.deactivate_image(image['id'])
        # FIXME: This should eventually respect tenancy when glance supports
        # system-scope and fail with an appropriate error (e.g., 403)
        self.do_request('reactivate_image', expected_status=204,
                        image_id=image['id'])


class ProjectMemberTests(ImageV2RbacImageTest, ImageV2RbacTemplate):

    credentials = ['project_member', 'project_admin', 'system_admin',
                   'project_alt_admin']

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
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.do_request('delete_image', expected_status=exceptions.NotFound,
                        image_id=image['id'])
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

        image = self.client.create_image(
            **self.image(visibility='private'))
        self.do_request('delete_image', expected_status=204,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.do_request('delete_image', expected_status=exceptions.NotFound,
                        image_id=image['id'])
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

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
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

        image = self.client.create_image(
            **self.image(visibility='community'))
        self.do_request('delete_image', expected_status=204,
                        image_id=image['id'])

        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.do_request('delete_image', expected_status=exceptions.Forbidden,
                        image_id=image['id'])
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

    def test_add_image_member(self):
        member_client = self.setup_user_client()
        member_project_id = member_client.credentials.project_id
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])

        # As users with authorization on the project that owns the image, we
        # should be able to share that image with other projects.
        self.do_request('create_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=200, image_id=image['id'],
                        member=member_project_id)

    def test_get_image_member(self):
        member_client = self.setup_user_client()
        member_project_id = member_client.credentials.project_id
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_member_client_v2.create_image_member(
            image['id'], member=member_project_id)
        self.do_request('show_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=200, image_id=image['id'],
                        member_id=member_project_id)

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_member_client_v2.create_image_member(
            image['id'], member=member_project_id)
        # The user can't show the members for this image because they can't get
        # the image or pass the get_image policy, which is processed before
        # fetching the members.
        self.do_request('show_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=exceptions.NotFound,
                        image_id=image['id'], member_id=member_project_id)

    def test_list_image_members(self):
        # Stash the project_id for this persona.
        project_id = self.persona.credentials.project_id

        other_member_client = self.setup_user_client()
        other_member_project_id = other_member_client.credentials.project_id

        # Create an image as an other user in a separate project and share that
        # image with this user and the other member.
        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        for p_id in [project_id, other_member_project_id]:
            project_client.image_member_client_v2.create_image_member(
                image['id'], member=p_id)
        resp = self.do_request('list_image_members',
                               client=self.persona.image_member_client_v2,
                               expected_status=200, image_id=image['id'])
        members = set(m['member_id'] for m in resp['members'])
        # Make sure this user (persona) can't view members of an image other
        # than themselves.
        self.assertIn(project_id, members)
        self.assertNotIn(other_member_project_id, members)

    def test_update_image_member(self):
        # Create a new user with authorization on another project.
        other_project_client = self.setup_user_client()

        # Create a shared image in the other project and share the image with
        # the persona user's project.
        image = other_project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        other_project_client.image_member_client_v2.create_image_member(
            image['id'], member=self.persona.credentials.project_id)

        # Make sure the persona users can accept the image.
        self.do_request('update_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=200, image_id=image['id'],
                        member_id=self.persona.credentials.project_id,
                        status='accepted')

        # Make sure the persona users can reject the image.
        self.do_request('update_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=200, image_id=image['id'],
                        member_id=self.persona.credentials.project_id,
                        status='rejected')

        # Create a new user with authorization on another project to act as a
        # different member.
        member_client = self.setup_user_client()
        member_project_id = member_client.credentials.project_id

        # Create another image with the first project_client to share with the
        # new member user.
        image = other_project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        other_project_client.image_member_client_v2.create_image_member(
            image['id'], member=member_project_id)

        # Make sure the persona user can't accept images for other projects
        # they are not a member of.
        self.do_request('update_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=exceptions.NotFound,
                        image_id=image['id'], member_id=member_project_id,
                        status='accepted')

        # Make sure the persona user can't reject images for other projects
        # they are not a member of.
        self.do_request('update_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=exceptions.NotFound,
                        image_id=image['id'], member_id=member_project_id,
                        status='rejected')

    def test_delete_image_member(self):
        # Create a new user with authorization on a separate project.
        member_client = self.setup_user_client()
        member_project_id = member_client.credentials.project_id

        # Create an image in the persona user's project and share that image
        # with the new member user.
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_member_client_v2.create_image_member(
            image['id'], member=member_project_id)

        # Make sure the persona user can delete image members from images they
        # own.
        self.do_request('delete_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=204,
                        image_id=image['id'], member_id=member_project_id)

        project_client = self.setup_user_client()
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_member_client_v2.create_image_member(
            image['id'], member=member_project_id)

        # Make sure the persona user can't delete image members from images
        # outside their project.
        self.do_request('delete_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=exceptions.NotFound,
                        image_id=image['id'], member_id=member_project_id)

    def test_deactivate_image(self):
        # Create a new user with authorization on the persona user's project.
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)
        file_contents = data_utils.random_bytes()
        image_data = six.BytesIO(file_contents)

        # Create a private image in the persona user's project and make sure
        # the persona user can deactivate it.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        self.do_request('deactivate_image', expected_status=204,
                        image_id=image['id'])
        resp = self.client.show_image(image_id=image['id'])
        self.assertTrue(resp['status'] == 'deactivated')

        # Create a shared image in the persona user's project and make sure the
        # persona user can deactivate it.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        self.do_request('deactivate_image', expected_status=204,
                        image_id=image['id'])
        resp = self.client.show_image(image_id=image['id'])
        self.assertTrue(resp['status'] == 'deactivated')

        # Create a new user with authorization on a separate project.
        project_client = self.setup_user_client()

        # Create a private image in that new project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        # The user can't deactivate this image because they can't find it.
        self.do_request('deactivate_image',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'])

        # Create a shared image in the new project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        # The user can't deactivate this image because they can't find it.
        self.do_request('deactivate_image',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'])

        # Project users can't deactivate community images, only administrators
        # should be able to do this.
        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.admin_images_client.store_image_file(image['id'], image_data)
        self.do_request('deactivate_image',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        # Project users can't deactivate public images, only administrators
        # should be able to do this.
        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.admin_images_client.store_image_file(image['id'], image_data)
        self.do_request('deactivate_image',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

    def test_reactivate_image(self):
        # Create a new user with authorization on the persona user's project.
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)
        file_contents = data_utils.random_bytes()
        image_data = six.BytesIO(file_contents)

        # Create a private image within the persona user's project and make
        # sure we can reactivate it.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        project_client.image_client_v2.deactivate_image(image['id'])
        resp = self.client.show_image(image_id=image['id'])
        self.assertTrue(resp['status'] == 'deactivated')
        self.do_request('reactivate_image', expected_status=204,
                        image_id=image['id'])
        resp = self.client.show_image(image_id=image['id'])
        self.assertTrue(resp['status'] == 'active')

        # Create a shared image within the persona user's project and make sure
        # we can reactivate it.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        project_client.image_client_v2.deactivate_image(image['id'])
        resp = self.client.show_image(image_id=image['id'])
        self.assertTrue(resp['status'] == 'deactivated')
        self.do_request('reactivate_image', expected_status=204,
                        image_id=image['id'])
        resp = self.client.show_image(image_id=image['id'])
        self.assertTrue(resp['status'] == 'active')

        # Create a new user with authorization on a separate project.
        project_client = self.setup_user_client()

        # Create a private image in the separate project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        project_client.image_client_v2.deactivate_image(image['id'])
        # The user can't reactivate this image because they can't find it.
        self.do_request('reactivate_image',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        project_client.image_client_v2.deactivate_image(image['id'])
        # The user can't reactivate this image because they can't find it.
        self.do_request('reactivate_image',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'])

        # Only administrators can reactivate community images.
        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.admin_images_client.store_image_file(image['id'], image_data)
        self.admin_images_client.deactivate_image(image['id'])
        self.do_request('reactivate_image',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        # Only administrators can reactivate public images.
        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.admin_images_client.store_image_file(image['id'], image_data)
        self.admin_images_client.deactivate_image(image['id'])
        self.do_request('reactivate_image',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])


class ProjectReaderTests(ProjectMemberTests):

    credentials = ['project_reader', 'project_admin', 'system_admin',
                   'project_alt_admin']

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

    def test_add_image_member(self):
        # Create a new user with authorization on a separate project.
        member_client = self.setup_user_client()
        member_project_id = member_client.credentials.project_id

        # Create a new user with authorization on the persona user's project.
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)

        # Create a shared image and make sure we can't share the image with
        # other projects.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.do_request('create_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'],
                        member=member_project_id)

    def test_update_image_member(self):
        # Create a new user with authorization on a separate project.
        project_client = self.setup_user_client()

        # Create a shared image in the other project and add the persona user's
        # project as a member.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_member_client_v2.create_image_member(
            image['id'], member=self.persona.credentials.project_id)

        # Make sure the user can't accept the image.
        self.do_request('update_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'],
                        member_id=self.persona.credentials.project_id,
                        status='accepted')

        # Make sure the user can't reject the change.
        self.do_request('update_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'],
                        member_id=self.persona.credentials.project_id,
                        status='rejected')

        # Create a new user with authorization on a separate project.
        member_client = self.setup_user_client()
        member_project_id = member_client.credentials.project_id

        # Have the original project client create a new shared image and share
        # it with the new member project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_member_client_v2.create_image_member(
            image['id'], member=member_project_id)

        # Make sure the user can't accept images for project they have no
        # authorization to know about.
        self.do_request('update_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=exceptions.NotFound,
                        image_id=image['id'], member_id=member_project_id,
                        status='accepted')

        # Make sure the user can't reject images for project they have no
        # authorization to know about.
        self.do_request('update_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=exceptions.NotFound,
                        image_id=image['id'], member_id=member_project_id,
                        status='rejected')

    def test_delete_image_member(self):
        # Create a new user with authorization on a separate project.
        member_client = self.setup_user_client()
        member_project_id = member_client.credentials.project_id

        # Create a new user with authorization on the persona user's project.
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)

        # Create a shared image in the persona user's project and share it with
        # the member project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_member_client_v2.create_image_member(
            image['id'], member=member_project_id)

        # Make sure the user can't delete image members.
        self.do_request('delete_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'], member_id=member_project_id)

        # Create a new user with authorization on a separate project.
        project_client = self.setup_user_client()

        # Creata a shared image in that new project and share it with the
        # member project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_member_client_v2.create_image_member(
            image['id'], member=member_project_id)

        # Make sure the user can't delete image members from images they have
        # no authorization to know about.
        self.do_request('delete_image_member',
                        client=self.persona.image_member_client_v2,
                        expected_status=exceptions.NotFound,
                        image_id=image['id'], member_id=member_project_id)

    def test_deactivate_image(self):
        # Create a new user with authorization on the persona user's project.
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)
        file_contents = data_utils.random_bytes()
        image_data = six.BytesIO(file_contents)

        # Create a new private image in the persona user's project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)

        # Make sure they can't deactivate images, even in their own project.
        self.do_request('deactivate_image',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        # Create a new shared image in the persona user's project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)

        # Make sure they can't deactivate images, even in their own project.
        self.do_request('deactivate_image',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        # Create a new user with authorization on a separate project.
        project_client = self.setup_user_client()

        # Create a private image in the new project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)

        # The user can't deactivate this image because they can't find it.
        self.do_request('deactivate_image',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'])

        # Create a shared image in the new project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)

        # The user can't deactivate this image because they can't find it.
        self.do_request('deactivate_image',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'])

        # Only administrators can deactivate community images.
        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.admin_images_client.store_image_file(image['id'], image_data)
        self.do_request('deactivate_image',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        # Only administrators can deactivate public images.
        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.admin_images_client.store_image_file(image['id'], image_data)
        self.do_request('deactivate_image',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

    def test_reactivate_image(self):
        # Create a new user with authorization on the persona user's project.
        project_id = self.persona.credentials.project_id
        project_client = self.setup_user_client(project_id=project_id)
        file_contents = data_utils.random_bytes()
        image_data = six.BytesIO(file_contents)

        # Create a private image in the persona user's project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        project_client.image_client_v2.deactivate_image(image['id'])

        # Make sure the user can't reactivate private images, even in their own
        # project.
        self.do_request('reactivate_image',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        # Create a shared image in the persona user's project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        project_client.image_client_v2.deactivate_image(image['id'])

        # Make sure the user can't reactivate shared images, even in their own
        # project.
        self.do_request('reactivate_image',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        # Create a new user with authorization on a separate project.
        project_client = self.setup_user_client()

        # Create a private image in the new project.
        image = project_client.image_client_v2.create_image(
            **self.image(visibility='private'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        project_client.image_client_v2.deactivate_image(image['id'])

        # The user can't reactivate this image because they can't find it.
        self.do_request('reactivate_image',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'])

        image = project_client.image_client_v2.create_image(
            **self.image(visibility='shared'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        project_client.image_client_v2.store_image_file(image['id'],
                                                        image_data)
        project_client.image_client_v2.deactivate_image(image['id'])

        # The user can't reactivate this image because they can't find it.
        self.do_request('reactivate_image',
                        expected_status=exceptions.NotFound,
                        image_id=image['id'])

        # Create a community image.
        image = self.admin_images_client.create_image(
            **self.image(visibility='community'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.admin_images_client.store_image_file(image['id'], image_data)
        self.admin_images_client.deactivate_image(image['id'])

        # Make sure the user can't reactivate community images.
        self.do_request('reactivate_image',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])

        # Create a public image.
        image = self.admin_images_client.create_image(
            **self.image(visibility='public'))
        self.addCleanup(self.admin_images_client.delete_image, image['id'])
        self.admin_images_client.store_image_file(image['id'], image_data)
        self.admin_images_client.deactivate_image(image['id'])

        # Make sure the user can't reactivate public images.
        self.do_request('reactivate_image',
                        expected_status=exceptions.Forbidden,
                        image_id=image['id'])
