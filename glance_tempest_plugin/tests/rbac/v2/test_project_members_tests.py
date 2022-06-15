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

import six

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions

from glance_tempest_plugin.tests.rbac.v2.base import ImageV2RbacImageTest
from glance_tempest_plugin.tests.rbac.v2.base import ImageV2RbacTemplate

CONF = config.CONF


class ProjectMemberTests(ImageV2RbacImageTest, ImageV2RbacTemplate):

    credentials = ['project_member', 'project_admin', 'system_admin',
                   'project_alt_admin']

    @decorators.idempotent_id('a71e7caf-2403-4fed-a4bf-9717949ecde2')
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

    @decorators.idempotent_id('2adf7202-7fc9-4a6e-b6dd-fb3d40365ccb')
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

    @decorators.idempotent_id('259d5578-410e-4b0f-bb2d-cb5b057bc696')
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

    @decorators.idempotent_id('13f8949b-3419-4a4a-bd0b-71fa711206fd')
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

    @decorators.idempotent_id('bd5845dc-d96b-4d83-a8da-7978bd91ddc1')
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

    @decorators.idempotent_id('3dfa6f70-f6fe-4ed5-96eb-5f4634064aa3')
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

    @decorators.idempotent_id('326d267a-de9d-4217-aadc-a0f2b5993537')
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

    @decorators.idempotent_id('395579c9-92bb-40a9-a8b6-9daaa20ae610')
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

    @decorators.idempotent_id('67510e3f-57cd-4a76-9e96-577e49229677')
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

    @decorators.idempotent_id('64ec16c4-3b8d-464d-88fb-f274241b1302')
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

    @decorators.idempotent_id('12636be0-6188-4003-8824-de4f89e3c745')
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

    @decorators.idempotent_id('bcfda1fa-ea65-47ce-8434-a64d85512fcf')
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

    @decorators.idempotent_id('abf9fe8b-ada3-4509-b15b-76d04e58f4e8')
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

    @decorators.idempotent_id('58558447-8618-4dbe-97ce-bfc39b3743e7')
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
