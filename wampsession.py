import uuid
from wamputil import check_signature, WeaklyBoundCallable
from wampmessage import WAMPMessage, WAMPMessageType
from wampexc import WAMPError
from pubsub import PubSub


class WAMPSession(object):

    cls_pubsub = PubSub('WAMPSessions')
    bad_prefix_uri = "http://wamp.ws/spec/#prefix_message"
    unrecognized_proc_uri = "http://wamp.ws/spec/#call_message"

    def __init__(self, pubsub=None, prefixes=None, procedures=None):
        self._session_id = str(uuid.uuid4())
        self.pubsub = pubsub or self.cls_pubsub
        self.prefixes = prefixes or dict()
        self.procedures = procedures or dict()

    @property
    def session_id(self):
        return self._session_id

    def handle_wamp_message(self, message, callback=None):
        handler_name = "_handle_" + message.type.name
        method = getattr(self, handler_name)
        if method:
            args = [message]
            if message.type == WAMPMessageType.CALL and callback is not None:
                check_signature(callback, num_args=1)
                args.append(WeaklyBoundCallable(callback))
            method(*args)

    # RPC Registration
    def register_procedure(self, uri, procedure):
        check_signature(procedure, min_args=0)
        self.procedures[uri] = WeaklyBoundCallable(procedure)

    def expand_uri(self, uri):
        try:
            prefix, iri = uri.split(':')
            uri = self.prefixes[prefix] + iri
        except KeyError:
            raise WAMPError(self.bad_prefix_uri,
                            "unrecognized prefix: '%s'" % prefix,
                            {'code': 404})
        except ValueError:
            pass
        return uri

    def proc_for_uri(self, uri):
        uri = self.expand_uri(uri)
        try:
            return self.procedures[uri]
        except KeyError:
            raise WAMPError(self.unrecognized_proc_uri,
                            "unrecognized procURI: '%s'" % uri,
                            {'code': 404})

    # send_wamp_message
    @property
    def send_wamp_message(self):
        return self._send_wamp_message

    @send_wamp_message.setter
    def send_wamp_message(self, value):
        check_signature(value, num_args=1)
        self._send_wamp_message = WeaklyBoundCallable(value)

    @send_wamp_message.deleter
    def send_wamp_message(self):
        del self._send_wamp_message

    # callresult_callback
    @property
    def callresult_callback(self):
        return self._callresult_callback

    @callresult_callback.setter
    def callresult_callback(self, value):
        check_signature(value, num_args=1)
        self._callresult_callback = WeaklyBoundCallable(value)

    @callresult_callback.deleter
    def callresult_callback(self):
        del self._callresult_callback

    # callerror_callback
    @property
    def callerror_callback(self):
        return self._callerror_callback

    @callerror_callback.setter
    def callerror_callback(self, value):
        check_signature(value, num_args=1)
        self._callerror_callback = WeaklyBoundCallable(value)

    @callerror_callback.deleter
    def callerror_callback(self):
        del self._callerror_callback

    # event_callback
    @property
    def event_callback(self):
        return self._event_callback

    @event_callback.setter
    def event_callback(self, value):
        check_signature(value, num_args=1)
        self._event_callback = WeaklyBoundCallable(value)

    @event_callback.deleter
    def event_callback(self):
        del self._event_callback

    # WAMP Message Handlers
    def _handle_WELCOME(self, message):
        self._session_id = message.session_id

    def _handle_PREFIX(self, message):
        self.prefixes[message.prefix] = message.uri

    def _handle_CALL(self, message, callback=None):
        try:
            procedure = self.proc_for_uri(message.proc_uri)
            result = procedure(*(message.args))
            response = WAMPMessage.callresult(message.call_id, result)
        except WAMPError as e:
            response = WAMPMessage.callerror(message.call_id, e.error_uri,
                                             e.error_desc, e.error_details)
        except Exception as e:
            response = WAMPMessage.callerror(message.call_id, 'errors/unknown',
                                             'unknown error', e.args)
        if callback is not None:
            callback(response)
        else:
            self.send_wamp_message(response)

    def _handle_CALLRESULT(self, message):
        self.callresult_callback(message)

    def _handle_CALLERROR(self, message):
        self.callerror_callback(message)

    # Pub-Sub
    def _pubsub_callback(self, topic, event):
        self.send_wamp_message(WAMPMessage.event(topic, event))

    def _handle_SUBSCRIBE(self, message):
        self.pubsub.subscribe(self, self.session_id, message.topic_uri,
                              self._pubsub_callback)

    def _handle_UNSUBSCRIBE(self, message):
        self.pubsub.unsubscribe(self, self.session_id, message.topic_uri,
                                self._pubsub_callback)

    def _handle_PUBLISH(self, message):
        try:
            exclude = [self.session_id] if message.exclude_me else []
            eligible = None
        except AttributeError:
            exclude = message.exclude
            eligible = message.eligible
        self.pubsub.publish(message.topic_uri, message.event,
                            exclude, eligible)

    def _handle_EVENT(self, message):
        self.event_callback(message)
