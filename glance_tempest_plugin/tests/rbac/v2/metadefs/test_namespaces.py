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


class MetadefV2RbacNamespaceTest(rbac_base.RbacMetadefBase):
    def setUp(self):
        # NOTE(abhishekk): As we are using global data there is a possibility
        # of invalid results if these tests are executed concurrently, to avoid
        # such conflicts we are using locking to execute metadef tests
        # serially.
        self.useFixture(fixtures.LockFixture('metadef_namespaces'))
        super(MetadefV2RbacNamespaceTest, self).setUp()

    @classmethod
    def setup_clients(cls):
        super(MetadefV2RbacNamespaceTest, cls).setup_clients()
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
        cls.project_id = cls.persona.namespaces_client.project_id
        cls.alt_project_id = cls.alt_persona.namespaces_client.project_id
        cls.admin_namespace_client = cls.os_project_admin.namespaces_client
        cls.namespace_client = cls.persona.namespaces_client
        cls.alt_namespace_client = cls.alt_persona.namespaces_client

    def assertListNamespaces(self, actual, expected, owner=None):
        expected_ns = set(ns['namespace'] for ns in expected['namespaces'])
        if owner:
            for ns in actual:
                if (ns['visibility'] == 'private' and
                        ns['owner'] != owner):
                    self.assertNotIn(ns['namespace'], expected_ns)
                else:
                    self.assertIn(ns['namespace'], expected_ns)
        else:
            for ns in actual:
                self.assertIn(ns['namespace'], expected_ns)


