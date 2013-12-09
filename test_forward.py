import unittest
import gc
import weakref
import concurrent.futures
import time

from wampsession import WAMPSession
from wampmessage import WAMPMessage, WAMPMessageType
from wampexc import WAMPError
from pubsub import PubSub

from forward import WAMPCallForwardingMixin


class ForwardingSession(WAMPCallForwardingMixin, WAMPSession):
    pass


class MockRecipient(object):

    def handle_call_message(self, message):
        proc_uri = message.proc_uri
        proc = getattr(self, proc_uri)
        return proc(message)

    def wamp_error(self, message):
        raise WAMPError('some_uri', 'expected error', {'key': 'value'})

    def unknown_exception(self, message):
        raise Exception("spam & eggs")

    def procedure1(self, message):
        return {'proc': 'procedure1', 'args': message.args}

    def procedure2(self, message):
        return {'proc': 'procedure2', 'args': message.args}

    def procedure3(self, message):
        pass


class TestWAMPSession(unittest.TestCase):

    def setUp(self):
        self.session = ForwardingSession()
        self.recipient = MockRecipient()
        self.session.send_wamp_message = self.send_wamp_message
        self.session.forward_wamp_message = self.recipient.handle_call_message
        self.message_log = []

    def send_wamp_message(self, message):
        self.message_log.append(message)

    def test_prefix(self):
        my_procedure = lambda *args: None
        self.session.register_procedure('long_uri#target', my_procedure)
        self.session.handle_wamp_message(
            WAMPMessage.prefix('prefix', 'long_uri'))
        self.session.handle_wamp_message(
            WAMPMessage.prefix('', 'long_uri'))
        self.assertEqual(self.session.proc_for_uri('prefix:#target'),
                         self.session.proc_for_uri('long_uri#target'))
        self.assertEqual(self.session.proc_for_uri(':#target'),
                         self.session.proc_for_uri('long_uri#target'))
        with self.assertRaises(WAMPError) as cm:
            self.session.proc_for_uri('not_a_prefix:#target')
        self.assertIn('not_a_prefix', cm.exception.error_desc)
        self.assertEqual(404, cm.exception.error_details['code'])

    def test_call(self):

        def procedure_never(message=None, *args):
            return WAMPMessage.callresult(message.call_id,
                                          {'proc': 'procedure_never',
                                           'args': message.args})

        self.session.register_procedure('procedure1')
        self.session.register_procedure('procedure2', procedure_never)
        prefix_message = WAMPMessage.prefix('proc', 'procedure')
        self.session.handle_wamp_message(prefix_message)
        call_message1 = WAMPMessage.call('call1', 'procedure1', 'arg1')
        call_message2 = WAMPMessage.call('call2', 'proc:1', 'arg2')
        call_message3 = WAMPMessage.call('call3', 'procedure2', 'arg3')
        call_message4 = WAMPMessage.call('call4', 'procedure3', 'arg4')
        self.session.handle_wamp_message(call_message1)
        self.session.handle_wamp_message(call_message2)
        self.session.handle_wamp_message(call_message3)
        self.session.handle_wamp_message(call_message4)
        self.assertEqual(len(self.message_log), 3)
        self.assertEqual(self.message_log[0],
                         WAMPMessage.callresult('call1',
                                                {'proc': 'procedure1',
                                                 'args': ['arg1']}))
        self.assertEqual(self.message_log[1],
                         WAMPMessage.callresult('call2',
                                                {'proc': 'procedure1',
                                                 'args': ['arg2']}))
        self.assertEqual(self.message_log[2],
                         WAMPMessage.callresult('call3',
                                                {'proc': 'procedure2',
                                                 'args': ['arg3']}))


if __name__ == '__main__':
    unittest.main()
