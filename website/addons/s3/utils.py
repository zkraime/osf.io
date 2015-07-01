import re
import httplib

from boto import exception
from boto.s3.connection import S3Connection
from boto.s3.connection import OrdinaryCallingFormat

from framework.exceptions import HTTPError
from website.util import web_url_for


def connect_s3(access_key=None, secret_key=None, user_settings=None):
    """Helper to build an S3Connection object
    Can be used to change settings on all S3Connections
    See: CallingFormat
    """
    if user_settings is not None:
        access_key, secret_key = user_settings.access_key, user_settings.secret_key
    connection = S3Connection(access_key, secret_key)
    return connection


def get_bucket_names(user_settings):
    try:
        buckets = connect_s3(user_settings=user_settings).get_all_buckets()
    except exception.NoAuthHandlerFound:
        raise HTTPError(httplib.FORBIDDEN)
    except exception.BotoServerError as e:
        raise HTTPError(e.status)

    return [bucket.name for bucket in buckets]


def validate_bucket_name(name):
    validate_name = re.compile('^(?!.*(\.\.|-\.))[^.][a-z0-9\d.-]{2,61}[^.]$')
    return bool(validate_name.match(name))


def create_bucket(user_settings, bucket_name):
    return connect_s3(user_settings=user_settings).create_bucket(bucket_name)


def bucket_exists(access_key, secret_key, bucket_name):
    """Tests for the existance of a bucket and if the user
    can access it with the given keys
    """
    if not bucket_name:
        return False

    connection = connect_s3(access_key, secret_key)

    if bucket_name != bucket_name.lower():
        # Must use ordinary calling format for mIxEdCaSe bucket names
        # otherwise use the default as it handles bucket outside of the US
        connection.calling_format = OrdinaryCallingFormat()

    try:
        # Will raise an exception if bucket_name doesn't exist
        connect_s3(access_key, secret_key).head_bucket(bucket_name)
    except exception.S3ResponseError as e:
        if e.status not in (301, 302):
            return False
    return True


def can_list(access_key, secret_key):
    """Return whether or not a user can list
    all buckets accessable by this keys
    """
    # Bail out early as boto does not handle getting
    # Called with (None, None)
    if not (access_key and secret_key):
        return False

    try:
        connect_s3(access_key, secret_key).get_all_buckets()
    except exception.S3ResponseError:
        return False
    return True

def serialize_urls(node_addon, user):
    node = node_addon.owner
    user_settings = node_addon.user_settings

    result = {
        'create_bucket': node.api_url_for('create_bucket'),
        'import_auth': node.api_url_for('s3_node_import_auth'),
        'create_auth': node.api_url_for('s3_authorize_node'),
        'deauthorize': node.api_url_for('s3_delete_node_settings'),
        'bucket_list': node.api_url_for('s3_get_bucket_list'),
        'set_bucket': node.api_url_for('s3_get_node_settings'),
        'settings': web_url_for('user_addons'),
        'files': node.web_url_for('collect_file_trees'),
    }
    if user_settings:
        result['owner'] = user_settings.owner.profile_url
    return result
