import unittest
import json
from wampmessage import WAMPMessageType, WAMPMessage
import wampmessage as WM


class TestWAMPMessageType(unittest.TestCase):

    def test_message_types(self):
        self.assertEqual(WAMPMessageType.WELCOME, 0)
        self.assertTrue(isinstance(WAMPMessageType.WELCOME, WAMPMessageType))
        self.assertEqual(WAMPMessageType.PREFIX, 1)
        self.assertTrue(isinstance(WAMPMessageType.PREFIX, WAMPMessageType))
        self.assertEqual(WAMPMessageType.CALL, 2)
        self.assertTrue(isinstance(WAMPMessageType.CALL, WAMPMessageType))
        self.assertEqual(WAMPMessageType.CALLRESULT, 3)
        self.assertTrue(isinstance(WAMPMessageType.CALLRESULT,
                                   WAMPMessageType))
        self.assertEqual(WAMPMessageType.CALLERROR, 4)
        self.assertTrue(isinstance(WAMPMessageType.CALLERROR, WAMPMessageType))
        self.assertEqual(WAMPMessageType.SUBSCRIBE, 5)
        self.assertTrue(isinstance(WAMPMessageType.SUBSCRIBE, WAMPMessageType))
        self.assertEqual(WAMPMessageType.UNSUBSCRIBE, 6)
        self.assertTrue(isinstance(WAMPMessageType.UNSUBSCRIBE,
                                   WAMPMessageType))
        self.assertEqual(WAMPMessageType.PUBLISH, 7)
        self.assertTrue(isinstance(WAMPMessageType.PUBLISH, WAMPMessageType))
        self.assertEqual(WAMPMessageType.EVENT, 8)
        self.assertTrue(isinstance(WAMPMessageType.EVENT, WAMPMessageType))

    def test_case_insensitivity(self):
        self.assertEqual(WAMPMessageType.WELCOME, WAMPMessageType.welcome)
        self.assertEqual(WAMPMessageType.PREFIX, WAMPMessageType.pReFiX)
        with self.assertRaises(AttributeError):
            WAMPMessageType.notreal

    def test_single_instances(self):
        self.assertEqual(id(WAMPMessageType.WELCOME),
                         id(WAMPMessageType.welcome))
        self.assertNotEqual(id(WAMPMessageType.WELCOME),
                            id(WAMPMessageType('WELCOME')))
        self.assertEqual(id(WAMPMessageType.CaLl),
                         id(WAMPMessageType.cAlL))
        self.assertNotEqual(id(WAMPMessageType.WELCOME),
                            id(WAMPMessageType.CALL))

    def test_name(self):
        self.assertEqual(WAMPMessageType.welcome.name, "WELCOME")
        self.assertEqual(WAMPMessageType.prefix.name, "PREFIX")
        self.assertEqual(WAMPMessageType.call.name, "CALL")
        self.assertEqual(WAMPMessageType.callResult.name, "CALLRESULT")
        self.assertEqual(WAMPMessageType.callError.name, "CALLERROR")
        self.assertEqual(WAMPMessageType.subscribe.name, "SUBSCRIBE")
        self.assertEqual(WAMPMessageType.unsubscribe.name, "UNSUBSCRIBE")
        self.assertEqual(WAMPMessageType.publish.name, "PUBLISH")
        self.assertEqual(WAMPMessageType.event.name, "EVENT")


