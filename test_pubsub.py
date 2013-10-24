import unittest
import gc
from pubsub import PubSub
from weakref import WeakValueDictionary
import myclass


log = dict()
log['callbacks'] = list()


def clear_log():
    log['callbacks'] = list()


class Subscriber(object):

    def __init__(self, key):
        self.key = key

    def cb1(self, topic, event):
        log['callbacks'].append((self, Subscriber.cb1, topic, event))

    def cb2(self, topic, event):
        log['callbacks'].append((self, Subscriber.cb2, topic, event))


class TestPubSub(unittest.TestCase):

    def setUp(self):
        log['callbacks'] = list()

    def test_instances(self):
        service_a = PubSub('a')
        service_b = PubSub('b')
        service_a2 = PubSub('a')
        self.assertEqual(service_a, service_a2)
        self.assertNotEqual(service_a, service_b)

    def test_subscription(self):
        service = PubSub('test_subscription')
        sub = Subscriber('sub')
        service.subscribe(sub, sub.key, 'topic', sub.cb1)
        subscriptions = service.subscriptions()
        self.assertIn('topic', subscriptions)
        self.assertIn((sub, sub.key, sub.cb1), subscriptions['topic'])

    def test_persistent_subscriptions(self):
        service = PubSub('test_pseristsent_subscriptions')
        sub = Subscriber('sub')
        service.subscribe(sub, sub.key, 'topic', sub.cb1)
        del service
        service = PubSub('test_pseristsent_subscriptions')
        subscriptions = service.subscriptions()
        self.assertIn('topic', subscriptions)
        self.assertIn((sub, sub.key, sub.cb1), subscriptions['topic'])

    def test_duplicate_subscription(self):
        service = PubSub('test_duplicate_subscription')
        sub = Subscriber('sub')
        local_dict = WeakValueDictionary()
        service.subscribe(sub, sub.key, 'topic', sub.cb1)
        service.subscribe(sub, sub.key, 'topic', sub.cb1)
        subscriptions = service.subscriptions()
        self.assertIn('topic', subscriptions)
        self.assertEqual(len(subscriptions['topic']), 1)
        self.assertIn((sub, sub.key, sub.cb1), subscriptions['topic'])

    def test_mutliple_subscriptions(self):
        service = PubSub('test_multiple_subscription')
        sub1 = Subscriber('sub1')
        sub2 = Subscriber('sub2')
        service.subscribe(sub1, sub1.key, 'topic1', sub1.cb1)
        service.subscribe(sub1, sub1.key, 'topic1', sub1.cb2)
        service.subscribe(sub1, sub1.key, 'topic2', sub1.cb1)
        service.subscribe(sub1, sub1.key, 'topic2', sub1.cb2)
        service.subscribe(sub2, sub2.key, 'topic1', sub2.cb1)
        service.subscribe(sub2, sub2.key, 'topic1', sub2.cb2)
        service.subscribe(sub2, sub2.key, 'topic2', sub2.cb1)
        service.subscribe(sub2, sub2.key, 'topic2', sub2.cb2)
        subscriptions = service.subscriptions()
        self.assertEqual(len(subscriptions), 2)
        self.assertIn('topic1', subscriptions)
        self.assertIn((sub1, sub1.key, sub1.cb1), subscriptions['topic1'])
        self.assertIn((sub1, sub1.key, sub1.cb2), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb1), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb2), subscriptions['topic1'])
        self.assertIn('topic2', subscriptions)
        self.assertIn((sub1, sub1.key, sub1.cb1), subscriptions['topic2'])
        self.assertIn((sub1, sub1.key, sub1.cb2), subscriptions['topic2'])
        self.assertIn((sub2, sub2.key, sub2.cb1), subscriptions['topic2'])
        self.assertIn((sub2, sub2.key, sub2.cb2), subscriptions['topic2'])

    def test_subscription_filter(self):
        service = PubSub('test_subscription_filter')
        sub1 = Subscriber('sub1')
        sub2 = Subscriber('sub2')
        service.subscribe(sub1, sub1.key, 'topic1', sub1.cb1)
        service.subscribe(sub1, sub1.key, 'topic1', sub1.cb2)
        service.subscribe(sub1, sub1.key, 'topic2', sub1.cb1)
        service.subscribe(sub1, sub1.key, 'topic2', sub1.cb2)
        service.subscribe(sub2, sub2.key, 'topic1', sub2.cb1)
        service.subscribe(sub2, sub2.key, 'topic1', sub2.cb2)
        service.subscribe(sub2, sub2.key, 'topic2', sub2.cb1)
        service.subscribe(sub2, sub2.key, 'topic2', sub2.cb2)
        subscriptions = service.subscriptions(subscriber=sub2)
        self.assertEqual(len(subscriptions), 2)
        self.assertIn('topic1', subscriptions)
        self.assertNotIn((sub1, sub1.key, sub1.cb1), subscriptions['topic1'])
        self.assertNotIn((sub1, sub1.key, sub1.cb2), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb1), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb2), subscriptions['topic1'])
        self.assertIn('topic2', subscriptions)
        self.assertNotIn((sub1, sub1.key, sub1.cb1), subscriptions['topic2'])
        self.assertNotIn((sub1, sub1.key, sub1.cb2), subscriptions['topic2'])
        self.assertIn((sub2, sub2.key, sub2.cb1), subscriptions['topic2'])
        self.assertIn((sub2, sub2.key, sub2.cb2), subscriptions['topic2'])
        subscriptions = service.subscriptions(key=sub1.key)
        self.assertEqual(len(subscriptions), 2)
        self.assertIn('topic1', subscriptions)
        self.assertIn((sub1, sub1.key, sub1.cb1), subscriptions['topic1'])
        self.assertIn((sub1, sub1.key, sub1.cb2), subscriptions['topic1'])
        self.assertNotIn((sub2, sub2.key, sub2.cb1), subscriptions['topic1'])
        self.assertNotIn((sub2, sub2.key, sub2.cb2), subscriptions['topic1'])
        self.assertIn('topic2', subscriptions)
        self.assertIn((sub1, sub1.key, sub1.cb1), subscriptions['topic2'])
        self.assertIn((sub1, sub1.key, sub1.cb2), subscriptions['topic2'])
        self.assertNotIn((sub2, sub2.key, sub2.cb1), subscriptions['topic2'])
        self.assertNotIn((sub2, sub2.key, sub2.cb2), subscriptions['topic2'])
        subscriptions = service.subscriptions(topic='topic1')
        self.assertEqual(len(subscriptions), 1)
        self.assertIn('topic1', subscriptions)
        self.assertIn((sub1, sub1.key, sub1.cb1), subscriptions['topic1'])
        self.assertIn((sub1, sub1.key, sub1.cb2), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb1), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb2), subscriptions['topic1'])
        self.assertNotIn('topic2', subscriptions)
        subscriptions = service.subscriptions(callback=sub1.cb1)
        self.assertEqual(len(subscriptions), 2)
        self.assertIn('topic1', subscriptions)
        self.assertIn((sub1, sub1.key, sub1.cb1), subscriptions['topic1'])
        self.assertNotIn((sub1, sub1.key, sub1.cb2), subscriptions['topic1'])
        self.assertNotIn((sub2, sub2.key, sub2.cb1), subscriptions['topic1'])
        self.assertNotIn((sub2, sub2.key, sub2.cb2), subscriptions['topic1'])
        self.assertIn('topic2', subscriptions)
        self.assertIn((sub1, sub1.key, sub1.cb1), subscriptions['topic2'])
        self.assertNotIn((sub1, sub1.key, sub1.cb2), subscriptions['topic2'])
        self.assertNotIn((sub2, sub2.key, sub2.cb1), subscriptions['topic2'])
        self.assertNotIn((sub2, sub2.key, sub2.cb2), subscriptions['topic2'])

    def test_unsubscribe(self):
        service = PubSub('test_unsubscribe')
        sub1 = Subscriber('sub1')
        sub2 = Subscriber('sub2')
        service.subscribe(sub1, sub1.key, 'topic1', sub1.cb1)
        service.subscribe(sub1, sub1.key, 'topic1', sub1.cb2)
        service.subscribe(sub1, sub1.key, 'topic2', sub1.cb1)
        service.subscribe(sub1, sub1.key, 'topic2', sub1.cb2)
        service.subscribe(sub2, sub2.key, 'topic1', sub2.cb1)
        service.subscribe(sub2, sub2.key, 'topic1', sub2.cb2)
        service.subscribe(sub2, sub2.key, 'topic2', sub2.cb1)
        service.subscribe(sub2, sub2.key, 'topic2', sub2.cb2)
        subscriptions = service.subscriptions()
        self.assertEqual(len(subscriptions), 2)
        self.assertIn('topic1', subscriptions)
        self.assertIn((sub1, sub1.key, sub1.cb1), subscriptions['topic1'])
        self.assertIn((sub1, sub1.key, sub1.cb2), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb1), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb2), subscriptions['topic1'])
        self.assertIn('topic2', subscriptions)
        self.assertIn((sub1, sub1.key, sub1.cb1), subscriptions['topic2'])
        self.assertIn((sub1, sub1.key, sub1.cb2), subscriptions['topic2'])
        self.assertIn((sub2, sub2.key, sub2.cb1), subscriptions['topic2'])
        self.assertIn((sub2, sub2.key, sub2.cb2), subscriptions['topic2'])
        self.assertIn((sub2, sub2.key, sub2.cb2), subscriptions['topic1'])
        service.unsubscribe(sub2, sub2.key, 'topic2', sub2.cb2)
        subscriptions = service.subscriptions()
        self.assertEqual(len(subscriptions), 2)
        self.assertIn('topic1', subscriptions)
        self.assertIn((sub1, sub1.key, sub1.cb1), subscriptions['topic1'])
        self.assertIn((sub1, sub1.key, sub1.cb2), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb1), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb2), subscriptions['topic1'])
        self.assertIn('topic2', subscriptions)
        self.assertIn((sub1, sub1.key, sub1.cb1), subscriptions['topic2'])
        self.assertIn((sub1, sub1.key, sub1.cb2), subscriptions['topic2'])
        self.assertIn((sub2, sub2.key, sub2.cb1), subscriptions['topic2'])
        self.assertNotIn((sub2, sub2.key, sub2.cb2), subscriptions['topic2'])
        service.unsubscribe(sub1, sub1.key, callback=sub1.cb2)
        subscriptions = service.subscriptions()
        self.assertEqual(len(subscriptions), 2)
        self.assertIn('topic1', subscriptions)
        self.assertIn((sub1, sub1.key, sub1.cb1), subscriptions['topic1'])
        self.assertNotIn((sub1, sub1.key, sub1.cb2), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb1), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb2), subscriptions['topic1'])
        self.assertIn('topic2', subscriptions)
        self.assertIn((sub1, sub1.key, sub1.cb1), subscriptions['topic2'])
        self.assertNotIn((sub1, sub1.key, sub1.cb2), subscriptions['topic2'])
        self.assertIn((sub2, sub2.key, sub2.cb1), subscriptions['topic2'])
        self.assertNotIn((sub2, sub2.key, sub2.cb2), subscriptions['topic2'])
        service.unsubscribe(callback=sub1.cb1)
        subscriptions = service.subscriptions()
        self.assertEqual(len(subscriptions), 2)
        self.assertIn('topic1', subscriptions)
        self.assertNotIn((sub1, sub1.key, sub1.cb1), subscriptions['topic1'])
        self.assertNotIn((sub1, sub1.key, sub1.cb2), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb1), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb2), subscriptions['topic1'])
        self.assertIn('topic2', subscriptions)
        self.assertNotIn((sub1, sub1.key, sub1.cb1), subscriptions['topic2'])
        self.assertNotIn((sub1, sub1.key, sub1.cb2), subscriptions['topic2'])
        self.assertIn((sub2, sub2.key, sub2.cb1), subscriptions['topic2'])
        self.assertNotIn((sub2, sub2.key, sub2.cb2), subscriptions['topic2'])
        service.unsubscribe(callback=sub2.cb1)
        subscriptions = service.subscriptions()
        self.assertEqual(len(subscriptions), 1)
        self.assertIn('topic1', subscriptions)
        self.assertNotIn((sub1, sub1.key, sub1.cb1), subscriptions['topic1'])
        self.assertNotIn((sub1, sub1.key, sub1.cb2), subscriptions['topic1'])
        self.assertNotIn((sub2, sub2.key, sub2.cb1), subscriptions['topic1'])
        self.assertIn((sub2, sub2.key, sub2.cb2), subscriptions['topic1'])
        self.assertNotIn('topic2', subscriptions)
        service.unsubscribe()
        subscriptions = service.subscriptions()
        self.assertEqual(len(subscriptions), 0)

    def test_weak_subscriptions(self):
        service = PubSub('test_weak_subscriptions')
        sub = Subscriber('sub')
        service.subscribe(sub, sub.key, 'topic', sub.cb1)
        subscriptions = service.subscriptions()
        self.assertEqual(len(subscriptions), 1)
        self.assertIn('topic', subscriptions)
        self.assertIn((sub, sub.key, sub.cb1), subscriptions['topic'])
        del sub
        del subscriptions
        gc.collect()
        subscriptions = service.subscriptions()
        self.assertEqual(len(subscriptions), 0)

    def test_publish(self):

        def callback(topic, event):
            log['callbacks'].append((callback, topic, event))
            pass

        service = PubSub('test_publish')
        sub = Subscriber('sub')
        service.subscribe(sub, sub.key, 'topic', sub.cb1)
        service.subscribe(sub, sub.key, 'topic', sub.cb2)
        service.subscribe(sub, sub.key, 'topic2', sub.cb2)
        service.subscribe(sub, sub.key, 'topic2', callback)
        service.publish('topic', 'event')
        service.publish('topic2', 'event2')
        self.assertEqual(len(log['callbacks']), 4)
        self.assertIn((sub, Subscriber.cb1, 'topic', 'event'),
                      log['callbacks'])
        self.assertIn((sub, Subscriber.cb2, 'topic', 'event'),
                      log['callbacks'])
        self.assertIn((sub, Subscriber.cb2, 'topic2', 'event2'),
                      log['callbacks'])
        self.assertIn((callback, 'topic2', 'event2'), log['callbacks'])

    def test_publish_filter(self):
        service = PubSub('test_publish_filter')
        subscribers = [Subscriber('sub%d' % i) for i in range(1, 5)]
        for sub in subscribers:
            service.subscribe(sub, sub.key, 'topic', sub.cb1)
        service.publish('topic', 'event1')
        for sub in subscribers:
            self.assertIn((sub, Subscriber.cb1, 'topic', 'event1'),
                          log['callbacks'])
        service.publish('topic', 'event2', subscribers[0].key)
        for sub in subscribers[:1]:
            self.assertNotIn((sub, Subscriber.cb1, 'topic', 'event2'),
                             log['callbacks'])
        for sub in subscribers[1:]:
            self.assertIn((sub, Subscriber.cb1, 'topic', 'event2'),
                          log['callbacks'])
        clear_log()
        service.publish('topic', 'event3',
                        subscribers[0].key, [s.key for s in subscribers[:3]])
        for sub in [subscribers[0], subscribers[3]]:
            self.assertNotIn((sub, Subscriber.cb1, 'topic', 'event3'),
                             log['callbacks'])
        for sub in subscribers[1:3]:
            self.assertIn((sub, Subscriber.cb1, 'topic', 'event3'),
                          log['callbacks'])


if __name__ == '__main__':
    unittest.main()
