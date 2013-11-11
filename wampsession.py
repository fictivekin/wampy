import concurrent.futures
import uuid
from wamputil import check_signature, WeaklyBoundCallable
from wampmessage import WAMPMessage
from pubsub import PubSub


class WAMPSession(object):

    _executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

    def __init__(self, pubsub=None, prefixes=None, procedures=None):
        self._session_id = uuid.uuid4()
        self.pubsub = pubsub or PubSub('WAMPSessions')
        self.prefixes = prefixes or dict()
        self.procedures = procedures or dict()

    @property
    def session_id(self):
        return self._session_id

    def handle_wamp_message(self, message, callback=None, as_future=False):
        handler_name = "_handle_" + message.type.name
        method = getattr(self, handler_name)
        if method:
            future = self._executor.submit(method, message)
            if hasattr(callback, '__call__'):
                future.add_done_callback(callback)
            if as_future or hasattr(callback, '__call__'):
                return future
            else:
                return future.result()

    # RPC Registration
    def register_procedure(self, uri, procedure):
        check_signature(procedure, min_args=0)
        self.procedures[uri] = WeaklyBoundCallable(procedure)

    def proc_for_uri(self, uri):
        try:
            prefix, iri = uri.split(':')
            uri = self.prefixes[prefix] + iri
        except KeyError:
            raise Exception("unrecognized prefix: '%s'" % prefix)
        except ValueError:
            pass
        return self.procedures[uri]

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

    def _handle_CALL(self, message):
        try:
            procedure = self.proc_for_uri(message.proc_uri)
            result = procedure(*(message.args))
            response = WAMPMessage.callresult(message.call_id, result)
        except KeyError as e:
            response = WAMPMessage.callerror(message.call_id, 'error/uri',
                                             'unrecognized procURI', e.args)
        except BaseException as e:
            response = WAMPMessage.callerror(message.call_id, 'error/uri',
                                             str(e))
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
