from json import dumps
from collections import Iterable
from util import iterablate


class WAMPMessageType(object):
    WELCOME = 0
    PREFIX = 1
    CALL = 2
    CALLRESULT = 3
    CALLERROR = 4
    SUBSCRIBE = 5
    UNSUBSCRIBE = 6
    PUBLISH = 7
    EVENT = 8


def welcome(session_id, protocol_version=1, server_ident=None):
    return dumps([WAMPMessageType.WELCOME, session_id,
                  protocol_version, server_ident], default=str)


def prefix(prefix, URI):
    return dumps([WAMPMessageType.PREFIX, prefix, URI], default=str)


def call(call_id, proc_uri, *args):
    return dumps([WAMPMessageType.CALL, call_id, proc_uri] + list(args),
                 default=str)


def call_result(call_id, result):
    return dumps([WAMPMessageType.CALLRESULT, call_id, result],
                 default=str)


def call_error(call_id, error_uri, error_desc, error_details=None):
    message = [WAMPMessageType.CALLERROR, call_id, error_uri, error_desc]
    if error_details:
        message.append(error_details)
    return dumps(message, default=str)


def subscribe(topic_uri):
    return dumps([WAMPMessageType.SUBSCRIBE, topic_uri], default=str)


def unsubscribe(topic_uri):
    return dumps([WAMPMessageType.UNSUBSCRIBE, topic_uri], default=str)


def publish(topic_uri, event, exclude=None, eligible=None):
    message = [WAMPMessageType.PUBLISH, topic_uri, event]
    if isinstance(exclude, bool):
        assert eligible is None, "eligible list requires exclude *list*"
        return dumps(message + ([exclude] if exclude else []))
    else:
        exclude = iterablate(exclude)
        eligible = iterablate(eligible)
    if len(exclude) > 0 or len(eligible) > 0:
        message.append(exclude)
    if len(eligible) > 0:
        message.append(eligible)
    return dumps(message, default=str)


def event(topic_uri, event):
    return dumps([WAMPMessageType.EVENT, topic_uri, event], default=str)