class TestWAMPMessage(unittest.TestCase):

    def test_init(self):
        with self.assertRaises(Exception):
            base = WAMPMessage()
        welcome = WAMPMessage(type=WAMPMessageType.WELCOME,
                              session_id="session1")
        self.assertTrue(isinstance(welcome, WAMPMessage))
        self.assertTrue(isinstance(welcome, WM.WAMPMessageWelcome))
        self.assertEqual(welcome.type, WAMPMessageType.WELCOME)
        welcome2 = WM.WAMPMessageWelcome(session_id="session2")
        self.assertTrue(isinstance(welcome2, WAMPMessage))
        self.assertTrue(isinstance(welcome2, WM.WAMPMessageWelcome))
        self.assertEqual(welcome2.type, WAMPMessageType.WELCOME)

    def test_loads(self):
        welcome = WAMPMessage.loads('[0, "session1", "protocol5", "server10"]')
        self.assertTrue(isinstance(welcome, WM.WAMPMessageWelcome))
        self.assertEqual(welcome.type, WAMPMessageType.WELCOME)
        self.assertEqual(welcome.session_id, "session1")
        self.assertEqual(welcome.protocol_version, "protocol5")
        self.assertEqual(welcome.server_ident, "server10")
        with self.assertRaises(Exception):
            welcome2 = (WM.WAMPMessageWelcome.
                        loads('[0, "session1", "protocol5", "server10"]'))

    def test_synthesized_factories(self):
        welcome = WAMPMessage.welcome("session1", "protocol5", "server10")
        self.assertTrue(isinstance(welcome, WM.WAMPMessageWelcome))
        self.assertEqual(welcome.type, WAMPMessageType.WELCOME)
        self.assertEqual(welcome.session_id, "session1")
        self.assertEqual(welcome.protocol_version, "protocol5")
        self.assertEqual(welcome.server_ident, "server10")
        with self.assertRaises(Exception):
            welcome2 = (WM.WAMPMessageWelcome.
                        welcome("session1", "protocol5", "server10"))

    def test_equality(self):
        welcome_b1 = WAMPMessage(type=WAMPMessageType.WELCOME,
                                 session_id="session1")
        welcome_w1 = WM.WAMPMessageWelcome(session_id="session1")
        welcome_b2 = WAMPMessage(type=WAMPMessageType.WELCOME,
                                 session_id="session2")
        welcome_w2 = WM.WAMPMessageWelcome(session_id="session2")
        self.assertEqual(welcome_b1, welcome_w1)
        self.assertEqual(welcome_b2, welcome_w2)
        self.assertNotEqual(welcome_b1, welcome_b2)
        self.assertNotEqual(welcome_b1, welcome_w2)
        self.assertNotEqual(welcome_w1, welcome_b2)
        self.assertNotEqual(welcome_w1, welcome_w2)
        call1 = WAMPMessage.call('call_1', 'call_uri', 'arg', {'key': 'val1'})
        call2 = WM.WAMPMessageCall('call_1', 'call_uri',
                                   'arg', {'key': 'val1'})
        call3 = WAMPMessage(WAMPMessageType.CALL,
                            'call_1', 'call_uri', 'arg', {'key': 'val2'})
        self.assertEqual(call1, call2)
        self.assertNotEqual(call1, call3)


