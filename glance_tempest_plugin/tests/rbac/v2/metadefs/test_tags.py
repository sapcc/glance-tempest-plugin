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


class MetadefV2RbacTagsTest(rbac_base.RbacMetadefBase):
    @classmethod
    def setup_clients(cls):
        super(MetadefV2RbacTagsTest, cls).setup_clients()
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
        cls.tags_client = cls.persona.namespace_tags_client

    def create_tags(self, namespaces, multiple_tags=False):
        namespace_tags = []

        if multiple_tags:
            tags = [{"name": "tag1"}, {"name": "tag2"}, {"name": "tag3"}]
            for ns in namespaces:
                alt_client = None
                if ns['namespace'].startswith(self.alt_project_id):
                    alt_client = \
                        self.os_project_alt_admin.namespace_tags_client
                    client = alt_client
                if alt_client is None:
                    client = self.os_project_admin.namespace_tags_client
                multiple_tags = client.create_namespace_tags(
                    ns['namespace'], tags=tags)

                namespace_multiple_tags = {'namespace': ns,
                                           'tags': multiple_tags}
                namespace_tags.append(namespace_multiple_tags)
        else:
            for ns in namespaces:
                alt_client = None
                if ns['namespace'].startswith(self.alt_project_id):
                    alt_client = \
                        self.os_project_alt_admin.namespace_tags_client
                    client = alt_client
                if alt_client is None:
                    client = self.os_project_admin.namespace_tags_client
                tag_name = "tag_of_%s" % (ns['namespace'])
                namespace_tag = client.create_namespace_tag(
                    ns['namespace'], tag_name=tag_name)

                tag = {'namespace': ns, 'tag': namespace_tag}
                namespace_tags.append(tag)

        return namespace_tags

    def assertTagsList(self, actual_tag, client, owner=None):
        ns = actual_tag['namespace']
        if owner:
            if not (ns['visibility'] == 'public' or ns['owner'] == owner):
                self.do_request('list_namespace_tags',
                                expected_status=exceptions.NotFound,
                                client=client,
                                namespace=ns['namespace'])
            else:
                resp = self.do_request('list_namespace_tags',
                                       expected_status=200,
                                       client=client,
                                       namespace=ns['namespace'])
                self.assertEqual(actual_tag['tag']['name'],
                                 resp['tags'][0]['name'])
        else:
            resp = self.do_request('list_namespace_tags',
                                   expected_status=200,
                                   client=client,
                                   namespace=ns['namespace'])
            self.assertEqual(actual_tag['tag']['name'],
                             resp['tags'][0]['name'])


