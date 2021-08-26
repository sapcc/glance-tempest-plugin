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

from tempest.common import tempest_fixtures as fixtures
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions

from glance_tempest_plugin.tests.rbac.v2 import base as rbac_base


class MetadefV2RbacObjectsTest(rbac_base.RbacMetadefBase):
    def setUp(self):
        # NOTE(pdeore): As we are using global data there is a possibility
        # of invalid results if these tests are executed concurrently, to avoid
        # such conflicts we are using locking to execute metadef tests
        # serially.
        self.useFixture(fixtures.LockFixture('metadef_namespaces'))
        super(MetadefV2RbacObjectsTest, self).setUp()

    @classmethod
    def setup_clients(cls):
        super(MetadefV2RbacObjectsTest, cls).setup_clients()
        if 'project_member' in cls.credentials:
            persona = 'project_member'
            alt_persona = 'project_alt_member'
        elif 'project_reader' in cls.credentials:
            persona = 'project_reader'
            alt_persona = 'project_alt_reader'
        else:
            persona = 'project_admin'
            alt_persona = 'project_alt_admin'
        cls.persona = getattr(cls, 'os_%s' % persona)
        cls.alt_persona = getattr(cls, 'os_%s' % alt_persona)
        cls.project_id = cls.persona.namespace_objects_client.project_id
        cls.alt_project_id = \
            cls.alt_persona.namespace_objects_client.project_id
        cls.objects_client = cls.persona.namespace_objects_client

    def create_objects(self):
        # Create namespace for two different projects
        namespaces = self.create_namespaces()

        client = self.os_project_admin.namespace_objects_client
        namespace_objects = []
        for ns in namespaces:
            if ns['namespace'].startswith(self.project_id):
                client = self.os_project_alt_admin.namespace_objects_client
            object_name = "object_of_%s" % (ns['namespace'])
            namespace_object = client.create_namespace_object(
                ns['namespace'], name=object_name,
                description=data_utils.arbitrary_string())

            obj = {'namespace': ns, 'object': namespace_object}
            namespace_objects.append(obj)

        return namespace_objects

    def assertObjectsList(self, actual_obj, client, owner=None):
        ns = actual_obj['namespace']
        if owner:
            if not (ns['visibility'] == 'public' or
                    ns['owner'] == owner):
                self.do_request('list_namespace_objects',
                                expected_status=exceptions.NotFound,
                                namespace=ns['namespace'],
                                client=client)
            else:
                resp = self.do_request('list_namespace_objects',
                                       expected_status=200,
                                       namespace=ns['namespace'],
                                       client=client)
                self.assertIn(actual_obj['object']['name'],
                              resp['objects'][0]['name'])
        else:
            resp = self.do_request('list_namespace_objects',
                                   expected_status=200,
                                   namespace=ns['namespace'],
                                   client=client)
            self.assertIn(actual_obj['object']['name'],
                          resp['objects'][0]['name'])


