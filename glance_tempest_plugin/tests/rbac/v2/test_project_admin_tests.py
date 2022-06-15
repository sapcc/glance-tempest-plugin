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


class ProjectAdminTests(ImageV2RbacImageTest,
                        ImageV2RbacTemplate):

    credentials = ['project_admin', 'system_admin', 'project_alt_admin']

    @decorators.idempotent_id('025eea27-fa86-44a9-85a2-91295842f808')
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

    @decorators.idempotent_id('61fd8b5e-8a0b-46ca-91c4-6c2c2d35039d')
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

    @decorators.idempotent_id('d0c18f80-6168-4d98-a86e-c09d28d83bb0')
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

    @decorators.idempotent_id('9e9f7fd6-e93c-402c-9f3c-177fede8f645')
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

    @decorators.idempotent_id('947f1ae1-c5b6-4552-89e3-1078ca722be4')
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

    @decorators.idempotent_id('24891c04-28ca-41f9-92d1-c06d8ba4b83d')
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

    @decorators.idempotent_id('e45899d6-7e16-4cbf-b800-31c05e6caf8c')
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

    @decorators.idempotent_id('ec3da4dc-f478-4a70-8799-db0814e340f4')
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

    @decorators.idempotent_id('8719285b-5b7b-48b8-ba5e-2bc7e3535025')
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

    @decorators.idempotent_id('daaef0c5-1172-457b-b1a3-0736b64c8426')
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

    @decorators.idempotent_id('2baaaca0-6335-4219-9bd9-207a5cfda6a2')
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

    @decorators.idempotent_id('7f0a8e2b-b655-416a-914b-9615cff18bbf')
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

    @decorators.idempotent_id('dfc73f6f-bf91-4b6a-8482-acc8c436e066')
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

    @decorators.idempotent_id('3cbef53c-ab8a-4343-b993-8f9e14ab90d1')
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