class MetadefV2RbacTagsTemplate(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def test_create_tag(self):
        """Test add_metadef_tag policy."""
        pass

    @abc.abstractmethod
    def test_get_tags(self):
        """Test get_metadef_tag policy."""
        pass

    @abc.abstractmethod
    def test_list_tags(self):
        """Test list_metadef_tags policy."""
        pass

    @abc.abstractmethod
    def test_update_tags(self):
        """Test update_metadef_tag policy."""
        pass

    @abc.abstractmethod
    def test_delete_tags(self):
        """Test delete_metadef_tag policy."""
        pass


class ProjectAdminTests(MetadefV2RbacTagsTest,
                        MetadefV2RbacTagsTemplate):

    credentials = ['project_admin', 'project_alt_admin', 'primary']

    def test_create_tag(self):
        # As this is been covered in other tests for admin role,
        # skipping to test only create properties separately.
        pass

    def test_get_tags(self):
        namespaces = self.create_namespaces()
        ns_tags = self.create_tags(namespaces)

        # Get all metadef tags with admin role of 'project'
        for tag in ns_tags:
            resp = self.do_request(
                'show_namespace_tag',
                expected_status=200,
                client=self.tags_client,
                namespace=tag['namespace']['namespace'],
                tag_name=tag['tag']['name'])
            self.assertEqual(tag['tag']['name'], resp['name'])

    def test_list_tags(self):
        namespaces = self.create_namespaces()
        ns_tags = self.create_tags(namespaces)
        # list all metadef tags with admin role of 'project'
        for tag in ns_tags:
            self.assertTagsList(tag, self.tags_client)

    def test_update_tags(self):
        namespaces = self.create_namespaces()
        ns_tags = self.create_tags(namespaces)

        # update all metadef tags with admin role of 'project'
        for tag in ns_tags:
            resp = self.do_request(
                'update_namespace_tag',
                expected_status=200,
                namespace=tag['namespace']['namespace'],
                client=self.tags_client,
                tag_name=tag['tag']['name'],
                name=data_utils.arbitrary_string(base_text="updated-name"))
            self.assertNotEqual(tag['tag']['name'], resp['name'])

    def test_delete_tags(self):
        namespaces = self.create_namespaces()
        ns_tags = self.create_tags(namespaces)

        def assertDeleteTags(tag, client, multiple_tags=False):
            namespace = tag['namespace']['namespace']
            if multiple_tags:
                self.do_request('delete_namespace_tags',
                                expected_status=204,
                                namespace=namespace,
                                client=client)
                # Verify the tags are deleted successfully
                resp = self.do_request('list_namespace_tags',
                                       client=client,
                                       namespace=namespace)
                self.assertEqual(0, len(resp['tags']))
            else:
                tag_name = tag['tag']['name']
                self.do_request('delete_namespace_tag',
                                expected_status=204,
                                namespace=namespace,
                                tag_name=tag_name,
                                client=client)

                # Verify the tag is deleted successfully
                self.do_request('show_namespace_tag',
                                expected_status=exceptions.NotFound,
                                client=client,
                                namespace=namespace,
                                tag_name=tag_name)

        # delete all metadef tags with admin role of 'project'
        for tag in ns_tags:
            assertDeleteTags(tag, self.tags_client)

        # Create multiple tags
        ns_multiple_tags = self.create_tags(namespaces, multiple_tags=True)
        # delete all metadef multiple tags with admin role of 'project'
        for tags in ns_multiple_tags:
            assertDeleteTags(tags, self.tags_client, multiple_tags=True)


class ProjectMemberTests(MetadefV2RbacTagsTest,
                         MetadefV2RbacTagsTemplate):

    credentials = ['project_member', 'project_alt_member',
                   'project_admin', 'project_alt_admin', 'primary']

    def test_create_tag(self):
        namespaces = self.create_namespaces()

        def assertTagsCreate(namespace, client, owner, multiple_tags=False):
            expected_status = exceptions.Forbidden
            if (namespace['visibility'] != 'public' and
                    namespace['owner'] != owner):
                expected_status = exceptions.NotFound

            if multiple_tags:
                multiple_tags = [{"name": "tag1"}, {"name": "tag2"},
                                 {"name": "tag3"}]
                self.do_request('create_namespace_tags',
                                expected_status=expected_status,
                                namespace=namespace['namespace'],
                                tags=multiple_tags,
                                client=client)
            else:
                tag_name = "tag_of_%s" % (namespace['namespace'])
                self.do_request('create_namespace_tag',
                                expected_status=expected_status,
                                namespace=namespace['namespace'],
                                tag_name=tag_name,
                                client=client)

        # Make sure non admin role of 'project' forbidden to
        # create tags
        for namespace in namespaces:
            assertTagsCreate(namespace, self.tags_client, self.project_id)

            # Create Multiple Tags
            assertTagsCreate(namespace, self.tags_client, self.project_id,
                             multiple_tags=True)

    def test_get_tags(self):
        namespaces = self.create_namespaces()
        ns_tags = self.create_tags(namespaces)

        def assertTagGet(actual_tag, client, owner=None):
            ns = actual_tag['namespace']
            expected_status = 200
            if (ns['visibility'] != 'public' and ns['owner'] != owner):
                expected_status = exceptions.NotFound

            self.do_request('show_namespace_tag',
                            expected_status=expected_status,
                            namespace=ns['namespace'],
                            tag_name=actual_tag['tag']['name'],
                            client=client)

        # Get tag - member role from 'project' can access all
        # tags of it's own & only tags having public namespace of
        # 'alt_project'
        for tag in ns_tags:
            assertTagGet(tag, self.tags_client, self.project_id)

    def test_list_tags(self):
        namespaces = self.create_namespaces()
        ns_tags = self.create_tags(namespaces)

        # list tags - member role from 'project' can access all
        # tags of it's own & only tags having public namespace of
        # 'alt_project'
        for tag in ns_tags:
            self.assertTagsList(tag, self.tags_client, self.project_id)

    def test_update_tags(self):
        namespaces = self.create_namespaces()
        ns_tags = self.create_tags(namespaces)

        def assertTagUpdate(tag, client, owner):
            ns = tag['namespace']
            expected_status = exceptions.Forbidden
            if (ns['visibility'] != 'public' and ns['owner'] != owner):
                expected_status = exceptions.NotFound

            self.do_request('update_namespace_tag',
                            expected_status=expected_status,
                            name=data_utils.arbitrary_string(),
                            namespace=tag['namespace']['namespace'],
                            tag_name=tag['tag']['name'],
                            client=client)

        # Make sure non admin role of 'project' not allowed to
        # update tags
        for tag in ns_tags:
            assertTagUpdate(tag, self.tags_client, self.project_id)

    def test_delete_tags(self):
        namespaces = self.create_namespaces()
        ns_tags = self.create_tags(namespaces)

        def assertTagsDelete(actual_tag, client, owner, multiple_tags=False):
            ns = tag['namespace']
            expected_status = exceptions.Forbidden
            if (ns['visibility'] != 'public' and ns['owner'] != owner):
                expected_status = exceptions.NotFound

            if multiple_tags:
                self.do_request('delete_namespace_tags',
                                expected_status=expected_status,
                                namespace=ns['namespace'],
                                client=client)
            else:
                self.do_request('delete_namespace_tag',
                                expected_status=expected_status,
                                namespace=ns['namespace'],
                                tag_name=actual_tag['tag']['name'],
                                client=client)

        # Make sure non admin role of 'project' not allowed to
        # delete tags
        for tag in ns_tags:
            assertTagsDelete(tag, self.tags_client, self.project_id)

        # Create Multiple Tags
        ns_multiple_tags = self.create_tags(namespaces, multiple_tags=True)
        # Make sure non admin role of 'project' not allowed to
        # delete multiple tags
        for tags in ns_multiple_tags:
            assertTagsDelete(tags, self.tags_client, self.project_id,
                             multiple_tags=True)


class ProjectReaderTests(ProjectMemberTests):

    credentials = ['project_reader', 'project_alt_reader',
                   'project_admin', 'project_alt_admin', 'primary']
