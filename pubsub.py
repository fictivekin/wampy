from collections import namedtuple, defaultdict
from weakref import WeakValueDictionary
from util import (none_or_equal, iterablate, check_signature,
                  WeaklyBoundCallable)


_services = dict()


def PubSub(service_name):

    class PubSubService(object):

        """
        Provides publish-subscribe service between local instances
        """

        class _Subscription(object):

            def __init__(self, key, callback):
                self.key = key
                self.callback = WeaklyBoundCallable(callback)

            def __eq__(self, other):
                return (self.__class__ == other.__class__ and
                        self.key == other.key and
                        self.callback == other.callback)

            def __ne__(self, other):
                return not (self.__eq__(other))

            def __hash__(self):
                return self.key.__hash__() ^ self.callback.__hash__()

        def __init__(self):
            self._subscriptions = defaultdict(WeakValueDictionary)

        def subscribe(self, subscriber, key, topic, callback):
            check_signature(callback, num_args=2)
            sub = self._Subscription(key, callback)
            self._subscriptions[topic][sub] = subscriber

        def subscriptions(self, subscriber=None, key=None, topic=None,
                          callback=None):
            report = defaultdict(list)
            if topic is not None:
                topics = iterablate(topic)
            else:
                topics = self._subscriptions.keys()
            if callback is not None:
                callback = WeaklyBoundCallable(callback)
            for topic in topics:
                topic_subs = self._subscriptions[topic]
                for sub in topic_subs.keys():
                    match = none_or_equal(subscriber, topic_subs[sub]) and \
                        none_or_equal(key, sub.key) and \
                        none_or_equal(callback, sub.callback)
                    if match:
                        record = (topic_subs[sub], sub.key,
                                  sub.callback.reverted())
                        report[topic].append(record)
            return report

        def unsubscribe(self, subscriber=None, key=None, topic=None,
                        callback=None):
            if topic is not None:
                topics = iterablate(topic)
            else:
                topics = self._subscriptions.keys()
            if callback is not None:
                callback = WeaklyBoundCallable(callback)
            for topic in topics:
                topic_subs = self._subscriptions[topic]
                for sub in topic_subs.keys():
                    remove = none_or_equal(subscriber, topic_subs[sub]) and \
                        none_or_equal(key, sub.key) and \
                        none_or_equal(callback, sub.callback)
                    if remove:
                        del topic_subs[sub]
                if len(topic_subs) <= 0:
                    del self._subscriptions[topic]

        def publish(self, topic, event, exclude=None, eligible=None):
            exclude = iterablate(exclude)
            eligible = iterablate(eligible)
            subscriptions = self._subscriptions[topic].keys()
            subscriptions = [subscription for subscription in subscriptions
                             if subscription.key not in exclude]
            if len(eligible) > 0:
                subscriptions = [subscription for subscription in subscriptions
                                 if subscription.key in eligible]
            for subscription in subscriptions:
                subscription.callback(topic, event)

    if service_name not in _services:
        _services[service_name] = PubSubService()
    return _services[service_name]