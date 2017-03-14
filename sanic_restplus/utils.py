# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from collections import OrderedDict
from copy import deepcopy
from six import iteritems

#copied from sanic router
REGEX_TYPES = {
    'string': (str, r'[^/]+'),
    'int': (int, r'\d+'),
    'number': (float, r'[0-9\\.]+'),
    'alpha': (str, r'[A-Za-z]+'),
}

FIRST_CAP_RE = re.compile('(.)([A-Z][a-z]+)')
ALL_CAP_RE = re.compile('([a-z0-9])([A-Z])')


__all__ = ('merge', 'camel_to_dash', 'default_id', 'not_none', 'not_none_sorted', 'unpack')


def merge(first, second):
    '''
    Recursively merges two dictionnaries.

    Second dictionnary values will take precedance over those from the first one.
    Nested dictionnaries are merged too.

    :param dict first: The first dictionnary
    :param dict second: The second dictionnary
    :return: the resulting merged dictionnary
    :rtype: dict
    '''
    if not isinstance(second, dict):
        return second
    result = deepcopy(first)
    for key, value in iteritems(second):
        if key in result and isinstance(result[key], dict):
                result[key] = merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def camel_to_dash(value):
    '''
    Transform a CamelCase string into a low_dashed one

    :param str value: a CamelCase string to transform
    :return: the low_dashed string
    :rtype: str
    '''
    first_cap = FIRST_CAP_RE.sub(r'\1_\2', value)
    return ALL_CAP_RE.sub(r'\1_\2', first_cap).lower()


def default_id(resource, method):
    '''Default operation ID generator'''
    return '{0}_{1}'.format(method, camel_to_dash(resource))


def not_none(data):
    '''
    Remove all keys where value is None

    :param dict data: A dictionnary with potentialy some values set to None
    :return: The same dictionnary without the keys with values to ``None``
    :rtype: dict
    '''
    return dict((k, v) for k, v in iteritems(data) if v is not None)


def not_none_sorted(data):
    '''
    Remove all keys where value is None

    :param OrderedDict data: A dictionnary with potentialy some values set to None
    :return: The same dictionnary without the keys with values to ``None``
    :rtype: OrderedDict
    '''
    ordered_items = OrderedDict(sorted(iteritems(data)))
    return OrderedDict((k, v) for k, v in iteritems(ordered_items) if v is not None)


def unpack(response, default_code=200):
    '''
    Unpack a Flask standard response.

    Flask response can be:
    - a single value
    - a 2-tuple ``(value, code)``
    - a 3-tuple ``(value, code, headers)``

    .. warning::

        When using this function, you must ensure that the tuple is not the reponse data.
        To do so, prefer returning list instead of tuple for listings.

    :param response: A Flask style response
    :param int default_code: The HTTP code to use as default if none is provided
    :return: a 3-tuple ``(data, code, headers)``
    :rtype: tuple
    :raise ValueError: if the response does not have one of the expected format
    '''
    if not isinstance(response, tuple):
        # data only
        return response, default_code, {}
    elif len(response) == 1:
        # data only as tuple
        return response[0], default_code, {}
    elif len(response) == 2:
        # data and code
        data, code = response
        return data, code, {}
    elif len(response) == 3:
        # data, code and headers
        data, code, headers = response
        return data, code or default_code, headers
    else:
        raise ValueError('Too many response values')


def best_match_accept_mimetype(request, representations, default=None):
    if representations is None or len(representations) < 1:
        return default
    try:
        accept_types = request.headers.get('accept', None)
        if accept_types is None:
            return default
        split_types = str(accept_types).split(',')
        for accept_type in split_types:
            if accept_type in representations:
                return accept_type
        for accept_type in split_types:
            type_part = str(accept_type).split(';', 1)[0]
            if type_part in representations:
                return type_part
    except (AttributeError, KeyError):
        return default

def parse_rule(parameter_string):
    """Parse a parameter string into its constituent name, type, and
    pattern

    For example:
    `parse_parameter_string('<param_one:[A-z]>')` ->
        ('param_one', str, '[A-z]')

    :param parameter_string: String to parse
    :return: tuple containing
        (parameter_name, parameter_type, parameter_pattern)
    """
    # We could receive NAME or NAME:PATTERN
    if str(parameter_string).startswith('/'):
        parameter_string = parameter_string[1:]
    parameter_string = str(parameter_string).strip('<>')
    name = parameter_string
    pattern = 'string'
    if ':' in parameter_string:
        name, pattern = parameter_string.split(':', 1)

    default = (str, pattern)
    # Pull from pre-configured types
    _type, pattern = REGEX_TYPES.get(pattern, default)

    return name, _type, pattern
