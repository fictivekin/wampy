import unittest
import gc
import weakref
import concurrent.futures
import time
from wampsession import WAMPSession
from wampmessage import WAMPMessage, WAMPMessageType
from pubsub import PubSub


class TestWAMPSession(unittest.TestCase):

    def test_init(self):
        session = WAMPSession()
        self.assertTrue(isinstance(session.session_id, basestring))
        self.assertEqual(id(session.pubsub), id(PubSub('WAMPSessions')))

    def test_registered_procedures(self):

        class MyClass(object):

            def my_bad(self):
                pass

            def my_procedure(self, *args):
                pass

        session = WAMPSession()
        instance = MyClass()
        self.assertRaises(Exception, session.register_procedure,
                          'proc_uri', instance.my_bad)
        self.assertRaises(Exception, session.proc_for_uri, 'proc_uri')
        session.register_procedure('proc_uri', instance.my_procedure)
        self.assertEqual(session.proc_for_uri('proc_uri').reverted(),
                         instance.my_procedure)
        weak_instance = weakref.ref(instance)
        self.assertNotEqual(weak_instance(), None)
        del instance
        gc.collect()
        self.assertEqual(weak_instance(), None)

    def test_welcome(self):
        session = WAMPSession()
        self.assertNotEqual(session.session_id, 'new_id')
        session.handle_wamp_message(WAMPMessage.welcome('new_id'))
        self.assertEqual(session.session_id, 'new_id')

    def test_pefix(self):

        class MyClass(object):

            def my_procedure(self, *args):
                pass

        session = WAMPSession()
        instance = MyClass()
        session.register_procedure('long_uri#target', instance.my_procedure)
        session.handle_wamp_message(WAMPMessage.prefix('prefix', 'long_uri'))
        session.handle_wamp_message(WAMPMessage.prefix('', 'long_uri'))
        self.assertEqual(session.proc_for_uri('prefix:#target'),
                         session.proc_for_uri('long_uri#target'))
        self.assertEqual(session.proc_for_uri(':#target'),
                         session.proc_for_uri('long_uri#target'))
        with self.assertRaises(Exception):
            session.proc_for_uri('not_a_prefix:#target')

    def test_call(self):

        message_log = []

        class MyClass(object):

            def __init__(self, tag):
                self.tag = tag

            def my_procedure1(self, arg=None, *args):
                return {'tag': self.tag,
                        'procedure': 'my_procedure1',
                        'argument': arg}

            def my_procedure2(self, arg=None, *args):
                return {'tag': self.tag,
                        'procedure': 'my_procedure2',
                        'argument': arg}

        def send_wamp_message(message):
            message_log.append(message)

        session = WAMPSession()
        session.send_wamp_message = send_wamp_message
        instance1 = MyClass('instance1')
        instance2 = MyClass('instance2')
        session.register_procedure('proc1', instance1.my_procedure1)
        session.register_procedure('proc2', instance2.my_procedure2)
        prefix_message = WAMPMessage.prefix('prefix', 'proc')
        session.handle_wamp_message(prefix_message)
        call_message1 = WAMPMessage.call('call1', 'proc1', 'arg1')
        call_message2 = WAMPMessage.call('call2', 'proc2', 'arg2')
        call_message3 = WAMPMessage.call('call3', 'prefix:1', 'arg3')
        session.handle_wamp_message(call_message1)
        session.handle_wamp_message(call_message2)
        session.handle_wamp_message(call_message3)
        self.assertEqual(len(message_log), 3)
        self.assertEqual(message_log[0],
                         WAMPMessage.callresult('call1',
                                                {'tag': 'instance1',
                                                 'procedure': 'my_procedure1',
                                                 'argument': 'arg1'}))
        self.assertEqual(message_log[1],
                         WAMPMessage.callresult('call2',
                                                {'tag': 'instance2',
                                                 'procedure': 'my_procedure2',
                                                 'argument': 'arg2'}))
        self.assertEqual(message_log[2],
                         WAMPMessage.callresult('call3',
                                                {'tag': 'instance1',
                                                 'procedure': 'my_procedure1',
                                                 'argument': 'arg3'}))

    def test_call_custom_send_callback(self):

        message_log = []

        def proc(arg=None, *args):
            return ('proc', arg)

        def send1(message):
            message_log.append(('send1', message))

        def send2(message):
            message_log.append(('send2', message))

        session = WAMPSession()
        session.send_wamp_message = send1
        session.register_procedure('proc', proc)
        call_message1 = WAMPMessage.call('call1', 'proc', 'arg1')
        call_message2 = WAMPMessage.call('call2', 'proc', 'arg2')
        call_message3 = WAMPMessage.call('call3', 'proc', 'arg3')
        session.handle_wamp_message(call_message1)
        session.handle_wamp_message(call_message2, send2)
        session.handle_wamp_message(call_message3)
        self.assertEqual(len(message_log), 3)
        self.assertEqual(message_log[0],
                         ('send1',
                          WAMPMessage.callresult('call1', ('proc', 'arg1'))))
        self.assertEqual(message_log[1],
                         ('send2',
                          WAMPMessage.callresult('call2', ('proc', 'arg2'))))
        self.assertEqual(message_log[2],
                         ('send1',
                          WAMPMessage.callresult('call3', ('proc', 'arg3'))))

    def test_call_exceptions(self):

        message_log = []

        def bad_function(*args):
            raise Exception("spam & eggs")

        def send_wamp_message(message):
            message_log.append(message)

        session = WAMPSession()
        session.send_wamp_message = send_wamp_message
        session.register_procedure('bad_function', bad_function)
        prefix_message = WAMPMessage.prefix('prefix', 'bad_')
        session.handle_wamp_message(prefix_message)
        call_message1 = WAMPMessage.call('call1', 'not:function')
        call_message2 = WAMPMessage.call('call2', 'not_function')
        call_message3 = WAMPMessage.call('call3', 'bad_function')
        call_message4 = WAMPMessage.call('call4', 'prefix:function')
        session.handle_wamp_message(call_message1)
        session.handle_wamp_message(call_message2)
        session.handle_wamp_message(call_message3)
        session.handle_wamp_message(call_message4)
        self.assertEqual(len(message_log), 4)
        self.assertEqual(message_log[0].json[:3],
                         [WAMPMessageType.CALLERROR, 'call1', 'error/uri'])
        self.assertIn('unrecognized prefix', message_log[0].json[3])
        self.assertEqual(message_log[1].json[:3],
                         [WAMPMessageType.CALLERROR, 'call2', 'error/uri'])
        self.assertIn('unrecognized procURI', message_log[1].json[3])
        self.assertEqual(message_log[2].json[:3],
                         [WAMPMessageType.CALLERROR, 'call3', 'error/uri'])
        self.assertIn('spam & eggs', message_log[2].json[3])
        self.assertEqual(message_log[3].json[:3],
                         [WAMPMessageType.CALLERROR, 'call4', 'error/uri'])
        self.assertIn('spam & eggs', message_log[3].json[3])

    def test_call_result(self):

        message_log = []

        def callresult_callback(message):
            message_log.append(message)

        session = WAMPSession()
        session.callresult_callback = callresult_callback
        message = WAMPMessage.callresult('call1', {'key': 'value'})
        session.handle_wamp_message(message)
        self.assertEqual(len(message_log), 1)
        self.assertEqual(message_log[0], message)

    def test_call_error(self):

        message_log = []

        def callerror_callback(message):
            message_log.append(message)

        session = WAMPSession()
        session.callerror_callback = callerror_callback
        message = WAMPMessage.callerror('call1', 'error/uri', 'unknown error')
        session.handle_wamp_message(message)
        self.assertEqual(len(message_log), 1)
        self.assertEqual(message_log[0], message)

    def test_pubsub(self):

        message_log = []

        def send_wamp_message(message):
            message_log.append(message)

        def send_wamp_message2(message):
            message_log.append(('special', message))

        pub_session = WAMPSession()
        sub_session = WAMPSession()
        pub_session.send_wamp_message = send_wamp_message
        sub_session.send_wamp_message = send_wamp_message
        sub_message = WAMPMessage.subscribe('topic_uri')
        sub_session.handle_wamp_message(sub_message)
        pub_message = WAMPMessage.publish('topic_uri', {'key': 'value'})
        pub_session.handle_wamp_message(pub_message)
        self.assertEqual(len(message_log), 1)
        self.assertEqual(message_log[0],
                         WAMPMessage.event('topic_uri', {'key': 'value'}))
        message_log = []
        # second subscriber
        pub_session.handle_wamp_message(sub_message)
        # updated subscription
        sub_session.send_wamp_message = send_wamp_message2
        sub_session.handle_wamp_message(sub_message)
        pub_message = WAMPMessage.publish('topic_uri', 'second event')
        pub_session.handle_wamp_message(pub_message)
        self.assertEqual(len(message_log), 2)
        event_message = WAMPMessage.event('topic_uri', 'second event')
        self.assertIn(event_message, message_log)
        self.assertIn(('special', event_message), message_log)
        message_log = []
        # unsubscribe
        sub_session.handle_wamp_message(WAMPMessage.unsubscribe('topic_uri'))
        pub_message = WAMPMessage.publish('topic_uri', ['third', 'event'])
        pub_session.handle_wamp_message(pub_message)
        self.assertEqual(len(message_log), 1)
        self.assertEqual(message_log[0],
                         WAMPMessage.event('topic_uri', ['third', 'event']))

    def test_event(self):

        event_log = []

        def event_callback(message):
            event_log.append(message)

        session = WAMPSession()
        session.event_callback = event_callback
        session.handle_wamp_message(WAMPMessage.event('topic', 'event'))
        self.assertEqual(len(event_log), 1)
        self.assertEqual(event_log[0], WAMPMessage.event('topic', 'event'))