class MetadefV2RbacObjectsTemplate(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def test_create_object(self):
        """Test add_metadef_object policy."""
        pass

    @abc.abstractmethod
    def test_get_object(self):
        """Test get_metadef_object policy."""
        pass

    @abc.abstractmethod
    def test_list_objects(self):
        """Test list_metadef_objects policy."""
        pass

    @abc.abstractmethod
    def test_update_object(self):
        """Test update_metadef_object policy."""
        pass

    @abc.abstractmethod
    def test_delete_object(self):
        """Test delete_metadef_object policy."""
        pass


class ProjectAdminTests(MetadefV2RbacObjectsTest,
                        MetadefV2RbacObjectsTemplate):

    credentials = ['project_admin', 'project_alt_admin', 'primary']

    def test_get_object(self):
        ns_objects = self.create_objects()

        # Get all metadef objects with admin role
        for obj in ns_objects:
            resp = self.do_request(
                'show_namespace_object',
                expected_status=200,
                client=self.objects_client,
                namespace=obj['namespace']['namespace'],
                object_name=obj['object']['name'])
            self.assertEqual(obj['object']['name'], resp['name'])

    def test_list_objects(self):
        ns_objects = self.create_objects()

        # list all metadef objects with admin role
        for obj in ns_objects:
            self.assertObjectsList(obj, self.objects_client)

    def test_update_object(self):
        ns_objects = self.create_objects()

        # update all metadef objects with admin role of 'project'
        for obj in ns_objects:
            resp = self.do_request(
                'update_namespace_object',
                expected_status=200,
                namespace=obj['namespace']['namespace'],
                client=self.objects_client,
                object_name=obj['object']['name'],
                name=obj['object']['name'],
                description=data_utils.arbitrary_string(base_text="updated"))
            self.assertNotEqual(obj['object']['description'],
                                resp['description'])

    def test_delete_object(self):
        ns_objects = self.create_objects()
        # delete all metadef objects with admin role of 'project'
        for obj in ns_objects:
            self.do_request('delete_namespace_object',
                            expected_status=204,
                            namespace=obj['namespace']['namespace'],
                            object_name=obj['object']['name'],
                            client=self.objects_client)

            # Verify the object is deleted successfully
            self.do_request('show_namespace_object',
                            expected_status=exceptions.NotFound,
                            client=self.objects_client,
                            namespace=obj['namespace']['namespace'],
                            object_name=obj['object']['name'])

    def test_create_object(self):
        # As this is been covered in other tests for admin role,
        # skipping to test only create objects seperately.
        pass


class ProjectMemberTests(MetadefV2RbacObjectsTest,
                         MetadefV2RbacObjectsTemplate):

    credentials = ['project_member', 'project_alt_member', 'project_admin',
                   'project_alt_admin', 'primary']

    def test_create_object(self):
        namespaces = self.create_namespaces()

        def assertCreateObjects(namespace, owner, client):
            object_name = "object_of_%s" % (namespace['namespace'])
            expected_status = exceptions.Forbidden
            if (namespace['visibility'] == 'private' and
                    namespace['owner'] != owner):
                expected_status = exceptions.NotFound

            self.do_request('create_namespace_object',
                            expected_status=expected_status,
                            namespace=namespace['namespace'],
                            name=object_name,
                            client=client)

        # Make sure non admin role of 'project' forbidden to
        # create objects
        for namespace in namespaces:
            assertCreateObjects(namespace, self.project_id,
                                self.objects_client)

    def test_get_object(self):

        def assertObjectGet(actual_obj, owner, client):
            ns = actual_obj['namespace']
            expected_status = 200
            if (ns['visibility'] == 'private' and
                    ns['owner'] != owner):
                expected_status = exceptions.NotFound

            self.do_request('show_namespace_object',
                            expected_status=expected_status,
                            namespace=actual_obj['namespace']['namespace'],
                            object_name=actual_obj['object']['name'],
                            client=client)

        ns_objects = self.create_objects()

        # Get object - member role from 'project' can access all
        # objects of it's own & only objects having public namespace of
        # 'alt_project'
        for obj in ns_objects:
            assertObjectGet(obj, self.project_id, self.objects_client)

    def test_list_objects(self):
        ns_objects = self.create_objects()

        # list objects - member role from 'project' can access all
        # objects of it's own & only objects having public namespace of
        # 'alt_project'
        for obj in ns_objects:
            self.assertObjectsList(obj, self.objects_client, self.project_id)

    def test_update_object(self):

        def assertObjectUpdate(actual_object, owner, client):
            ns = actual_object['namespace']
            expected_status = exceptions.Forbidden
            if (ns['visibility'] == 'private' and
                    ns['owner'] != owner):
                expected_status = exceptions.NotFound

            self.do_request('update_namespace_object',
                            expected_status=expected_status,
                            name=actual_object['object']['name'],
                            description=data_utils.arbitrary_string(),
                            namespace=actual_object['namespace']['namespace'],
                            object_name=actual_object['object']['name'],
                            client=client)

        ns_objects = self.create_objects()
        # Make sure non admin role of 'project' not allowed to
        # update objects
        for obj in ns_objects:
            assertObjectUpdate(obj, self.project_id, self.objects_client)

    def test_delete_object(self):

        def assertObjectDelete(actual_obj, owner, client):
            ns = actual_obj['namespace']
            expected_status = exceptions.Forbidden
            if (ns['visibility'] == 'private' and
                    ns['owner'] != owner):
                expected_status = exceptions.NotFound

            self.do_request('delete_namespace_object',
                            expected_status=expected_status,
                            namespace=actual_obj['namespace']['namespace'],
                            object_name=actual_obj['object']['name'],
                            client=client)

        ns_objects = self.create_objects()
        # Make sure non admin role of 'project' not allowed to
        # delete objects
        for obj in ns_objects:
            assertObjectDelete(obj, self.project_id, self.objects_client)


class ProjectReaderTests(ProjectMemberTests):

    credentials = ['project_reader', 'project_alt_reader', 'project_admin',
                   'project_alt_admin', 'primary']
