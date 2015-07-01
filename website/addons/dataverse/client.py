import httplib as http

from dataverse import Connection
from dataverse.exceptions import ConnectionError, UnauthorizedError, OperationFailedError

from framework.exceptions import HTTPError


def _connect(host, token):
    try:
        return Connection(host, token)
    except ConnectionError:
        return None


def connect_from_settings(node_settings):
    if not (node_settings and node_settings.external_account):
        return None

    host = node_settings.external_account.oauth_key
    token = node_settings.external_account.oauth_secret

    try:
        return _connect(host, token)
    except UnauthorizedError:
        return None


def connect_or_401(host, token):
    try:
        return _connect(host, token)
    except UnauthorizedError:
        raise HTTPError(http.UNAUTHORIZED)


def connect_from_settings_or_401(node_settings):
    if not (node_settings and node_settings.external_account):
        return None

    host = node_settings.external_account.oauth_key
    token = node_settings.external_account.oauth_secret

    return connect_or_401(host, token)


def get_files(dataset, published=False):
    version = 'latest-published' if published else 'latest'
    return dataset.get_files(version)


def publish_dataverse(dataverse):
    try:
        dataverse.publish()
    except OperationFailedError:
        raise HTTPError(http.BAD_REQUEST)


def publish_dataset(dataset):
    if dataset.get_state() == 'RELEASED':
        raise HTTPError(http.CONFLICT, data=dict(
            message_short='Dataset conflict',
            message_long='This version of the dataset has already been '
                         'published.'
        ))
    if not dataset.dataverse.is_published:
        raise HTTPError(http.METHOD_NOT_ALLOWED, data=dict(
            message_short='Method not allowed',
            message_long='A dataset cannot be published until its parent '
                         'Dataverse is published.'
        ))

    try:
        dataset.publish()
    except OperationFailedError:
        raise HTTPError(http.BAD_REQUEST)


def get_datasets(dataverse):
    if dataverse is None:
        return []
    return dataverse.get_datasets()


def get_dataset(dataverse, doi):
    if dataverse is None:
        return
    dataset = dataverse.get_dataset_by_doi(doi)
    try:
        if dataset and dataset.get_state() == 'DEACCESSIONED':
            raise HTTPError(http.GONE, data=dict(
                message_short='Dataset deaccessioned',
                message_long='This dataset has been deaccessioned and can no '
                             'longer be linked to the OSF.'
            ))
        return dataset
    except UnicodeDecodeError:
        raise HTTPError(http.NOT_ACCEPTABLE, data=dict(
            message_short='Not acceptable',
            message_long='This dataset cannot be connected due to forbidden '
                         'characters in one or more of the file names.'
        ))


def get_dataverses(connection):
    if connection is None:
        return []
    return connection.get_dataverses()


def get_dataverse(connection, alias):
    if connection is None:
        return
    return connection.get_dataverse(alias)
