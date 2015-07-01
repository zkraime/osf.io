# -*- coding: utf-8 -*-

from __future__ import division

import re
import copy
import math
import logging
import unicodedata

import six

from elasticsearch import (
    Elasticsearch,
    RequestError,
    NotFoundError,
    ConnectionError,
    helpers,
)

from framework import sentry

from website import settings
from website.filters import gravatar
from website.models import User, Node
from website.search import exceptions
from website.search.util import build_query
from website.util import sanitize

logger = logging.getLogger(__name__)


# These are the doc_types that exist in the search database
ALIASES = {
    'project': 'Projects',
    'component': 'Components',
    'registration': 'Registrations',
    'user': 'Users',
    'total': 'Total'
}

# Prevent tokenizing and stop word removal.
NOT_ANALYZED_PROPERTY = {'type': 'string', 'index': 'not_analyzed'}

# Perform stemming on the field it's applied to.
ENGLISH_ANALYZER_PROPERTY = {'type': 'string', 'analyzer': 'english'}

INDEX = settings.ELASTIC_INDEX

try:
    es = Elasticsearch(
        settings.ELASTIC_URI,
        request_timeout=settings.ELASTIC_TIMEOUT
    )
    logging.getLogger('elasticsearch').setLevel(logging.WARN)
    logging.getLogger('elasticsearch.trace').setLevel(logging.WARN)
    logging.getLogger('urllib3').setLevel(logging.WARN)
    logging.getLogger('requests').setLevel(logging.WARN)
    es.cluster.health(wait_for_status='yellow')
except ConnectionError as e:
    sentry.log_exception()
    sentry.log_message("The SEARCH_ENGINE setting is set to 'elastic', but there "
            "was a problem starting the elasticsearch interface. Is "
            "elasticsearch running?")
    es = None


def requires_search(func):
    def wrapped(*args, **kwargs):
        if es is not None:
            try:
                return func(*args, **kwargs)
            except ConnectionError:
                raise exceptions.SearchUnavailableError('Could not connect to elasticsearch')
            except NotFoundError as e:
                raise exceptions.IndexNotFoundError(e.error)
            except RequestError as e:
                if 'ParseException' in e.error:
                    raise exceptions.MalformedQueryError(e.error)
                raise exceptions.SearchException(e.error)

        sentry.log_message('Elastic search action failed. Is elasticsearch running?')
        raise exceptions.SearchUnavailableError("Failed to connect to elasticsearch")
    return wrapped


@requires_search
def get_counts(count_query, clean=True):
    count_query['aggregations'] = {
        'counts': {
            'terms': {
                'field': '_type',
            }
        }
    }

    res = es.search(index=INDEX, doc_type=None, search_type='count', body=count_query)

    counts = {x['key']: x['doc_count'] for x in res['aggregations']['counts']['buckets'] if x['key'] in ALIASES.keys()}

    counts['total'] = sum([val for val in counts.values()])
    return counts


@requires_search
def get_tags(query, index):
    query['aggregations'] = {
        'tag_cloud': {
            'terms': {'field': 'tags'}
        }
    }

    results = es.search(index=index, doc_type=None, body=query)
    tags = results['aggregations']['tag_cloud']['buckets']

    return tags


@requires_search
def search(query, index=None, doc_type='_all'):
    """Search for a query

    :param query: The substring of the username/project name/tag to search for
    :param index:
    :param doc_type:

    :return: List of dictionaries, each containing the results, counts, tags and typeAliases
        results: All results returned by the query, that are within the index and search type
        counts: A dictionary in which keys are types and values are counts for that type, e.g, count['total'] is the sum of the other counts
        tags: A list of tags that are returned by the search query
        typeAliases: the doc_types that exist in the search database
    """
    index = index or INDEX
    tag_query = copy.deepcopy(query)
    count_query = copy.deepcopy(query)

    for key in ['from', 'size', 'sort']:
        try:
            del tag_query[key]
            del count_query[key]
        except KeyError:
            pass

    tags = get_tags(tag_query, index)
    counts = get_counts(count_query, index)

    # Run the real query and get the results
    raw_results = es.search(index=index, doc_type=doc_type, body=query)

    results = [hit['_source'] for hit in raw_results['hits']['hits']]
    return_value = {
        'results': format_results(results),
        'counts': counts,
        'tags': tags,
        'typeAliases': ALIASES
    }
    return return_value


def format_results(results):
    ret = []
    for result in results:
        if result.get('category') == 'user':
            result['url'] = '/profile/' + result['id']
        elif result.get('category') in {'project', 'component', 'registration'}:
            result = format_result(result, result.get('parent_id'))
        ret.append(result)
    return ret


