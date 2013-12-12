import json
from wamputil import iterablate, UppercaseAliasingMixin, AttributeFactoryMixin


class WAMPMessageTypeMetaclass(UppercaseAliasingMixin,
                               AttributeFactoryMixin,
                               type):
    pass


class WAMPMessageType(int):

    __metaclass__ = WAMPMessageTypeMetaclass
    _message_types = ['WELCOME',
                      'PREFIX',
                      'CALL',
                      'CALLRESULT',
                      'CALLERROR',
                      'SUBSCRIBE',
                      'UNSUBSCRIBE',
                      'PUBLISH',
                      'EVENT']
    _instances = dict()

    def __new__(cls, identifier):
        if isinstance(identifier, int):
            try:
                name = cls._message_types[identifier]
                type_id = identifier
            except IndexError:
                raise AttributeError("Invalid %s: %d" %
                                     (cls.__name__, identifier))
        else:
            try:
                type_id = cls._message_types.index(identifier)
                name = identifier
            except ValueError:
                raise AttributeError("Invalid %s: %s" %
                                     (cls.__name__, identifier))
        if type_id not in cls._instances:
            new_instance = super(WAMPMessageType, cls).__new__(cls, type_id)
            new_instance.name = name
            cls._instances[type_id] = new_instance
        return cls._instances[type_id]


class WAMPMessageMetaclass(type):

    def __getattribute__(cls, name):
        try:
            return type.__getattribute__(cls, name)
        except AttributeError:
            message_type = getattr(WAMPMessageType, name)
            try:
                assert cls == WAMPMessage, "cannot be called from a subclass"
                return cls._sc[message_type]
            except KeyError as e:
                raise AttributeError("%s object has no attribute %s" %
                                     cls.__name__, name)


class WAMPMessage(object):

    __metaclass__ = WAMPMessageMetaclass
    _sc = dict()

    def __new__(cls, type=None, *args, **kwargs):
        if cls == WAMPMessage:
            assert type in cls._sc, "unrecognized message type"
            return cls._sc[type](*args, **kwargs)
        else:
            return super(WAMPMessage, cls).__new__(cls)

    @classmethod
    def loads(cls, in_string):
        assert cls == WAMPMessage, "cannot be called from a subclass"
        in_object = json.loads(in_string)
        return WAMPMessage(*in_object)

    @property
    def type(self):
        return getattr(self, '_type', None)

    @property
    def json(self):
        return [self.type] + self.wamp_args

    def __hash__(self):
        return int(self.type) if self.type is not None else -1

    def __eq__(self, other):
        return (isinstance(other, WAMPMessage) and
                self.__hash__() == other.__hash__() and
                self.json == other.json)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return json.dumps(self.json, default=str)

    def __getnewargs__(self):
        return tuple(self.wamp_args)


class WAMPMessageWelcome(WAMPMessage):

    def __new__(cls, session_id, protocol_version=1, server_ident=1):
        self = super(WAMPMessageWelcome, cls).__new__(WAMPMessageWelcome)
        self._type = WAMPMessageType.WELCOME
        self.session_id = session_id
        self.protocol_version = protocol_version
        self.server_ident = server_ident
        return self

    @property
    def wamp_args(self):
        return [self.session_id, self.protocol_version, self.server_ident]

WAMPMessage._sc[WAMPMessageType.WELCOME] = WAMPMessageWelcome


class WAMPMessagePrefix(WAMPMessage):

    def __new__(cls, prefix, uri):
        self = super(WAMPMessagePrefix, cls).__new__(WAMPMessagePrefix)
        self._type = WAMPMessageType.PREFIX
        self.prefix = prefix
        self.uri = uri
        return self

    @property
    def wamp_args(self):
        return [self.prefix, self.uri]

WAMPMessage._sc[WAMPMessageType.PREFIX] = WAMPMessagePrefix


