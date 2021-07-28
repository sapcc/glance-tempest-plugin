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

from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions

from glance_tempest_plugin.tests.rbac.v2 import base as rbac_base


class MetadefV2RbacPropertiesTest(rbac_base.RbacMetadefBase):
    @classmethod
    def setup_clients(cls):
        super(MetadefV2RbacPropertiesTest, cls).setup_clients()
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
        cls.properties_client = cls.persona.namespace_properties_client

    def create_properties(self):
        # Create namespace for two different projects
        namespaces = self.create_namespaces()

        namespace_properties = []
        for ns in namespaces:
            alt_client = None
            if ns['namespace'].startswith(self.alt_project_id):
                alt_client = \
                    self.os_project_alt_admin.namespace_properties_client
                client = alt_client
            if alt_client is None:
                client = self.os_project_admin.namespace_properties_client

            property_name = "prop_of_%s" % (ns['namespace'])
            namespace_property = client.create_namespace_property(
                ns['namespace'], name=property_name, title='property',
                type='integer')

            prop = {'namespace': ns, 'property': namespace_property}
            namespace_properties.append(prop)

        return namespace_properties

    def assertPropertyList(self, actual_prop, client, owner=None):
        ns = actual_prop['namespace']
        if owner:
            if not (ns['visibility'] == 'public' or ns['owner'] == owner):
                resp = self.do_request('list_namespace_properties',
                                       expected_status=exceptions.NotFound,
                                       client=client,
                                       namespace=ns['namespace'])
            else:
                resp = self.do_request('list_namespace_properties',
                                       expected_status=200,
                                       client=client,
                                       namespace=ns['namespace'])
                self.assertEqual(actual_prop['property']['name'],
                                 [*resp['properties']][0])
        else:
            resp = self.do_request('list_namespace_properties',
                                   expected_status=200,
                                   client=client,
                                   namespace=ns['namespace'])
            self.assertEqual(actual_prop['property']['name'],
                             [*resp['properties']][0])