def format_result(result, parent_id=None):
    parent_info = load_parent(parent_id)
    formatted_result = {
        'contributors': result['contributors'],
        'wiki_link': result['url'] + 'wiki/',
        # TODO: Remove safe_unescape_html when mako html safe comes in
        'title': sanitize.safe_unescape_html(result['title']),
        'url': result['url'],
        'is_component': False if parent_info is None else True,
        'parent_title': sanitize.safe_unescape_html(parent_info.get('title')) if parent_info else None,
        'parent_url': parent_info.get('url') if parent_info is not None else None,
        'tags': result['tags'],
        'is_registration': (result['is_registration'] if parent_info is None
                                                        else parent_info.get('is_registration')),
        'is_retracted': result['is_retracted'],
        'pending_retraction': result['pending_retraction'],
        'embargo_end_date': result['embargo_end_date'],
        'pending_embargo': result['pending_embargo'],
        'description': result['description'] if parent_info is None else None,
        'category': result.get('category'),
        'date_created': result.get('date_created'),
        'date_registered': result.get('registration_date')
    }

    return formatted_result


def load_parent(parent_id):
    parent = Node.load(parent_id)
    if parent is None:
        return None
    parent_info = {}
    if parent is not None and parent.is_public:
        parent_info['title'] = parent.title
        parent_info['url'] = parent.url
        parent_info['is_registration'] = parent.is_registration
        parent_info['id'] = parent._id
    else:
        parent_info['title'] = '-- private project --'
        parent_info['url'] = ''
        parent_info['is_registration'] = None
        parent_info['id'] = None
    return parent_info


COMPONENT_CATEGORIES = set([k for k in Node.CATEGORY_MAP.keys() if not k == 'project'])

def get_doctype_from_node(node):

    if node.category in COMPONENT_CATEGORIES:
        return 'component'
    elif node.is_registration:
        return 'registration'
    else:
        return node.category


@requires_search
def update_node(node, index=None):
    index = index or INDEX
    from website.addons.wiki.model import NodeWikiPage

    category = get_doctype_from_node(node)

    if category == 'project':
        elastic_document_id = node._id
        parent_id = None
    else:
        try:
            elastic_document_id = node._id
            parent_id = node.parent_id
        except IndexError:
            # Skip orphaned components
            return
    if node.is_deleted or not node.is_public or node.archiving:
        delete_doc(elastic_document_id, node)
    else:
        try:
            normalized_title = six.u(node.title)
        except TypeError:
            normalized_title = node.title
        normalized_title = unicodedata.normalize('NFKD', normalized_title).encode('ascii', 'ignore')

        elastic_document = {
            'id': elastic_document_id,
            'contributors': [
                {
                    'fullname': x.fullname,
                    'url': x.profile_url if x.is_active else None
                }
                for x in node.visible_contributors
                if x is not None
            ],
            'title': node.title,
            'normalized_title': normalized_title,
            'category': category,
            'public': node.is_public,
            'tags': [tag._id for tag in node.tags if tag],
            'description': node.description,
            'url': node.url,
            'is_registration': node.is_registration,
            'is_retracted': node.is_retracted,
            'pending_retraction': node.pending_retraction,
            'embargo_end_date': node.embargo_end_date.strftime("%A, %b. %d, %Y") if node.embargo_end_date else False,
            'pending_embargo': node.pending_embargo,
            'registered_date': node.registered_date,
            'wikis': {},
            'parent_id': parent_id,
            'date_created': node.date_created,
            'boost': int(not node.is_registration) + 1,  # This is for making registered projects less relevant
        }

        if not node.is_retracted:
            for wiki in [
                NodeWikiPage.load(x)
                for x in node.wiki_pages_current.values()
            ]:
                elastic_document['wikis'][wiki.page_name] = wiki.raw_text(node)

        es.index(index=index, doc_type=category, id=elastic_document_id, body=elastic_document, refresh=True)


def bulk_update_contributors(nodes, index=INDEX):
    """Updates only the list of contributors of input projects

    :param nodes: Projects, components or registrations
    :param index: Index of the nodes
    :return:
    """
    actions = []
    for node in nodes:
        actions.append({
            '_op_type': 'update',
            '_index': index,
            '_id': node._id,
            '_type': get_doctype_from_node(node),
            'doc': {
                'contributors': [
                    {
                        'fullname': user.fullname,
                        'url': user.profile_url if user.is_active else None
                    } for user in node.visible_contributors
                    if user is not None
                    and user.is_active
                ]
            }
        })
    return helpers.bulk(es, actions)


