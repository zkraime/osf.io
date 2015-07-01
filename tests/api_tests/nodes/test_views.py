# -*- coding: utf-8 -*-
import mock
from nose.tools import *  # flake8: noqa

from website.models import Node
from framework.auth.core import Auth
from website.util.sanitize import strip_html
from api.base.settings.defaults import API_BASE

from tests.base import ApiTestCase, fake
from tests.factories import (
    DashboardFactory,
    FolderFactory,
    NodeFactory,
    ProjectFactory,
    RegistrationFactory,
    UserFactory
)

class TestWelcomeToApi(ApiTestCase):
    def setUp(self):
        super(TestWelcomeToApi, self).setUp()
        self.user = UserFactory.build()
        self.user.set_password('justapoorboy')
        self.user.save()
        self.basic_auth = (self.user.username, 'justapoorboy')
        self.url = '/{}'.format(API_BASE)

    def test_returns_200_for_logged_out_user(self):
        res = self.app.get(self.url)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['meta']['current_user'], None)

    def test_returns_current_user_info_when_logged_in(self):
        res = self.app.get(self.url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['meta']['current_user']['data']['given_name'], self.user.given_name)


class TestNodeList(ApiTestCase):
    def setUp(self):
        super(TestNodeList, self).setUp()
        self.user = UserFactory.build()
        self.user.set_password('justapoorboy')
        self.user.save()
        self.basic_auth = (self.user.username, 'justapoorboy')

        self.non_contrib = UserFactory.build()
        self.non_contrib.set_password('justapoorboy')
        self.non_contrib.save()
        self.basic_non_contrib_auth = (self.non_contrib.username, 'justapoorboy')

        self.deleted = ProjectFactory(is_deleted=True)
        self.private = ProjectFactory(is_public=False, creator=self.user)
        self.public = ProjectFactory(is_public=True, creator=self.user)

        self.url = '/{}nodes/'.format(API_BASE)

    def test_only_returns_non_deleted_public_projects(self):
        res = self.app.get(self.url)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.public._id, ids)
        assert_not_in(self.deleted._id, ids)
        assert_not_in(self.private._id, ids)

    def test_return_public_node_list_logged_out_user(self):
        res = self.app.get(self.url)
        assert_equal(res.status_code, 200)
        ids = [each['id'] for each in res.json['data']]
        assert_in(self.public._id, ids)
        assert_not_in(self.private._id, ids)

    def test_return_public_node_list_logged_in_user(self):
        res = self.app.get(self.url, auth=self.non_contrib)
        assert_equal(res.status_code, 200)
        ids = [each['id'] for each in res.json['data']]
        assert_in(self.public._id, ids)
        assert_not_in(self.private._id, ids)

    def test_return_private_node_list_logged_out_user(self):
        res = self.app.get(self.url)
        ids = [each['id'] for each in res.json['data']]
        assert_in(self.public._id, ids)
        assert_not_in(self.private._id, ids)

    def test_return_private_node_list_logged_in_contributor(self):
        res = self.app.get(self.url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        ids = [each['id'] for each in res.json['data']]
        assert_in(self.public._id, ids)
        assert_in(self.private._id, ids)

    def test_return_private_node_list_logged_in_non_contributor(self):
        res = self.app.get(self.url, auth=self.basic_non_contrib_auth)
        ids = [each['id'] for each in res.json['data']]
        assert_in(self.public._id, ids)
        assert_not_in(self.private._id, ids)

        Node.remove()


class TestNodeFiltering(ApiTestCase):

    def setUp(self):
        super(TestNodeFiltering, self).setUp()
        self.user_one = UserFactory.build()
        self.user_one.set_password('justapoorboy')
        self.user_one.save()
        self.basic_auth_one = (self.user_one.username, 'justapoorboy')
        self.user_two = UserFactory.build()
        self.user_two.set_password('justapoorboy')
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, 'justapoorboy')
        self.project_one = ProjectFactory(title="Project One", is_public=True)
        self.project_two = ProjectFactory(title="Project Two", description="One Three", is_public=True)
        self.project_three = ProjectFactory(title="Three", is_public=True)
        self.private_project_user_one = ProjectFactory(title="Private Project User One",
                                                       is_public=False,
                                                       creator=self.user_one)
        self.private_project_user_two = ProjectFactory(title="Private Project User Two",
                                                       is_public=False,
                                                       creator=self.user_two)
        self.folder = FolderFactory()
        self.dashboard = DashboardFactory()

        self.url = "/{}nodes/".format(API_BASE)

    def tearDown(self):
        super(TestNodeFiltering, self).tearDown()
        Node.remove()

    def test_get_all_projects_with_no_filter_logged_in(self):
        res = self.app.get(self.url, auth=self.basic_auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_in(self.project_three._id, ids)
        assert_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_all_projects_with_no_filter_not_logged_in(self):
        res = self.app.get(self.url)
        node_json = res.json['data']
        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_one_project_with_exact_filter_logged_in(self):
        url = "/{}nodes/?filter[title]=Project%20One".format(API_BASE)

        res = self.app.get(url, auth=self.basic_auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_not_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_one_project_with_exact_filter_not_logged_in(self):
        url = "/{}nodes/?filter[title]=Project%20One".format(API_BASE)

        res = self.app.get(url)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_not_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_some_projects_with_substring_logged_in(self):
        url = "/{}nodes/?filter[title]=Two".format(API_BASE)

        res = self.app.get(url, auth=self.basic_auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_not_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_some_projects_with_substring_not_logged_in(self):
        url = "/{}nodes/?filter[title]=Two".format(API_BASE)

        res = self.app.get(url, auth=self.basic_auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_not_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_only_public_or_my_projects_with_filter_logged_in(self):
        url = "/{}nodes/?filter[title]=Project".format(API_BASE)

        res = self.app.get(url, auth=self.basic_auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_get_only_public_projects_with_filter_not_logged_in(self):
        url = "/{}nodes/?filter[title]=Project".format(API_BASE)

        res = self.app.get(url)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_alternate_filtering_field_logged_in(self):
        url = "/{}nodes/?filter[description]=Three".format(API_BASE)

        res = self.app.get(url, auth=self.basic_auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_not_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_alternate_filtering_field_not_logged_in(self):
        url = "/{}nodes/?filter[description]=Three".format(API_BASE)

        res = self.app.get(url)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_not_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_not_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_incorrect_filtering_field_logged_in(self):
        # TODO Change to check for error when the functionality changes. Currently acts as though it doesn't exist
        url = '/{}nodes/?filter[notafield]=bogus'.format(API_BASE)

        res = self.app.get(url, auth=self.basic_auth_one)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_in(self.project_three._id, ids)
        assert_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)

    def test_incorrect_filtering_field_not_logged_in(self):
        # TODO Change to check for error when the functionality changes. Currently acts as though it doesn't exist
        url = '/{}nodes/?filter[notafield]=bogus'.format(API_BASE)

        res = self.app.get(url)
        node_json = res.json['data']

        ids = [each['id'] for each in node_json]
        assert_in(self.project_one._id, ids)
        assert_in(self.project_two._id, ids)
        assert_in(self.project_three._id, ids)
        assert_not_in(self.private_project_user_one._id, ids)
        assert_not_in(self.private_project_user_two._id, ids)
        assert_not_in(self.folder._id, ids)
        assert_not_in(self.dashboard._id, ids)


class TestNodeCreate(ApiTestCase):

    def setUp(self):
        super(TestNodeCreate, self).setUp()
        self.user = UserFactory.build()
        self.user.set_password('justapoorboy')
        self.user.save()
        self.basic_auth = (self.user.username, 'justapoorboy')

        self.url = '/{}nodes/'.format(API_BASE)

        self.title = 'Cool Project'
        self.description = 'A Properly Cool Project'
        self.category = 'data'

        self.user_two = UserFactory.build()
        self.user_two.set_password('justapoorboy')
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, 'justapoorboy')

        self.public_project = {'title': self.title,
                               'description': self.description,
                               'category': self.category,
                               'public': True}
        self.private_project = {'title': self.title,
                                'description': self.description,
                                'category': self.category,
                                'public': False}

    def test_creates_public_project_logged_out(self):
        res = self.app.post_json(self.url, self.public_project, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_creates_public_project_logged_in(self):
        res = self.app.post_json(self.url, self.public_project, auth=self.basic_auth)
        assert_equal(res.status_code, 201)
        assert_equal(res.json['data']['title'], self.public_project['title'])
        assert_equal(res.json['data']['description'], self.public_project['description'])
        assert_equal(res.json['data']['category'], self.public_project['category'])

    def test_creates_private_project_logged_out(self):
        res = self.app.post_json(self.url, self.private_project, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_creates_private_project_logged_in_contributor(self):
        res = self.app.post_json(self.url, self.private_project, auth=self.basic_auth)
        assert_equal(res.status_code, 201)
        assert_equal(res.json['data']['title'], self.private_project['title'])
        assert_equal(res.json['data']['description'], self.private_project['description'])
        assert_equal(res.json['data']['category'], self.private_project['category'])

    def test_creates_project_creates_project_and_sanitizes_html(self):
        title = '<em>Cool</em> <strong>Project</strong>'
        description = 'An <script>alert("even cooler")</script> project'

        res = self.app.post_json(self.url, {
            'title': title,
            'description': description,
            'category': self.category,
            'public': True,
        }, auth=self.basic_auth)
        project_id = res.json['data']['id']
        assert_equal(res.status_code, 201)
        url = '/{}nodes/{}/'.format(API_BASE, project_id)
<<<<<<< HEAD
=======

>>>>>>> d7854c833fbc8530a0865851d2f51ce3d8af3798
        res = self.app.get(url, auth=self.basic_auth)
        assert_equal(res.json['data']['title'], strip_html(title))
        assert_equal(res.json['data']['description'], strip_html(description))
        assert_equal(res.json['data']['category'], self.category)


class TestNodeDetail(ApiTestCase):
    def setUp(self):
        super(TestNodeDetail, self).setUp()
        self.user = UserFactory.build()
        self.user.set_password('justapoorboy')
        self.user.save()
        self.basic_auth = (self.user.username, 'justapoorboy')

        self.user_two = UserFactory.build()
        self.user_two.set_password('justapoorboy')
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, 'justapoorboy')

        self.public_project = ProjectFactory(title="Project One", is_public=True, creator=self.user)
        self.private_project = ProjectFactory(title="Project Two", is_public=False, creator=self.user)
        self.public_url = '/{}nodes/{}/'.format(API_BASE, self.public_project._id)
        self.private_url = '/{}nodes/{}/'.format(API_BASE, self.private_project._id)

    def test_return_public_project_details_logged_out(self):
        res = self.app.get(self.public_url)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['title'], self.public_project.title)
        assert_equal(res.json['data']['description'], self.public_project.description)
        assert_equal(res.json['data']['category'], self.public_project.category)

    def test_return_public_project_details_logged_in(self):
        res = self.app.get(self.public_url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['title'], self.public_project.title)
        assert_equal(res.json['data']['description'], self.public_project.description)
        assert_equal(res.json['data']['category'], self.public_project.category)

    def test_return_private_project_details_logged_out(self):
        res = self.app.get(self.private_url, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_return_private_project_details_logged_in_contributor(self):
        res = self.app.get(self.private_url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['title'], self.private_project.title)
        assert_equal(res.json['data']['description'], self.private_project.description)
        assert_equal(res.json['data']['category'], self.private_project.category)

    def test_return_private_project_details_logged_in_non_contributor(self):
        res = self.app.get(self.private_url, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)


class TestNodeUpdate(ApiTestCase):

    def setUp(self):
        super(TestNodeUpdate, self).setUp()
        self.user = UserFactory.build()
        self.user.set_password('justapoorboy')
        self.user.save()
        self.basic_auth = (self.user.username, 'justapoorboy')

        self.title = 'Cool Project'
        self.new_title = 'Super Cool Project'
        self.description = 'A Properly Cool Project'
        self.new_description = 'An even cooler project'
        self.category = 'data'
        self.new_category = 'project'

        self.user_two = UserFactory.build()
        self.user_two.set_password('justapoorboy')
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, 'justapoorboy')

<<<<<<< HEAD
        self.public_project = ProjectFactory(title=self.title, description=self.description, category=self.category, is_public=True, creator=self.user)
        self.public_url = '/{}nodes/{}/'.format(API_BASE, self.public_project._id)

        self.private_project = ProjectFactory(title=self.title, description=self.description, category=self.category, is_public=False, creator=self.user)
=======
        self.public_project = ProjectFactory(title=self.title,
                                             description=self.description,
                                             category=self.category,
                                             is_public=True,
                                             creator=self.user)
        self.public_url = '/{}nodes/{}/'.format(API_BASE, self.public_project._id)

        self.private_project = ProjectFactory(title=self.title,
                                              description=self.description,
                                              category=self.category,
                                              is_public=False,
                                              creator=self.user)
>>>>>>> d7854c833fbc8530a0865851d2f51ce3d8af3798
        self.private_url = '/{}nodes/{}/'.format(API_BASE, self.private_project._id)

    def test_update_public_project_logged_out(self):
        res = self.app.put_json(self.public_url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': True,
        }, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_update_public_project_logged_in(self):
        # Public project, logged in, contrib
        res = self.app.put_json(self.public_url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': True,
        }, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['title'], self.new_title)
        assert_equal(res.json['data']['description'], self.new_description)
        assert_equal(res.json['data']['category'], self.new_category)

        # Public project, logged in, unauthorized
        res = self.app.put_json(self.public_url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': True,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_update_private_project_logged_out(self):
        res = self.app.put_json(self.private_url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': False,
        }, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_update_private_project_logged_in_contributor(self):
        res = self.app.put_json(self.private_url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': False,
        }, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['title'], self.new_title)
        assert_equal(res.json['data']['description'], self.new_description)
        assert_equal(res.json['data']['category'], self.new_category)

    def test_update_private_project_logged_in_non_contributor(self):
        res = self.app.put_json(self.private_url, {
            'title': self.new_title,
            'description': self.new_description,
            'category': self.new_category,
            'public': False,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_update_project_sanitizes_html_properly(self):
        """Post request should update resource, and any HTML in fields should be stripped"""
        new_title = '<strong>Super</strong> Cool Project'
        new_description = 'An <script>alert("even cooler")</script> project'
        project = self.project = ProjectFactory(
            title=self.title, description=self.description, category=self.category, is_public=True, creator=self.user)

        url = '/{}nodes/{}/'.format(API_BASE, project._id)
        res = self.app.put_json(url, {
            'title': new_title,
            'description': new_description,
            'category': self.new_category,
            'public': True,
        }, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['title'], strip_html(new_title))
        assert_equal(res.json['data']['description'], strip_html(new_description))

    def test_partial_update_project_updates_project_correctly_and_sanitizes_html(self):
        new_title = 'An <script>alert("even cooler")</script> project'
        project = self.project = ProjectFactory(
            title=self.title, description=self.description, category=self.category, is_public=True, creator=self.user)

        url = '/{}nodes/{}/'.format(API_BASE, project._id)
        res = self.app.patch_json(url, {
            'title': new_title,
        }, auth=self.basic_auth)
        assert_equal(res.status_code, 200)

        res = self.app.get(url)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['title'], strip_html(new_title))
        assert_equal(res.json['data']['description'], self.description)
        assert_equal(res.json['data']['category'], self.category)

    def test_writing_to_public_field(self):
        title = "Cool project"
        description = 'A Properly Cool Project'
        category = 'data'
        project = self.project = ProjectFactory(
            title=title, description=description, category=category, is_public=True, creator=self.user)
        # Test non-contrib writing to public field
        url = '/{}nodes/{}/'.format(API_BASE, project._id)
        res = self.app.patch_json(url, {
            'is_public': False,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)
        # Test creator writing to public field (supposed to be read-only)
        res = self.app.patch_json(url, {
            'is_public': False,
        }, auth=self.basic_auth, expect_errors=True)
        assert_true(res.json['data']['public'])
        # TODO: Figure out why the validator isn't raising when attempting to write to a read-only field
        # assert_equal(res.status_code, 403)

    def test_partial_update_public_project_logged_out(self):
        res = self.app.patch_json(self.public_url, {'title': self.new_title}, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_partial_update_public_project_logged_in(self):
        res = self.app.patch_json(self.public_url, {
            'title': self.new_title,
        }, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['title'], self.new_title)
        assert_equal(res.json['data']['description'], self.description)
        assert_equal(res.json['data']['category'], self.category)

        # Public resource, logged in, unauthorized
        res = self.app.patch_json(self.public_url, {
            'title': self.new_title,
        }, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_partial_update_private_project_logged_out(self):
        res = self.app.patch_json(self.private_url, {'title': self.new_title}, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_partial_update_private_project_logged_in_contributor(self):
        res = self.app.patch_json(self.private_url, {'title': self.new_title}, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data']['title'], self.new_title)
        assert_equal(res.json['data']['description'], self.description)
        assert_equal(res.json['data']['category'], self.category)

    def test_partial_update_private_project_logged_in_non_contributor(self):
        res = self.app.patch_json(self.private_url,
                                  {'title': self.new_title},
                                  auth=self.basic_auth_two,
                                  expect_errors=True)
        assert_equal(res.status_code, 403)


class TestNodeDelete(ApiTestCase):

    def setUp(self):
        super(TestNodeDelete, self).setUp()
        self.user = UserFactory.build()
        self.user.set_password('password')
        self.user.save()
        self.basic_auth = (self.user.username, 'password')

        self.project = ProjectFactory(creator=self.user, is_public=False)
        self.private_url = '/{}nodes/{}/'.format(API_BASE, self.project._id)

        self.user_two = UserFactory.build()
        self.user_two.set_password('password')
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, 'password')

        self.public_project = ProjectFactory(is_public=True, creator=self.user)
        self.public_url = '/{}nodes/{}/'.format(API_BASE, self.public_project._id)

        self.fake_url = '/{}nodes/{}/'.format(API_BASE, '12345')

    def test_deletes_public_node_logged_out(self):
        res = self.app.delete(self.public_url, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_deletes_public_node_fails_if_bad_auth(self):
        res = self.app.delete_json(self.public_url, auth=self.basic_auth_two, expect_errors=True)
        self.public_project.reload()
        assert_equal(res.status_code, 403)
        assert_equal(self.public_project.is_deleted, False)

    def test_deletes_public_node_succeeds_as_owner(self):
        res = self.app.delete_json(self.public_url, auth=self.basic_auth, expect_errors=True)
        self.public_project.reload()
        assert_equal(res.status_code, 204)
        assert_equal(self.public_project.is_deleted, True)

    def test_deletes_private_node_logged_out(self):
        res = self.app.delete(self.private_url, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_deletes_private_node_logged_in_contributor(self):
        res = self.app.delete(self.private_url, auth=self.basic_auth, expect_errors=True)
        self.project.reload()
        assert_equal(res.status_code, 204)
        assert_equal(self.project.is_deleted, True)

    def test_deletes_private_node_logged_in_non_contributor(self):
        res = self.app.delete(self.private_url, auth=self.basic_auth_two, expect_errors=True)
        self.project.reload()
        assert_equal(res.status_code, 403)
        assert_equal(self.project.is_deleted, False)

    def test_deletes_private_node_logged_in_read_only_contributor(self):
        self.project.add_contributor(self.user_two, permissions=['read'])
        self.project.save()
        res = self.app.delete(self.private_url, auth=self.basic_auth_two, expect_errors=True)
        self.project.reload()
        assert_equal(res.status_code, 403)
        assert_equal(self.project.is_deleted, False)

    def test_deletes_invalid_node(self):
        res = self.app.delete(self.fake_url, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)


class TestNodeContributorList(ApiTestCase):

    def setUp(self):
        super(TestNodeContributorList, self).setUp()
        self.user = UserFactory.build()
        password = fake.password()
        self.password = password
        self.user.set_password(password)
        self.user.save()
        self.basic_auth = (self.user.username, password)

        self.user_two = UserFactory.build()
        self.user_two.set_password(self.password)
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, self.password)

        self.private_project = ProjectFactory(is_public=False, creator=self.user)
        self.private_url = '/{}nodes/{}/contributors/'.format(API_BASE, self.private_project._id)
        self.public_project = ProjectFactory(is_public=True, creator=self.user)
        self.public_url = '/{}nodes/{}/contributors/'.format(API_BASE, self.public_project._id)

    def test_return_public_contributor_list_logged_out(self):
        self.public_project.add_contributor(self.user_two)
        self.public_project.save()

        res = self.app.get(self.public_url)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), 2)
        assert_equal(res.json['data'][0]['id'], self.user._id)
        assert_equal(res.json['data'][1]['id'], self.user_two._id)

    def test_return_public_contributor_list_logged_in(self):
        res = self.app.get(self.public_url, auth=self.basic_auth_two)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), 1)
        assert_equal(res.json['data'][0]['id'], self.user._id)

    def test_return_private_contributor_list_logged_out(self):
        res = self.app.get(self.private_url, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_return_private_contributor_list_logged_in_contributor(self):
        self.private_project.add_contributor(self.user_two)
        self.private_project.save()

        res = self.app.get(self.private_url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), 2)
        assert_equal(res.json['data'][0]['id'], self.user._id)
        assert_equal(res.json['data'][1]['id'], self.user_two._id)

    def test_return_private_contributor_list_logged_in_non_contributor(self):
        res = self.app.get(self.private_url, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)


class TestNodeContributorFiltering(ApiTestCase):

    def setUp(self):
        super(TestNodeContributorFiltering, self).setUp()
        self.project = ProjectFactory()
        self.password = fake.password()
        self.project.creator.set_password(self.password)
        self.project.creator.save()
        self.basic_auth = (self.project.creator.username, self.password)

    def test_filtering_node_with_only_bibliographic_contributors(self):

        base_url = '/{}nodes/{}/contributors/'.format(API_BASE, self.project._id)
        # no filter
        res = self.app.get(base_url, auth=self.basic_auth)
        assert_equal(len(res.json['data']), 1)

        # filter for bibliographic contributors
        url = base_url + '?filter[bibliographic]=True'
        res = self.app.get(url, auth=self.basic_auth)
        assert_equal(len(res.json['data']), 1)
        assert_true(res.json['data'][0].get('bibliographic', None))

        # filter for non-bibliographic contributors
        url = base_url + '?filter[bibliographic]=False'
        res = self.app.get(url, auth=self.basic_auth)
        assert_equal(len(res.json['data']), 0)

    def test_filtering_node_with_non_bibliographic_contributor(self):
        non_bibliographic_contrib = UserFactory()
        self.project.add_contributor(non_bibliographic_contrib, visible=False)
        self.project.save()

<<<<<<< HEAD
        base_url = base_url = '/{}nodes/{}/contributors/'.format(API_BASE, self.project._id)
=======
        base_url = '/{}nodes/{}/contributors/'.format(API_BASE, self.project._id)
>>>>>>> d7854c833fbc8530a0865851d2f51ce3d8af3798

        # no filter
        res = self.app.get(base_url, auth=self.basic_auth)
        assert_equal(len(res.json['data']), 2)

        # filter for bibliographic contributors
        url = base_url + '?filter[bibliographic]=True'
        res = self.app.get(url, auth=self.basic_auth)
        assert_equal(len(res.json['data']), 1)
        assert_true(res.json['data'][0].get('bibliographic', None))

        # filter for non-bibliographic contributors
        url = base_url + '?filter[bibliographic]=False'
        res = self.app.get(url, auth=self.basic_auth)
        assert_equal(len(res.json['data']), 1)
        assert_false(res.json['data'][0].get('bibliographic', None))


class TestNodeRegistrationList(ApiTestCase):
    def setUp(self):
        super(TestNodeRegistrationList, self).setUp()
        self.user = UserFactory.build()
        password = fake.password()
        self.password = password
        self.user.set_password(password)
        self.user.save()
        self.basic_auth = (self.user.username, password)
        self.project = ProjectFactory(is_public=False, creator=self.user)
        self.registration_project = RegistrationFactory(creator=self.user, project=self.project)
        self.project.save()
        self.private_url = '/{}nodes/{}/registrations/'.format(API_BASE, self.project._id)

        self.public_project = ProjectFactory(is_public=True, creator=self.user)
        self.public_registration_project = RegistrationFactory(creator=self.user, project=self.public_project)
        self.public_project.save()
        self.public_url = '/{}nodes/{}/registrations/'.format(API_BASE, self.public_project._id)

        self.user_two = UserFactory.build()
        self.user_two.set_password(password)
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, password)

    def test_return_public_registrations_logged_out(self):
        res = self.app.get(self.public_url)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data'][0]['title'], self.public_project.title)

    def test_return_public_registrations_logged_in(self):
        res = self.app.get(self.public_url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data'][0]['category'], self.public_project.category)

    def test_return_private_registrations_logged_out(self):
        res = self.app.get(self.private_url, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_return_private_registrations_logged_in_contributor(self):
        res = self.app.get(self.private_url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data'][0]['category'], self.project.category)

    def test_return_private_registrations_logged_in_non_contributor(self):
        res = self.app.get(self.private_url, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)


class TestNodeChildrenList(ApiTestCase):
    def setUp(self):
        super(TestNodeChildrenList, self).setUp()
        self.user = UserFactory.build()
        password = fake.password()
        self.password = password
        self.user.set_password(password)
        self.user.save()
        self.basic_auth = (self.user.username, password)
        self.project = ProjectFactory()
        self.project.add_contributor(self.user, permissions=['read', 'write'])
        self.project.save()
        self.component = NodeFactory(parent=self.project, creator=self.user)
        self.pointer = ProjectFactory()
        self.project.add_pointer(self.pointer, auth=Auth(self.user), save=True)
        self.private_project_url = '/{}nodes/{}/children/'.format(API_BASE, self.project._id)

        self.public_project = ProjectFactory(is_public=True, creator=self.user)
        self.public_project.save()
        self.public_component = NodeFactory(parent=self.public_project, creator=self.user, is_public=True)
        self.public_project_url = '/{}nodes/{}/children/'.format(API_BASE, self.public_project._id)

        self.user_two = UserFactory.build()
        self.user_two.set_password(password)
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, password)

    def test_node_children_list_does_not_include_pointers(self):
        res = self.app.get(self.private_project_url, auth=self.basic_auth)
        assert_equal(len(res.json['data']), 1)

    def test_return_public_node_children_list_logged_out(self):
        res = self.app.get(self.public_project_url)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), 1)
        assert_equal(res.json['data'][0]['id'], self.public_component._id)

    def test_return_public_node_children_list_logged_in(self):
        res = self.app.get(self.public_project_url, auth=self.basic_auth_two)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), 1)
        assert_equal(res.json['data'][0]['id'], self.public_component._id)

    def test_return_private_node_children_list_logged_out(self):
        res = self.app.get(self.private_project_url, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_return_private_node_children_list_logged_in_contributor(self):
        res = self.app.get(self.private_project_url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), 1)
        assert_equal(res.json['data'][0]['id'], self.component._id)

    def test_return_private_node_children_list_logged_in_non_contributor(self):
        res = self.app.get(self.private_project_url, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_node_children_list_does_not_include_unauthorized_projects(self):
        private_component = NodeFactory(parent=self.project)
        res = self.app.get(self.private_project_url, auth=self.basic_auth)
        assert_equal(len(res.json['data']), 1)

        Node.remove()


class TestNodePointersList(ApiTestCase):

    def setUp(self):
        super(TestNodePointersList, self).setUp()
        self.user = UserFactory.build()
        self.user.set_password('password')
        self.user.save()
        self.basic_auth = (self.user.username, 'password')
        self.project = ProjectFactory(is_public=False, creator=self.user)
        self.pointer_project = ProjectFactory(is_public=False, creator=self.user)
        self.project.add_pointer(self.pointer_project, auth=Auth(self.user))
        self.private_url = '/{}nodes/{}/pointers/'.format(API_BASE, self.project._id)

        self.public_project = ProjectFactory(is_public=True, creator=self.user)
        self.public_pointer_project = ProjectFactory(is_public=True, creator=self.user)
        self.public_project.add_pointer(self.public_pointer_project, auth=Auth(self.user))
        self.public_url = '/{}nodes/{}/pointers/'.format(API_BASE, self.public_project._id)

        self.user_two = UserFactory.build()
        self.user_two.set_password('password')
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, 'password')

    def test_return_public_node_pointers_logged_out(self):
        res = self.app.get(self.public_url)
        res_json = res.json['data']
        assert_equal(len(res_json), 1)
        assert_equal(res.status_code, 200)
        assert_in(res_json[0]['node_id'], self.public_pointer_project._id)

    def test_return_public_node_pointers_logged_in(self):
        res = self.app.get(self.public_url, auth=self.basic_auth_two)
        res_json = res.json['data']
        assert_equal(len(res_json), 1)
        assert_equal(res.status_code, 200)
        assert_in(res_json[0]['node_id'], self.public_pointer_project._id)

    def test_return_private_node_pointers_logged_out(self):
        res = self.app.get(self.private_url, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_return_private_node_pointers_logged_in_contributor(self):
        res = self.app.get(self.private_url, auth=self.basic_auth)
        res_json = res.json['data']
        assert_equal(res.status_code, 200)
        assert_equal(len(res_json), 1)
        assert_in(res_json[0]['node_id'], self.pointer_project._id)

    def test_return_private_node_pointers_logged_in_non_contributor(self):
        res = self.app.get(self.private_url, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)


class TestCreateNodePointer(ApiTestCase):
    def setUp(self):
        super(TestCreateNodePointer, self).setUp()
        self.user = UserFactory.build()
        self.user.set_password('password')
        self.user.save()
        self.basic_auth = (self.user.username, 'password')
        self.project = ProjectFactory(is_public=False, creator=self.user)
        self.pointer_project = ProjectFactory(is_public=False, creator=self.user)
        self.private_url = '/{}nodes/{}/pointers/'.format(API_BASE, self.project._id)
        self.private_payload = {'node_id': self.pointer_project._id}

        self.public_project = ProjectFactory(is_public=True, creator=self.user)
        self.public_pointer_project = ProjectFactory(is_public=True, creator=self.user)
        self.public_url = '/{}nodes/{}/pointers/'.format(API_BASE, self.public_project._id)
        self.public_payload = {'node_id': self.public_pointer_project._id}
        self.fake_url = '/{}nodes/{}/pointers/'.format(API_BASE, 'fdxlq')
        self.fake_payload = {'node_id': 'fdxlq'}
<<<<<<< HEAD
        self.point_to_itself_payload = {'node_id': self.public_project._id }
=======
        self.point_to_itself_payload = {'node_id': self.public_project._id}
>>>>>>> d7854c833fbc8530a0865851d2f51ce3d8af3798

        self.user_two = UserFactory.build()
        self.user_two.set_password('password')
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, 'password')

        self.user_two_project = ProjectFactory(is_public=True, creator=self.user_two)
        self.user_two_url = '/{}nodes/{}/pointers/'.format(API_BASE, self.user_two_project._id)
        self.user_two_payload = {'node_id': self.user_two_project._id}

    def test_creates_public_node_pointer_logged_out(self):
        res = self.app.post(self.public_url, self.public_payload, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_creates_public_node_pointer_logged_in(self):
        res = self.app.post(self.public_url, self.public_payload, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

        res = self.app.post(self.public_url, self.public_payload, auth=self.basic_auth)
        assert_equal(res.status_code, 201)
        assert_equal(res.json['data']['node_id'], self.public_pointer_project._id)

    def test_creates_private_node_pointer_logged_out(self):
        res = self.app.post(self.private_url, self.private_payload, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_creates_private_node_pointer_logged_in_contributor(self):
        res = self.app.post(self.private_url, self.private_payload, auth=self.basic_auth)
        assert_equal(res.status_code, 201)
        assert_equal(res.json['data']['node_id'], self.pointer_project._id)

    def test_creates_private_node_pointer_logged_in_non_contributor(self):
        res = self.app.post(self.private_url, self.private_payload, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_create_node_pointer_non_contributing_node_to_contributing_node(self):
        res = self.app.post(self.private_url, self.user_two_payload, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_create_node_pointer_contributing_node_to_non_contributing_node(self):
        res = self.app.post(self.private_url, self.user_two_payload, auth=self.basic_auth)
        assert_equal(res.status_code, 201)
        assert_equal(res.json['data']['node_id'], self.user_two_project._id)

    def test_create_pointer_non_contributing_node_to_fake_node(self):
        res = self.app.post(self.private_url, self.fake_payload, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_create_pointer_contributing_node_to_fake_node(self):
        res = self.app.post(self.private_url, self.fake_payload, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_create_fake_node_pointing_to_contributing_node(self):
        res = self.app.post(self.fake_url, self.private_payload, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 404)

        res = self.app.post(self.fake_url, self.private_payload, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 404)

    def test_create_node_pointer_to_itself(self):
        res = self.app.post(self.public_url, self.point_to_itself_payload, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

        res = self.app.post(self.public_url, self.point_to_itself_payload, auth=self.basic_auth)
        assert_equal(res.status_code, 201)
        assert_equal(res.json['data']['node_id'], self.public_project._id)

    def test_create_node_pointer_already_connected(self):
        res = self.app.post(self.public_url, self.public_payload, auth=self.basic_auth)
        assert_equal(res.status_code, 201)
        assert_equal(res.json['data']['node_id'], self.public_pointer_project._id)

        res = self.app.post(self.public_url, self.public_payload, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 400)


class TestNodeFilesList(ApiTestCase):

    def setUp(self):
        super(TestNodeFilesList, self).setUp()
        self.user = UserFactory.build()
        self.user.set_password('justapoorboy')
        self.user.save()
        self.basic_auth = (self.user.username, 'justapoorboy')
        self.project = ProjectFactory(creator=self.user)
<<<<<<< HEAD
        self.private_url = url = '/{}nodes/{}/files/'.format(API_BASE, self.project._id)
=======
        self.private_url = '/{}nodes/{}/files/'.format(API_BASE, self.project._id)
>>>>>>> d7854c833fbc8530a0865851d2f51ce3d8af3798

        self.user_two = UserFactory.build()
        self.user_two.set_password('justapoorboy')
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, 'justapoorboy')

        self.public_project = ProjectFactory(creator=self.user, is_public=True)
        self.public_url = '/{}nodes/{}/files/'.format(API_BASE, self.public_project._id)

    def test_returns_public_files_logged_out(self):
        res = self.app.get(self.public_url, expect_errors=True)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data'][0]['provider'], 'osfstorage')

    def test_returns_public_files_logged_in(self):
        res = self.app.get(self.public_url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(res.json['data'][0]['provider'], 'osfstorage')

    def test_returns_private_files_logged_out(self):
        res = self.app.get(self.private_url, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_returns_private_files_logged_in_contributor(self):
        res = self.app.get(self.private_url, auth=self.basic_auth)
        assert_equal(res.status_code, 200)
        assert_equal(len(res.json['data']), 1)
        assert_equal(res.json['data'][0]['provider'], 'osfstorage')

    def test_returns_private_files_logged_in_non_contributor(self):
        res = self.app.get(self.private_url, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)

    def test_returns_addon_folders(self):
        user_auth = Auth(self.user)
        res = self.app.get(self.private_url, auth=self.basic_auth)
        assert_equal(len(res.json['data']), 1)
        assert_equal(res.json['data'][0]['provider'], 'osfstorage')

        self.project.add_addon('github', auth=user_auth)
        self.project.save()
        res = self.app.get(self.private_url, auth=self.basic_auth)
        data = res.json['data']
        providers = [item['provider'] for item in data]
        assert_equal(len(data), 2)
        assert_in('github', providers)
        assert_in('osfstorage', providers)

    @mock.patch('api.nodes.views.requests.get')
    def test_returns_node_files_list(self, mock_waterbutler_request):
        mock_res = mock.MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {
            u'data': [{
                u'contentType': None,
                u'extra': {u'downloads': 0, u'version': 1},
                u'kind': u'file',
                u'modified': None,
                u'name': u'NewFile',
                u'path': u'/',
                u'provider': u'osfstorage',
                u'size': None
            }]
        }
        mock_waterbutler_request.return_value = mock_res
<<<<<<< HEAD
=======

>>>>>>> d7854c833fbc8530a0865851d2f51ce3d8af3798
        url = '/{}nodes/{}/files/?path=%2F&provider=osfstorage'.format(API_BASE, self.project._id)
        res = self.app.get(url, auth=self.basic_auth)
        assert_equal(res.json['data'][0]['name'], 'NewFile')
        assert_equal(res.json['data'][0]['provider'], 'osfstorage')

    @mock.patch('api.nodes.views.requests.get')
    def test_handles_unauthenticated_waterbutler_request(self, mock_waterbutler_request):
        url = '/{}nodes/{}/files/?path=%2F&provider=osfstorage'.format(API_BASE, self.project._id)
        mock_res = mock.MagicMock()
        mock_res.status_code = 401
        mock_waterbutler_request.return_value = mock_res
        res = self.app.get(url, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 403)

    @mock.patch('api.nodes.views.requests.get')
    def test_handles_bad_waterbutler_request(self, mock_waterbutler_request):
        url = '/{}nodes/{}/files/?path=%2F&provider=osfstorage'.format(API_BASE, self.project._id)
        mock_res = mock.MagicMock()
        mock_res.status_code = 418
        mock_res.json.return_value = {}
        mock_waterbutler_request.return_value = mock_res
        res = self.app.get(url, auth=self.basic_auth, expect_errors=True)
        assert_equal(res.status_code, 400)


class TestNodePointerDetail(ApiTestCase):

    def setUp(self):
        super(TestNodePointerDetail, self).setUp()
        self.user = UserFactory.build()
        self.user.set_password('password')
        self.user.save()
        self.basic_auth = (self.user.username, 'password')
        self.private_project = ProjectFactory(creator=self.user, is_public=False)
        self.pointer_project = ProjectFactory(creator=self.user, is_public=False)
        self.pointer = self.private_project.add_pointer(self.pointer_project, auth=Auth(self.user), save=True)
        self.private_url = '/{}nodes/{}/pointers/{}'.format(API_BASE, self.private_project._id, self.pointer._id)

        self.user_two = UserFactory.build()
        self.user_two.set_password('password')
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, 'password')

        self.public_project = ProjectFactory(is_public=True)
        self.public_pointer_project = ProjectFactory(is_public=True)
<<<<<<< HEAD
        self.public_pointer = self.public_project.add_pointer(self.public_pointer_project, auth= Auth(self.user), save=True)
=======
        self.public_pointer = self.public_project.add_pointer(self.public_pointer_project,
                                                              auth=Auth(self.user),
                                                              save=True)
>>>>>>> d7854c833fbc8530a0865851d2f51ce3d8af3798
        self.public_url = '/{}nodes/{}/pointers/{}'.format(API_BASE, self.public_project._id, self.public_pointer._id)

    def test_returns_public_node_pointer_detail_logged_out(self):
        res = self.app.get(self.public_url)
        assert_equal(res.status_code, 200)
        res_json = res.json['data']
        assert_equal(res_json['node_id'], self.public_pointer_project._id)

    def test_returns_public_node_pointer_detail_logged_in(self):
        res = self.app.get(self.public_url, auth=self.basic_auth)
        res_json = res.json['data']
        assert_equal(res.status_code, 200)
        assert_equal(res_json['node_id'], self.public_pointer_project._id)

    def test_returns_private_node_pointer_detail_logged_out(self):
        res = self.app.get(self.private_url, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_returns_private_node_pointer_detail_logged_in_contributor(self):
        res = self.app.get(self.private_url, auth=self.basic_auth)
        res_json = res.json['data']
        assert_equal(res.status_code, 200)
        assert_equal(res_json['node_id'], self.pointer_project._id)

    def returns_private_node_pointer_detail_logged_in_non_contributor(self):
        res = self.app.get(self.private_url, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)


class TestDeleteNodePointer(ApiTestCase):

    def setUp(self):
        super(TestDeleteNodePointer, self).setUp()
        self.user = UserFactory.build()
        self.user.set_password('password')
        self.user.save()
        self.basic_auth = (self.user.username, 'password')
        self.project = ProjectFactory(creator=self.user, is_public=False)
        self.pointer_project = ProjectFactory(creator=self.user, is_public=True)
        self.pointer = self.project.add_pointer(self.pointer_project, auth=Auth(self.user), save=True)
        self.private_url = '/{}nodes/{}/pointers/{}'.format(API_BASE, self.project._id, self.pointer._id)

        self.user_two = UserFactory.build()
        self.user_two.set_password('password')
        self.user_two.save()
        self.basic_auth_two = (self.user_two.username, 'password')

        self.public_project = ProjectFactory(is_public=True, creator=self.user)
        self.public_pointer_project = ProjectFactory(is_public=True, creator=self.user)
<<<<<<< HEAD
        self.public_pointer = self.public_project.add_pointer(self.public_pointer_project, auth= Auth(self.user), save=True)
=======
        self.public_pointer = self.public_project.add_pointer(self.public_pointer_project,
                                                              auth=Auth(self.user),
                                                              save=True)
>>>>>>> d7854c833fbc8530a0865851d2f51ce3d8af3798
        self.public_url = '/{}nodes/{}/pointers/{}'.format(API_BASE, self.public_project._id, self.public_pointer._id)

    def test_deletes_public_node_pointer_logged_out(self):
        res = self.app.delete(self.public_url, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_deletes_public_node_pointer_fails_if_bad_auth(self):
        node_count_before = len(self.public_project.nodes_pointer)
        res = self.app.delete(self.public_url, auth=self.basic_auth_two, expect_errors=True)
        self.public_project.reload()
        # This is could arguably be a 405, but we don't need to go crazy with status codes
        assert_equal(res.status_code, 403)
        assert_equal(node_count_before, len(self.public_project.nodes_pointer))

    def test_deletes_public_node_pointer_succeeds_as_owner(self):
        node_count_before = len(self.public_project.nodes_pointer)
        res = self.app.delete(self.public_url, auth=self.basic_auth)
        self.public_project.reload()
        assert_equal(res.status_code, 204)
        assert_equal(node_count_before - 1, len(self.public_project.nodes_pointer))

    def test_deletes_private_node_pointer_logged_out(self):
        res = self.app.delete(self.private_url, expect_errors=True)
        # This is 403 instead of 401 because basic authentication is only for unit tests and, in order to keep from
        # presenting a basic authentication dialog box in the front end. We may change this as we understand CAS
        # a little better
        assert_equal(res.status_code, 403)

    def test_deletes_private_node_pointer_logged_in_contributor(self):
        res = self.app.delete(self.private_url, auth=self.basic_auth)
        self.project.reload()  # Update the model to reflect changes made by post request
        assert_equal(res.status_code, 204)
        assert_equal(len(self.project.nodes_pointer), 0)

    def test_deletes_private_node_pointer_logged_in_non_contributor(self):
<<<<<<< HEAD
        url = '/{}nodes/{}/pointers/'.format(API_BASE, self.project._id)
        payload = {'node_id': self.project._id}
        res = self.app.post(url, payload, auth=self.basic_auth)

        res = self.app.delete(url, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 405)
=======
        res = self.app.delete(self.private_url, auth=self.basic_auth_two, expect_errors=True)
        assert_equal(res.status_code, 403)
>>>>>>> d7854c833fbc8530a0865851d2f51ce3d8af3798