class MetadefV2RbacPropertiesTemplate(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def test_create_property(self):
        """Test add_metadef_property policy."""
        pass

    @abc.abstractmethod
    def test_get_properties(self):
        """Test get_metadef_property policy."""
        pass

    @abc.abstractmethod
    def test_list_properties(self):
        """Test list_metadef_properties policy."""
        pass

    @abc.abstractmethod
    def test_update_properties(self):
        """Test update_metadef_property policy."""
        pass

    @abc.abstractmethod
    def test_delete_properties(self):
        """Test delete_metadef_property policy."""
        pass


class ProjectAdminTests(MetadefV2RbacPropertiesTest,
                        MetadefV2RbacPropertiesTemplate):

    credentials = ['project_admin', 'project_alt_admin', 'primary']

    def test_create_property(self):
        # As this is been covered in other tests for admin role,
        # skipping to test only create properties separately.
        pass

    def test_get_properties(self):
        ns_properties = self.create_properties()

        # Get all metadef properties with admin role of 'project'
        for prop in ns_properties:
            resp = self.do_request(
                'show_namespace_properties',
                expected_status=200,
                client=self.properties_client,
                namespace=prop['namespace']['namespace'],
                property_name=prop['property']['name'])
            self.assertEqual(prop['property'], resp)

    def test_list_properties(self):
        ns_properties = self.create_properties()
        # list all metadef properties with admin role of 'project'
        for prop in ns_properties:
            self.assertPropertyList(prop, self.properties_client)

    def test_update_properties(self):
        ns_properties = self.create_properties()

        # update all metadef properties with admin role of 'project'
        for prop in ns_properties:
            resp = self.do_request(
                'update_namespace_properties',
                expected_status=200,
                namespace=prop['namespace']['namespace'],
                client=self.properties_client,
                title="UPDATE_Property",
                property_name=prop['property']['name'],
                name=prop['property']['name'],
                type="string")
            self.assertNotEqual(prop['property']['title'],
                                resp['title'])

    def test_delete_properties(self):
        ns_properties = self.create_properties()

        # delete all metadef properties with admin role of 'project'
        for prop in ns_properties:
            self.do_request('delete_namespace_property',
                            expected_status=204,
                            namespace=prop['namespace']['namespace'],
                            property_name=prop['property']['name'],
                            client=self.properties_client)

            # Verify the property is deleted successfully
            self.do_request('show_namespace_properties',
                            expected_status=exceptions.NotFound,
                            client=self.properties_client,
                            namespace=prop['namespace']['namespace'],
                            property_name=prop['property']['name'])


class ProjectMemberTests(MetadefV2RbacPropertiesTest,
                         MetadefV2RbacPropertiesTemplate):

    credentials = ['project_member', 'project_alt_member',
                   'project_admin', 'project_alt_admin', 'primary']

    def test_create_property(self):
        namespaces = self.create_namespaces()

        def assertPropertyCreate(namespace, client, owner=None):
            property_name = "prop_of_%s" % (namespace['namespace'])
            expected_status = exceptions.Forbidden
            if not (namespace['visibility'] == 'public' or
                    namespace['owner'] == owner):
                expected_status = exceptions.NotFound

            self.do_request('create_namespace_property',
                            expected_status=expected_status,
                            namespace=namespace['namespace'],
                            title="property",
                            type='integer',
                            name=property_name,
                            client=client)
        # Make sure non admin role of 'project' forbidden to
        # create properties
        for namespace in namespaces:
            assertPropertyCreate(namespace, self.properties_client,
                                 self.project_id)

    def test_get_properties(self):
        ns_properties = self.create_properties()

        def assertPropertyGet(actual_prop, client, owner=None):
            ns = actual_prop['namespace']
            expected_status = 200
            if (ns['visibility'] != 'public' and
                    ns['owner'] != owner):
                expected_status = exceptions.NotFound

            self.do_request('show_namespace_properties',
                            expected_status=expected_status,
                            namespace=ns['namespace'],
                            property_name=actual_prop['property']['name'],
                            client=client)

        # Get property - member role from 'project' can access all
        # properties of it's own & only propertys having public namespace of
        # 'alt_project'
        for prop in ns_properties:
            assertPropertyGet(prop, self.properties_client, self.project_id)

    def test_list_properties(self):
        ns_properties = self.create_properties()

        # list properties - member role from 'project' can access all
        # properties of it's own & only propertys having public namespace of
        # 'alt_project'
        for prop in ns_properties:
            self.assertPropertyList(prop, self.properties_client,
                                    self.project_id)

    def test_update_properties(self):
        ns_properties = self.create_properties()

        def assertPropertyUpdate(actual_prop, client, owner=None):
            ns = actual_prop['namespace']
            expected_status = exceptions.Forbidden
            if (ns['visibility'] != 'public' and
                    ns['owner'] != owner):
                expected_status = exceptions.NotFound

            self.do_request('update_namespace_properties',
                            expected_status=expected_status,
                            name=actual_prop['property']['name'],
                            description=data_utils.arbitrary_string(),
                            namespace=ns['namespace'],
                            property_name=actual_prop['property']['name'],
                            title="UPDATE_Property",
                            type="string",
                            client=client)

        # Make sure non admin role of 'project' not allowed to
        # update properties
        for prop in ns_properties:
            assertPropertyUpdate(prop, self.properties_client,
                                 self.project_id)

    def test_delete_properties(self):
        ns_properties = self.create_properties()

        def assertPropertyDelete(actual_prop, client, owner=None):
            ns = actual_prop['namespace']
            expected_status = exceptions.Forbidden
            if (ns['visibility'] != 'public' and
                    ns['owner'] != owner):
                expected_status = exceptions.NotFound

            self.do_request('delete_namespace_property',
                            expected_status=expected_status,
                            namespace=ns['namespace'],
                            property_name=actual_prop['property']['name'],
                            client=client)

        # Make sure non admin role of 'project' not allowed to
        # delete properties
        for prop in ns_properties:
            assertPropertyDelete(prop, self.properties_client,
                                 self.project_id)


class ProjectReaderTests(ProjectMemberTests):

    credentials = ['project_reader', 'project_alt_reader',
                   'project_admin', 'project_alt_admin', 'primary']