@requires_search
def update_user(user, index=None):
    index = index or INDEX
    if not user.is_active:
        try:
            es.delete(index=index, doc_type='user', id=user._id, refresh=True, ignore=[404])
        except NotFoundError:
            pass
        return

    names = dict(
        fullname=user.fullname,
        given_name=user.given_name,
        family_name=user.family_name,
        middle_names=user.middle_names,
        suffix=user.suffix
    )

    normalized_names = {}
    for key, val in names.items():
        if val is not None:
            try:
                val = six.u(val)
            except TypeError:
                pass  # This is fine, will only happen in 2.x if val is already unicode
            normalized_names[key] = unicodedata.normalize('NFKD', val).encode('ascii', 'ignore')

    user_doc = {
        'id': user._id,
        'user': user.fullname,
        'normalized_user': normalized_names['fullname'],
        'normalized_names': normalized_names,
        'names': names,
        'job': user.jobs[0]['institution'] if user.jobs else '',
        'job_title': user.jobs[0]['title'] if user.jobs else '',
        'school': user.schools[0]['institution'] if user.schools else '',
        'category': 'user',
        'degree': user.schools[0]['degree'] if user.schools else '',
        'social': user.social_links,
        'boost': 2,  # TODO(fabianvf): Probably should make this a constant or something
    }

    es.index(index=index, doc_type='user', body=user_doc, id=user._id, refresh=True)


@requires_search
def delete_all():
    delete_index(INDEX)


@requires_search
def delete_index(index):
    es.indices.delete(index, ignore=[404])


@requires_search
def create_index(index=None):
    '''Creates index with some specified mappings to begin with,
    all of which are applied to all projects, components, and registrations.
    '''
    index = index or INDEX
    document_types = ['project', 'component', 'registration', 'user']
    project_like_types = ['project', 'component', 'registration']
    analyzed_fields = ['title', 'description']

    es.indices.create(index, ignore=[400])
    for type_ in document_types:
        mapping = {'properties': {'tags': NOT_ANALYZED_PROPERTY}}
        if type_ in project_like_types:
            analyzers = {field: ENGLISH_ANALYZER_PROPERTY
                         for field in analyzed_fields}
            mapping['properties'].update(analyzers)

        es.indices.put_mapping(index=index, doc_type=type_, body=mapping, ignore=[400, 404])


@requires_search
def delete_doc(elastic_document_id, node, index=None, category=None):
    index = index or INDEX
    category = category or 'registration' if node.is_registration else node.project_or_component
    es.delete(index=index, doc_type=category, id=elastic_document_id, refresh=True, ignore=[404])


@requires_search
def search_contributor(query, page=0, size=10, exclude=None, current_user=None):
    """Search for contributors to add to a project using elastic search. Request must
    include JSON data with a "query" field.

    :param query: The substring of the username to search for
    :param page: For pagination, the page number to use for results
    :param size: For pagination, the number of results per page
    :param exclude: A list of User objects to exclude from the search
    :param current_user: A User object of the current user

    :return: List of dictionaries, each containing the ID, full name,
        most recent employment and education, gravatar URL of an OSF user

    """
    start = (page * size)
    items = re.split(r'[\s-]+', query)
    exclude = exclude or []
    normalized_items = []
    for item in items:
        try:
            normalized_item = six.u(item)
        except TypeError:
            normalized_item = item
        normalized_item = unicodedata.normalize('NFKD', normalized_item).encode('ascii', 'ignore')
        normalized_items.append(normalized_item)
    items = normalized_items

    query = ''

    query = "  AND ".join('{}*~'.format(re.escape(item)) for item in items) + \
            "".join(' NOT id:"{}"'.format(excluded._id) for excluded in exclude)

    results = search(build_query(query, start=start, size=size), index=INDEX, doc_type='user')
    docs = results['results']
    pages = math.ceil(results['counts'].get('user', 0) / size)

    users = []
    for doc in docs:
        # TODO: use utils.serialize_user
        user = User.load(doc['id'])

        if current_user:
            n_projects_in_common = current_user.n_projects_in_common(user)
        else:
            n_projects_in_common = 0

        if user is None:
            logger.error('Could not load user {0}'.format(doc['id']))
            continue
        if user.is_active:  # exclude merged, unregistered, etc.
            current_employment = None
            education = None

            if user.jobs:
                current_employment = user.jobs[0]['institution']

            if user.schools:
                education = user.schools[0]['institution']

            users.append({
                'fullname': doc['user'],
                'id': doc['id'],
                'employment': current_employment,
                'education': education,
                'n_projects_in_common': n_projects_in_common,
                'gravatar_url': gravatar(
                    user,
                    use_ssl=True,
                    size=settings.GRAVATAR_SIZE_ADD_CONTRIBUTOR,
                ),
                'profile_url': user.profile_url,
                'registered': user.is_registered,
                'active': user.is_active

            })

    return {
        'users': users,
        'total': results['counts']['total'],
        'pages': pages,
        'page': page,
    }
