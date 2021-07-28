# Copyright 2021 Red Hat, Inc.
# All Rights Reserved.
#
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

from tempest.lib import exceptions

from glance_tempest_plugin.tests.rbac.v2 import base as rbac_base


class MetadefV2RbacResourceTypeTest(rbac_base.RbacMetadefBase):
    @classmethod
    def setup_clients(cls):
        super(MetadefV2RbacResourceTypeTest, cls).setup_clients()
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
        cls.resource_types_client = cls.persona.resource_types_client

    def create_resource_types(self):
        # Create namespace for two different projects
        namespaces = self.create_namespaces()

        namespace_resource_types = []
        for ns in namespaces:
            alt_client = None
            if ns['namespace'].startswith(self.alt_project_id):
                alt_client = self.os_project_alt_admin.resource_types_client
                client = alt_client
            if alt_client is None:
                client = self.os_project_admin.resource_types_client
            resource_name = "rs_type_of_%s" % (ns['namespace'])
            resource_type = client.create_resource_type_association(
                ns['namespace'], name=resource_name)
            resource_types = {'namespace': ns,
                              'resource_type': resource_type}
            namespace_resource_types.append(resource_types)

        return namespace_resource_types

    def assertRSTypeList(self, ns_rs_types, resp):
        actual_rs_types = set(rt['name'] for rt in resp['resource_types'])

        for rs_type in ns_rs_types:
            self.assertIn(rs_type['resource_type']['name'],
                          actual_rs_types)


class MetadefV2RbacResourceTypeTemplate(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def test_create_resource_type(self):
        """Test add_metadef_resource_type_association policy."""
        pass

    @abc.abstractmethod
    def test_get_resource_type(self):
        """Test get_metadef_resource_type policy."""
        pass

    @abc.abstractmethod
    def test_list_resource_types(self):
        """Test list_metadef_resource_types policy."""
        pass

    @abc.abstractmethod
    def test_delete_resource_type(self):
        """Test remove_metadef_resource_type_association policy."""
        pass


class ProjectAdminTests(MetadefV2RbacResourceTypeTest,
                        MetadefV2RbacResourceTypeTemplate):

    credentials = ['project_admin', 'project_alt_admin', 'primary']

    def test_create_resource_type(self):
        # As this is been covered in other tests for admin role,
        # skipping to test only create resource types separately.
        pass

    def test_get_resource_type(self):
        ns_rs_types = self.create_resource_types()

        # Get all metadef resource types with admin role of 'project'
        for rs_type in ns_rs_types:
            resp = self.do_request(
                'list_resource_type_association',
                expected_status=200,
                client=self.resource_types_client,
                namespace_id=rs_type['namespace']['namespace'])
            self.assertEqual(rs_type['resource_type']['name'],
                             resp['resource_type_associations'][0]['name'])

    def test_list_resource_types(self):
        ns_rs_types = self.create_resource_types()

        # list resource types - with admin role of 'project'
        resp = self.do_request('list_resource_types',
                               expected_status=200,
                               client=self.resource_types_client)

        # Verify that admin role of 'project' will be able to view available
        # resource types
        self.assertRSTypeList(ns_rs_types, resp)

    def test_delete_resource_type(self):
        ns_rs_types = self.create_resource_types()

        # delete all metadef resource types with admin role of 'project'
        for rs_type in ns_rs_types:
            self.do_request('delete_resource_type_association',
                            expected_status=204,
                            namespace_id=rs_type['namespace']['namespace'],
                            resource_name=rs_type['resource_type']['name'],
                            client=self.resource_types_client)

            # Verify the resource types is deleted successfully
            resp = self.do_request(
                'list_resource_type_association', expected_status=200,
                client=self.resource_types_client,
                namespace_id=rs_type['namespace']['namespace'])
            self.assertEqual([], resp['resource_type_associations'])


class ProjectMemberTests(MetadefV2RbacResourceTypeTest,
                         MetadefV2RbacResourceTypeTemplate):

    credentials = ['project_member', 'project_alt_member', 'project_admin',
                   'project_alt_admin', 'primary']

    def test_create_resource_type(self):
        namespaces = self.create_namespaces()

        def assertRSTypeCreate(namespace, owner, client):
            rs_type_name = "rs_type_of_%s" % (namespace['namespace'])
            expected_status = exceptions.Forbidden
            if (namespace['visibility'] != 'public' and
                    namespace['owner'] != owner):
                expected_status = exceptions.NotFound

            self.do_request('create_resource_type_association',
                            expected_status=expected_status,
                            namespace_id=namespace['namespace'],
                            name=rs_type_name,
                            client=client)

        # Make sure non admin role of 'project' forbidden to
        # create resource types
        for namespace in namespaces:
            assertRSTypeCreate(namespace, self.project_id,
                               self.resource_types_client)

    def test_get_resource_type(self):
        ns_rs_types = self.create_resource_types()

        def assertRSTypeGet(actual_rs_type, client, owner):
            ns = actual_rs_type['namespace']
            expected_status = 200
            if (ns['visibility'] != 'public' and ns['owner'] != owner):
                expected_status = exceptions.NotFound

            self.do_request('list_resource_type_association',
                            expected_status=expected_status,
                            namespace_id=ns['namespace'],
                            client=client)

        # Get resource type - member role from 'project' can access all
        # resource types of it's own & only resource types having public
        # namespace of 'alt_project'
        for rs_type in ns_rs_types:
            assertRSTypeGet(rs_type, self.resource_types_client,
                            self.project_id)

    def test_list_resource_types(self):
        ns_rs_types = self.create_resource_types()

        # list resource types - with member role of 'project'
        resp = self.do_request('list_resource_types',
                               expected_status=200,
                               client=self.resource_types_client)

        # Verify that member role of 'project' will be able to view available
        # resource types
        self.assertRSTypeList(ns_rs_types, resp)

        # list resource types -  with member role of 'alt_project'
        resp = self.do_request('list_resource_types',
                               expected_status=200,
                               client=self.resource_types_client)

    def test_delete_resource_type(self):
        ns_rs_types = self.create_resource_types()

        def assertRSTypeDelete(actual_rs_type, client, owner):
            ns = actual_rs_type['namespace']
            expected_status = exceptions.Forbidden
            if (ns['visibility'] != 'public' and ns['owner'] != owner):
                expected_status = exceptions.NotFound

            self.do_request(
                'delete_resource_type_association',
                expected_status=expected_status,
                namespace_id=ns['namespace'],
                resource_name=actual_rs_type['resource_type']['name'],
                client=client)

        # Make sure non admin role of 'project' not allowed to
        # delete resource types
        for rs_type in ns_rs_types:
            assertRSTypeDelete(rs_type, self.resource_types_client,
                               self.project_id)


class ProjectReaderTests(ProjectMemberTests):

    credentials = ['project_reader', 'project_alt_reader', 'project_admin',
                   'project_alt_admin', 'primary']