class MetadefV2RbacNamespaceTemplate(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def test_get_namespace(self):
        """Test get_metadef_namespace policy."""
        pass

    @abc.abstractmethod
    def test_list_namespaces(self):
        """Test get_metadef_namespaces policy."""
        pass

    @abc.abstractmethod
    def test_update_namespace(self):
        """Test modify_metadef_namespace policy."""
        pass

    @abc.abstractmethod
    def test_create_namespace(self):
        """Test add_metadef_namespace policy."""
        pass

    @abc.abstractmethod
    def test_delete_namespace(self):
        """Test delete_metadef_namespace policy."""
        pass


class ProjectAdminTests(MetadefV2RbacNamespaceTest,
                        MetadefV2RbacNamespaceTemplate):

    credentials = ['project_admin', 'project_alt_admin', 'primary']

    def test_list_namespaces(self):
        actual_namespaces = self.create_namespaces()

        # Get above created namespace by admin role
        resp = self.do_request('list_namespaces', expected_status=200,
                               client=self.admin_namespace_client)

        self.assertListNamespaces(actual_namespaces, resp)

    def test_get_namespace(self):
        actual_namespaces = self.create_namespaces()

        # Get above created namespace by admin role
        for ns in actual_namespaces:
            resp = self.do_request('show_namespace', expected_status=200,
                                   namespace=ns['namespace'],
                                   client=self.admin_namespace_client)
            self.assertEqual(ns['namespace'], resp['namespace'])

    def test_create_namespace(self):
        # As this is been covered in other tests for admin role,
        # skipping to test only create namespaces seperately.
        pass

    def test_update_namespace(self):
        actual_namespaces = self.create_namespaces()

        # Updating the above created namespace by admin role
        for ns in actual_namespaces:
            resp = self.do_request(
                'update_namespace', expected_status=200,
                namespace=ns['namespace'],
                client=self.admin_namespace_client,
                description=data_utils.arbitrary_string(base_text="updated"))
            self.assertNotEqual(ns['description'], resp['description'])

    def test_delete_namespace(self):
        actual_namespaces = self.create_namespaces()

        # Deleting the above created namespace by admin role
        for ns in actual_namespaces:
            self.do_request('delete_namespace', expected_status=204,
                            namespace=ns['namespace'],
                            client=self.admin_namespace_client,)

            # Verify the namespaces are deleted successfully
            self.do_request('show_namespace',
                            expected_status=exceptions.NotFound,
                            namespace=ns['namespace'],
                            client=self.admin_namespace_client,)


class ProjectMemberTests(MetadefV2RbacNamespaceTest,
                         MetadefV2RbacNamespaceTemplate):

    credentials = ['project_member', 'project_alt_member',
                   'project_admin', 'project_alt_admin', 'primary']

    def test_get_namespace(self):

        def assertGetNamespace(actual_ns, owner, client):
            expected_status = 200
            if (actual_ns['visibility'] == 'private' and
                    actual_ns['owner'] != owner):
                expected_status = exceptions.NotFound

            self.do_request('show_namespace',
                            expected_status=expected_status,
                            client=client,
                            namespace=actual_ns['namespace'])

        actual_namespaces = self.create_namespaces()

        # Get namespace - member role from 'project' can access all
        # namespaces of it's own & only public namespace of 'alt_project'
        for actual_ns in actual_namespaces:
            assertGetNamespace(actual_ns, self.project_id,
                               self.namespace_client)

        # Get namespace - member role from 'alt_project' can access all
        # namespaces of it's own & only public namespace of 'project'
        for actual_ns in actual_namespaces:
            assertGetNamespace(actual_ns, self.alt_project_id,
                               self.alt_namespace_client)

    def test_list_namespaces(self):
        actual_namespaces = self.create_namespaces()

        # List namespace - member role from 'project' can access all
        # namespaces of it's own & only public namespace of 'alt_project'
        resp = self.do_request('list_namespaces',
                               client=self.namespace_client,
                               expected_status=200)
        self.assertListNamespaces(actual_namespaces, resp, self.project_id)

        # List namespace - member role from 'alt_project' can access all
        # namespaces of it's own & only public namespace of 'project'
        resp = self.do_request('list_namespaces',
                               client=self.alt_namespace_client,
                               expected_status=200)
        self.assertListNamespaces(actual_namespaces, resp, self.alt_project_id)

    def test_update_namespace(self):
        actual_namespaces = self.create_namespaces()

        def assertUpdateNamespace(actual_ns, owner, client):
            expected_status = exceptions.Forbidden
            if not (actual_ns['visibility'] == 'public' or
                    actual_ns['owner'] == owner):
                expected_status = exceptions.NotFound

            self.do_request('update_namespace',
                            expected_status=expected_status,
                            client=client,
                            description=data_utils.arbitrary_string(),
                            namespace=actual_ns['namespace'])

        # Check member role of 'project' is forbidden to update namespace
        for actual_ns in actual_namespaces:
            assertUpdateNamespace(actual_ns, self.project_id,
                                  self.namespace_client)

        # Check member role of 'alt_project' is forbidden to update namespace
        for actual_ns in actual_namespaces:
            assertUpdateNamespace(actual_ns, self.alt_project_id,
                                  self.alt_namespace_client)

    def test_create_namespace(self):
        # Check non-admin role of 'project' not allowed to create namespace
        self.do_request('create_namespace',
                        expected_status=exceptions.Forbidden,
                        client=self.namespace_client,
                        namespace=data_utils.arbitrary_string())

        # Check non-admin role of 'alt_project' not allowed to create namespace
        self.do_request('create_namespace',
                        expected_status=exceptions.Forbidden,
                        client=self.alt_namespace_client,
                        namespace=data_utils.arbitrary_string())

    def test_delete_namespace(self):
        actual_namespaces = self.create_namespaces()

        def assertDeleteNamespace(actual_ns, owner, client):
            expected_status = exceptions.Forbidden
            if not (actual_ns['visibility'] == 'public' or
                    actual_ns['owner'] == owner):
                expected_status = exceptions.NotFound

            self.do_request('delete_namespace',
                            expected_status=expected_status,
                            client=client,
                            namespace=actual_ns['namespace'])

        # Check member role of 'project' is forbidden to delete namespace
        for actual_ns in actual_namespaces:
            assertDeleteNamespace(actual_ns, self.project_id,
                                  self.namespace_client)

        # Check member role of 'alt_project' is forbidden to delete namespace
        for actual_ns in actual_namespaces:
            assertDeleteNamespace(actual_ns, self.alt_project_id,
                                  self.alt_namespace_client)

        # Verify the namespaces are not deleted
        for actual_ns in actual_namespaces:
            self.do_request('show_namespace',
                            expected_status=200,
                            client=self.admin_namespace_client,
                            namespace=actual_ns['namespace'])


class ProjectReaderTests(ProjectMemberTests):
    credentials = ['project_reader', 'project_alt_reader',
                   'project_admin', 'project_alt_admin', 'primary']