class WAMPMessageCall(WAMPMessage):

    def __new__(cls, call_id, proc_uri, *args):
        self = super(WAMPMessageCall, cls).__new__(WAMPMessageCall)
        self._type = WAMPMessageType.CALL
        self.call_id = call_id
        self.proc_uri = proc_uri
        self.args = list(args)
        return self

    @property
    def wamp_args(self):
        return [self.call_id, self.proc_uri] + self.args

WAMPMessage._sc[WAMPMessageType.CALL] = WAMPMessageCall


class WAMPMessageCallResult(WAMPMessage):

    def __new__(cls, call_id, result):
        self = (super(WAMPMessageCallResult, cls).
                __new__(WAMPMessageCallResult))
        self._type = WAMPMessageType.CALLRESULT
        self.call_id = call_id
        self.result = result
        return self

    @property
    def wamp_args(self):
        return [self.call_id, self.result]

WAMPMessage._sc[WAMPMessageType.CALLRESULT] = WAMPMessageCallResult


class WAMPMessageCallError(WAMPMessage):

    def __new__(cls, call_id, error_uri, error_desc, error_details=None):
        self = (super(WAMPMessageCallError, cls).
                __new__(WAMPMessageCallError))
        self._type = WAMPMessageType.CALLERROR
        self.call_id = call_id
        self.error_uri = error_uri
        self.error_desc = error_desc
        self.error_details = error_details
        return self

    @property
    def wamp_args(self):
        return ([self.call_id, self.error_uri, self.error_desc] +
                ([] if self.error_details is None else [self.error_details]))

WAMPMessage._sc[WAMPMessageType.CALLERROR] = WAMPMessageCallError


class WAMPMessageSubscribe(WAMPMessage):

    def __new__(cls, topic_uri):
        self = (super(WAMPMessageSubscribe, cls).
                __new__(WAMPMessageSubscribe))
        self._type = WAMPMessageType.SUBSCRIBE
        self.topic_uri = topic_uri
        return self

    @property
    def wamp_args(self):
        return [self.topic_uri]

WAMPMessage._sc[WAMPMessageType.SUBSCRIBE] = WAMPMessageSubscribe


class WAMPMessageUnsubscribe(WAMPMessage):

    def __new__(cls, topic_uri):
        self = (super(WAMPMessageUnsubscribe, cls).
                __new__(WAMPMessageUnsubscribe))
        self._type = WAMPMessageType.UNSUBSCRIBE
        self.topic_uri = topic_uri
        return self

    @property
    def wamp_args(self):
        return [self.topic_uri]

WAMPMessage._sc[WAMPMessageType.UNSUBSCRIBE] = WAMPMessageUnsubscribe


class WAMPMessagePublish(WAMPMessage):

    def __new__(cls, topic_uri, event, exclude=None, eligible=None):
        self = super(WAMPMessagePublish, cls).__new__(WAMPMessagePublish)
        self._type = WAMPMessageType.PUBLISH
        self.topic_uri = topic_uri
        self.event = event
        if isinstance(exclude, bool):
            assert eligible is None, "eligible list requires exclude *list*"
            self.exclude_me = True
        else:
            self.exclude = iterablate(exclude, wrapper_cls=list)
            self.eligible = iterablate(eligible, wrapper_cls=list)
        return self

    @property
    def wamp_args(self):
        if hasattr(self, 'exclude_me') and self.exclude_me:
            filters = [True]
        elif len(self.eligible) > 0 or len(self.exclude) > 0:
            filters = [self.exclude]
            if len(self.eligible) > 0:
                filters += [self.eligible]
        else:
            filters = []
        return [self.topic_uri, self.event] + filters

WAMPMessage._sc[WAMPMessageType.PUBLISH] = WAMPMessagePublish


class WAMPMessageEvent(WAMPMessage):

    def __new__(cls, topic_uri, event):
        self = super(WAMPMessageEvent, cls).__new__(WAMPMessageEvent)
        self._type = WAMPMessageType.EVENT
        self.topic_uri = topic_uri
        self.event = event
        return self

    @property
    def wamp_args(self):
        return [self.topic_uri, self.event]

WAMPMessage._sc[WAMPMessageType.EVENT] = WAMPMessageEvent