class TestAsyncWAMPSession(unittest.TestCase):

    def setUp(self):
        self.message_log = []
        self.callback_log = []
        self.async_log = []
        self.session = WAMPSession()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        self.session.send_wamp_message = self.send_wamp_message
        self.session.register_procedure('sf', self.sync_fast)
        self.session.register_procedure('ss', self.sync_slow)
        self.session.register_procedure('aa', self.async_a)
        self.session.register_procedure('ab', self.async_b)
        super(TestAsyncWAMPSession, self).setUp()

    def send_wamp_message(self, message):
        self.message_log.append(message)

    def sync_fast(self, *args):
        return 'sync_fast'

    def sync_slow(self, *args):
        time.sleep(0.2)
        return 'sync_slow'

    def callback(self, future):
        self.callback_log.append('callback')

    def async_a(self, *args):
        self.async_log.append('async_a1')
        time.sleep(0.1)
        self.async_log.append('async_a2')
        time.sleep(0.2)
        self.async_log.append('async_a3')
        return 'async_a'

    def async_b(self, *args):
        self.async_log.append('async_b1')
        time.sleep(0.2)
        self.async_log.append('async_b2')
        time.sleep(0.2)
        self.async_log.append('async_b3')
        return 'async_b'

    def test_synchronous(self):
        self.session.handle_wamp_message(WAMPMessage.call('c1', 'sf'))
        self.assertEqual(len(self.message_log), 1)
        self.assertEqual(self.message_log[0],
                         WAMPMessage.callresult('c1', 'sync_fast'))

    def test_callback(self):
        future = self.executor.submit(self.session.handle_wamp_message,
                                      WAMPMessage.call('c2', 'ss'))
        future.add_done_callback(self.callback)
        self.assertEqual(len(self.message_log), 0)
        self.assertEqual(len(self.callback_log), 0)
        time.sleep(3)
        self.assertEqual(len(self.message_log), 1)
        self.assertEqual(self.message_log[0],
                         WAMPMessage.callresult('c2', 'sync_slow'))
        self.assertEqual(len(self.callback_log), 1)
        self.assertEqual(self.callback_log[0], 'callback')

    def test_future(self):
        future = self.executor.submit(self.session.handle_wamp_message,
                                      WAMPMessage.call('c3', 'ss'))
        self.assertEqual(len(self.message_log), 0)
        result = future.result()
        self.assertEqual(len(self.message_log), 1)
        self.assertEqual(self.message_log[0],
                         WAMPMessage.callresult('c3', 'sync_slow'))

    def test_serial(self):
        f1 = self.session.handle_wamp_message(WAMPMessage.call('c4', 'aa'))
        f2 = self.session.handle_wamp_message(WAMPMessage.call('c5', 'ab'))
        self.assertEqual(f1, None)
        self.assertEqual(f2, None)
        self.assertEqual(len(self.message_log), 2)
        self.assertEqual(self.message_log[0],
                         WAMPMessage.callresult('c4', 'async_a'))
        self.assertEqual(self.message_log[1],
                         WAMPMessage.callresult('c5', 'async_b'))
        self.assertEqual(len(self.async_log), 6)
        self.assertEqual(self.async_log, ['async_a1', 'async_a2', 'async_a3',
                                          'async_b1', 'async_b2', 'async_b3'])

    def test_concurrent(self):
        f1 = self.executor.submit(self.session.handle_wamp_message,
                                  WAMPMessage.call('c6', 'aa'))
        f2 = self.executor.submit(self.session.handle_wamp_message,
                                  WAMPMessage.call('c7', 'ab'))
        self.assertTrue(isinstance(f1, concurrent.futures.Future))
        self.assertTrue(isinstance(f2, concurrent.futures.Future))
        concurrent.futures.wait((f1, f2))
        self.assertEqual(len(self.message_log), 2)
        self.assertEqual(self.message_log[0],
                         WAMPMessage.callresult('c6', 'async_a'))
        self.assertEqual(self.message_log[1],
                         WAMPMessage.callresult('c7', 'async_b'))
        self.assertEqual(len(self.async_log), 6)
        self.assertEqual(self.async_log, ['async_a1', 'async_b1', 'async_a2',
                                          'async_b2', 'async_a3', 'async_b3'])


if __name__ == '__main__':
    unittest.main()