class TestWAMPMessageSubclasses(unittest.TestCase):

    def test_welcome(self):
        welcome1 = WAMPMessage(WAMPMessageType.WELCOME, 'session_id')
        welcome2 = WM.WAMPMessageWelcome('session_id', 1)
        welcome3 = WAMPMessage.Welcome('session_id')
        welcome4 = WAMPMessage.loads('[0, "session_id", 1, 1]')
        self.assertEqual(welcome1, welcome2)
        self.assertEqual(welcome1, welcome3)
        self.assertEqual(welcome1, welcome4)
        list1 = welcome1.json
        list2 = welcome2.json
        list3 = welcome3.json
        list4 = welcome4.json
        self.assertEqual(list1, [WAMPMessageType.WELCOME, 'session_id', 1, 1])
        self.assertEqual(list1, list2)
        self.assertEqual(list2, list3)
        self.assertEqual(list3, list4)
        string1 = str(welcome1)
        string2 = str(welcome2)
        string3 = str(welcome3)
        string4 = str(welcome4)
        self.assertEqual(string1, '[0, "session_id", 1, 1]')
        self.assertEqual(string1, string2)
        self.assertEqual(string2, string3)
        self.assertEqual(string3, string4)

    def test_prefix(self):
        prefix1 = WAMPMessage(WAMPMessageType.PREFIX, 'prefix', 'uri')
        prefix2 = WM.WAMPMessagePrefix('prefix', 'uri')
        prefix3 = WAMPMessage.Prefix('prefix', 'uri')
        prefix4 = WAMPMessage.loads('[1, "prefix", "uri"]')
        self.assertEqual(prefix1, prefix2)
        self.assertEqual(prefix1, prefix3)
        self.assertEqual(prefix1, prefix4)
        list1 = prefix1.json
        list2 = prefix2.json
        list3 = prefix3.json
        list4 = prefix4.json
        self.assertEqual(list1, [WAMPMessageType.PREFIX, 'prefix', 'uri'])
        self.assertEqual(list1, list2)
        self.assertEqual(list2, list3)
        self.assertEqual(list3, list4)
        string1 = str(prefix1)
        string2 = str(prefix2)
        string3 = str(prefix3)
        string4 = str(prefix4)
        self.assertEqual(string1, '[1, "prefix", "uri"]')
        self.assertEqual(string1, string2)
        self.assertEqual(string2, string3)
        self.assertEqual(string3, string4)

    def test_call(self):
        call1 = WAMPMessage(WAMPMessageType.CALL, 'call1', 'proc_uri',
                            'arg1', ['arg2', 'arg3'], {'arg4': 'value4'})
        call2 = WM.WAMPMessageCall('call1', 'proc_uri', 'arg1',
                                   ['arg2', 'arg3'], {'arg4': 'value4'})
        call3 = WAMPMessage.Call('call1', 'proc_uri',
                                 'arg1', ['arg2', 'arg3'], {'arg4': 'value4'})
        call4 = WAMPMessage.loads(('[2, "call1", "proc_uri",'
                                   '"arg1", ["arg2", "arg3"],'
                                   '{"arg4":"value4"}]'))
        self.assertEqual(call1, call2)
        self.assertEqual(call1, call3)
        self.assertEqual(call1, call4)
        list1 = call1.json
        list2 = call2.json
        list3 = call3.json
        list4 = call4.json
        self.assertEqual(list1, [WAMPMessageType.CALL, 'call1',  'proc_uri',
                                 'arg1', ['arg2', 'arg3'], {'arg4': 'value4'}])
        self.assertEqual(list1, list2)
        self.assertEqual(list2, list3)
        self.assertEqual(list3, list4)
        string1 = str(call1)
        string2 = str(call2)
        string3 = str(call3)
        string4 = str(call4)
        self.assertEqual(string1, ('[2, "call1", "proc_uri", '
                                   '"arg1", ["arg2", "arg3"], '
                                   '{"arg4": "value4"}]'))
        self.assertEqual(string1, string2)
        self.assertEqual(string2, string3)
        self.assertEqual(string3, string4)

    def test_call_no_args(self):
        call1 = WAMPMessage(WAMPMessageType.CALL, 'call1', 'proc_uri')
        call2 = WM.WAMPMessageCall('call1', 'proc_uri')
        call3 = WAMPMessage.Call('call1', 'proc_uri')
        call4 = WAMPMessage.loads('[2, "call1", "proc_uri"]')
        self.assertEqual(call1, call2)
        self.assertEqual(call1, call3)
        self.assertEqual(call1, call4)
        list1 = call1.json
        list2 = call2.json
        list3 = call3.json
        list4 = call4.json
        self.assertEqual(list1, [WAMPMessageType.CALL, 'call1',  'proc_uri'])
        self.assertEqual(list1, list2)
        self.assertEqual(list2, list3)
        self.assertEqual(list3, list4)
        string1 = str(call1)
        string2 = str(call2)
        string3 = str(call3)
        string4 = str(call4)
        self.assertEqual(string1, '[2, "call1", "proc_uri"]')
        self.assertEqual(string1, string2)
        self.assertEqual(string2, string3)
        self.assertEqual(string3, string4)

    def test_result(self):
        result1 = WAMPMessage(WAMPMessageType.CALLRESULT,
                              'call1', {'key': 'value'})
        result2 = WM.WAMPMessageCallResult('call1', {'key': 'value'})
        result3 = WAMPMessage.CallResult('call1', {'key': 'value'})
        result4 = WAMPMessage.loads('[3, "call1", {"key": "value"}]')
        self.assertEqual(result1, result2)
        self.assertEqual(result1, result3)
        self.assertEqual(result1, result4)
        list1 = result1.json
        list2 = result2.json
        list3 = result3.json
        list4 = result4.json
        self.assertEqual(list1, [WAMPMessageType.CALLRESULT,
                                 'call1', {'key': 'value'}])
        self.assertEqual(list1, list2)
        self.assertEqual(list2, list3)
        self.assertEqual(list3, list4)
        string1 = str(result1)
        string2 = str(result2)
        string3 = str(result3)
        string4 = str(result4)
        self.assertEqual(string1, '[3, "call1", {"key": "value"}]')
        self.assertEqual(string1, string2)
        self.assertEqual(string2, string3)
        self.assertEqual(string3, string4)

    def test_error(self):
        error1 = WAMPMessage(WAMPMessageType.CALLERROR,
                             'call1', 'uri', 'desc', {'key': 'value'})
        error2 = WM.WAMPMessageCallError('call1', 'uri', 'desc',
                                         {'key': 'value'})
        error3 = WAMPMessage.CallError('call1', 'uri', 'desc',
                                       {'key': 'value'})
        error4 = WAMPMessage.loads('[4, "call1", "uri", "desc", '
                                   '{"key": "value"}]')
        self.assertEqual(error1, error2)
        self.assertEqual(error1, error3)
        self.assertEqual(error1, error4)
        list1 = error1.json
        list2 = error2.json
        list3 = error3.json
        list4 = error4.json
        self.assertEqual(list1, [WAMPMessageType.CALLERROR,
                                 'call1', 'uri', 'desc', {'key': 'value'}])
        self.assertEqual(list1, list2)
        self.assertEqual(list2, list3)
        self.assertEqual(list3, list4)
        string1 = str(error1)
        string2 = str(error2)
        string3 = str(error3)
        string4 = str(error4)
        self.assertEqual(string1,
                         '[4, "call1", "uri", "desc", {"key": "value"}]')
        self.assertEqual(string1, string2)
        self.assertEqual(string2, string3)
        self.assertEqual(string3, string4)

    def test_error_no_args(self):
        error1 = WAMPMessage(WAMPMessageType.CALLERROR, 'call1', 'uri', 'desc')
        error2 = WM.WAMPMessageCallError('call1', 'uri', 'desc')
        error3 = WAMPMessage.callerror('call1', 'uri', 'desc')
        error4 = WAMPMessage.loads('[4, "call1", "uri", "desc"]')
        self.assertEqual(error1, error2)
        self.assertEqual(error1, error3)
        self.assertEqual(error1, error4)
        list1 = error1.json
        list2 = error2.json
        list3 = error3.json
        list4 = error4.json
        self.assertEqual(list1, [WAMPMessageType.CALLERROR,
                                 'call1',  'uri', 'desc'])
        self.assertEqual(list1, list2)
        self.assertEqual(list2, list3)
        self.assertEqual(list3, list4)
        string1 = str(error1)
        string2 = str(error2)
        string3 = str(error3)
        string4 = str(error4)
        self.assertEqual(string1, '[4, "call1", "uri", "desc"]')
        self.assertEqual(string1, string2)
        self.assertEqual(string2, string3)
        self.assertEqual(string3, string4)

    def test_subscribe(self):
        subscribe1 = WAMPMessage(WAMPMessageType.SUBSCRIBE, 'topic')
        subscribe2 = WM.WAMPMessageSubscribe('topic')
        subscribe3 = WAMPMessage.Subscribe('topic')
        subscribe4 = WAMPMessage.loads('[5, "topic"]')
        self.assertEqual(subscribe1, subscribe2)
        self.assertEqual(subscribe1, subscribe3)
        self.assertEqual(subscribe1, subscribe4)
        list1 = subscribe1.json
        list2 = subscribe2.json
        list3 = subscribe3.json
        list4 = subscribe4.json
        self.assertEqual(list1, [WAMPMessageType.SUBSCRIBE, 'topic'])
        self.assertEqual(list1, list2)
        self.assertEqual(list2, list3)
        self.assertEqual(list3, list4)
        string1 = str(subscribe1)
        string2 = str(subscribe2)
        string3 = str(subscribe3)
        string4 = str(subscribe4)
        self.assertEqual(string1, '[5, "topic"]')
        self.assertEqual(string1, string2)
        self.assertEqual(string2, string3)
        self.assertEqual(string3, string4)

    def test_unsubscribe(self):
        unsubscribe1 = WAMPMessage(WAMPMessageType.UNSUBSCRIBE, 'topic')
        unsubscribe2 = WM.WAMPMessageUnsubscribe('topic')
        unsubscribe3 = WAMPMessage.Unsubscribe('topic')
        unsubscribe4 = WAMPMessage.loads('[6, "topic"]')
        self.assertEqual(unsubscribe1, unsubscribe2)
        self.assertEqual(unsubscribe1, unsubscribe3)
        self.assertEqual(unsubscribe1, unsubscribe4)
        list1 = unsubscribe1.json
        list2 = unsubscribe2.json
        list3 = unsubscribe3.json
        list4 = unsubscribe4.json
        self.assertEqual(list1, [WAMPMessageType.UNSUBSCRIBE, 'topic'])
        self.assertEqual(list1, list2)
        self.assertEqual(list2, list3)
        self.assertEqual(list3, list4)
        string1 = str(unsubscribe1)
        string2 = str(unsubscribe2)
        string3 = str(unsubscribe3)
        string4 = str(unsubscribe4)
        self.assertEqual(string1, '[6, "topic"]')
        self.assertEqual(string1, string2)
        self.assertEqual(string2, string3)
        self.assertEqual(string3, string4)

    def test_publish(self):
        publish1 = WAMPMessage(WAMPMessageType.PUBLISH, 'topic', 'event')
        publish2 = WM.WAMPMessagePublish('topic', 'event')
        publish3 = WAMPMessage.Publish('topic', 'event')
        publish4 = WAMPMessage.loads('[7, "topic", "event"]')
        self.assertEqual(publish1, publish2)
        self.assertEqual(publish1, publish3)
        self.assertEqual(publish1, publish4)
        list1 = publish1.json
        list2 = publish2.json
        list3 = publish3.json
        list4 = publish4.json
        self.assertEqual(list1, [WAMPMessageType.PUBLISH, 'topic', 'event'])
        self.assertEqual(list1, list2)
        self.assertEqual(list2, list3)
        self.assertEqual(list3, list4)
        string1 = str(publish1)
        string2 = str(publish2)
        string3 = str(publish3)
        string4 = str(publish4)
        self.assertEqual(string1, '[7, "topic", "event"]')
        self.assertEqual(string1, string2)
        self.assertEqual(string2, string3)
        self.assertEqual(string3, string4)

    def test_publish_filters(self):
        publish = WAMPMessage.publish('topic', 'event', True)
        self.assertEqual(publish.json, [WAMPMessageType.PUBLISH,
                                        'topic', 'event', True])
        publish = WAMPMessage.publish('topic', 'event', 'ex1')
        self.assertEqual(publish.json, [WAMPMessageType.PUBLISH,
                                        'topic', 'event', ['ex1']])
        publish = WAMPMessage.publish('topic', 'event', ['ex1', 'ex2'])
        self.assertEqual(publish.json, [WAMPMessageType.PUBLISH,
                                        'topic', 'event', ['ex1', 'ex2']])
        publish = WAMPMessage.publish('topic', 'event', None, 'el1')
        self.assertEqual(publish.json, [WAMPMessageType.PUBLISH,
                                        'topic', 'event', [], ['el1']])
        publish = WAMPMessage.publish('topic', 'event', None, ['el1', 'el2'])
        self.assertEqual(publish.json, [WAMPMessageType.PUBLISH,
                                        'topic', 'event', [], ['el1', 'el2']])
        publish = WAMPMessage.publish('topic', 'event', 'ex1', 'el1')
        self.assertEqual(publish.json, [WAMPMessageType.PUBLISH,
                                        'topic', 'event', ['ex1'], ['el1']])
        with self.assertRaises(AssertionError):
            publish = WAMPMessage.publish('topic', 'event', True, 'el1')

    def test_event(self):
        event1 = WAMPMessage(WAMPMessageType.EVENT, 'topic', 'event')
        event2 = WM.WAMPMessageEvent('topic', 'event')
        event3 = WAMPMessage.Event('topic', 'event')
        event4 = WAMPMessage.loads('[8, "topic", "event"]')
        self.assertEqual(event1, event2)
        self.assertEqual(event1, event3)
        self.assertEqual(event1, event4)
        list1 = event1.json
        list2 = event2.json
        list3 = event3.json
        list4 = event4.json
        self.assertEqual(list1, [WAMPMessageType.EVENT, 'topic', 'event'])
        self.assertEqual(list1, list2)
        self.assertEqual(list2, list3)
        self.assertEqual(list3, list4)
        string1 = str(event1)
        string2 = str(event2)
        string3 = str(event3)
        string4 = str(event4)
        self.assertEqual(string1, '[8, "topic", "event"]')
        self.assertEqual(string1, string2)
        self.assertEqual(string2, string3)
        self.assertEqual(string3, string4)


if __name__ == '__main__':
    unittest.main()
