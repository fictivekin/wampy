import unittest
import json
import wampmessage as WAMPMessage
from wampmessage import WAMPMessageType


class TestWAMPMessage(unittest.TestCase):

    def test_message_types(self):
        self.assertEqual(WAMPMessageType.WELCOME, 0)
        self.assertEqual(WAMPMessageType.PREFIX, 1)
        self.assertEqual(WAMPMessageType.CALL, 2)
        self.assertEqual(WAMPMessageType.CALLRESULT, 3)
        self.assertEqual(WAMPMessageType.CALLERROR, 4)
        self.assertEqual(WAMPMessageType.SUBSCRIBE, 5)
        self.assertEqual(WAMPMessageType.UNSUBSCRIBE, 6)
        self.assertEqual(WAMPMessageType.PUBLISH, 7)
        self.assertEqual(WAMPMessageType.EVENT, 8)

    def checked_message_obj(self, message):
        self.assertIsInstance(message, str)
        message_obj = json.loads(message)
        self.assertIsInstance(message_obj, list)
        return message_obj

    def test_welcome(self):
        message = WAMPMessage.welcome('12345', server_ident='my_server')
        result = self.checked_message_obj(message)
        self.assertEqual(result,
                         [WAMPMessageType.WELCOME, '12345', 1, 'my_server'])

    def test_prefix(self):
        message = WAMPMessage.prefix('prefix', 'uri')
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.PREFIX, 'prefix', 'uri'])

    def test_call(self):
        message = WAMPMessage.call('12345', 'proc/uri')
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.CALL, '12345', 'proc/uri'])

        message = WAMPMessage.call('12345', 'proc/uri', 'arg1')
        result = self.checked_message_obj(message)
        self.assertEqual(result,
                         [WAMPMessageType.CALL, '12345', 'proc/uri', 'arg1'])

        message = WAMPMessage.call('12345', 'proc/uri', ['arg1', 'arg2'])
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.CALL,
                                  '12345', 'proc/uri', ['arg1', 'arg2']])

        message = WAMPMessage.call('123', 'proc/uri', 'arg1', 'arg2', 'arg3')
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.CALL,
                                  '123', 'proc/uri', 'arg1', 'arg2', 'arg3'])

    def test_result(self):
        message = WAMPMessage.call_result('result_id', 'the result')
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.CALLRESULT,
                                  'result_id', 'the result'])

    def test_error(self):
        message = WAMPMessage.call_error('err_id', 'err_uri', 'err_desc')
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.CALLERROR,
                                  'err_id', 'err_uri', 'err_desc'])

        message = WAMPMessage.call_error('id', 'uri', 'desc', 'err_det')
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.CALLERROR,
                                  'id', 'uri', 'desc', 'err_det'])

    def test_subscribe(self):
        message = WAMPMessage.subscribe('topic/uri')
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.SUBSCRIBE, 'topic/uri'])

    def test_unsubscribe(self):
        message = WAMPMessage.unsubscribe('topic/uri')
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.UNSUBSCRIBE, 'topic/uri'])

    def test_publish(self):
        message = WAMPMessage.publish('topic/uri', 'event!')
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.PUBLISH,
                                  'topic/uri', 'event!'])

        message = WAMPMessage.publish('topic/uri', 'event!', True)
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.PUBLISH,
                                  'topic/uri', 'event!', True])

        message = WAMPMessage.publish('topic/uri', 'event!', ['ex1'])
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.PUBLISH,
                                  'topic/uri', 'event!', ['ex1']])

        message = WAMPMessage.publish('topic/uri', 'event!', eligible=['el1'])
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.PUBLISH,
                                  'topic/uri', 'event!', [], ['el1']])

        message = WAMPMessage.publish('topic/uri', 'event!',
                                      exclude=['ex1'], eligible=['el1'])
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.PUBLISH,
                                  'topic/uri', 'event!', ['ex1'], ['el1']])

        with self.assertRaises(AssertionError):
            WAMPMessage.publish('topic/uri', 'event!', False, eligible=['el1'])

        with self.assertRaises(AssertionError):
            WAMPMessage.publish('topic/uri', 'event!', True, ['ex1'])

    def test_event(self):
        message = WAMPMessage.event('topic/uri', 'event!')
        result = self.checked_message_obj(message)
        self.assertEqual(result, [WAMPMessageType.EVENT,
                                  'topic/uri', 'event!'])


if __name__ == '__main__':
    unittest.main()
