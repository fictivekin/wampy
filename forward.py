from wamputil import check_signature, WeaklyBoundCallable


class WAMPCallForwardingMixin(object):

    @property
    def forward_wamp_message(self):
        return self._forward_wamp_message

    @forward_wamp_message.setter
    def forward_wamp_message(self, value):
        check_signature(value, num_args=1)
        self._forward_wamp_message = WeaklyBoundCallable(value)

    @forward_wamp_message.deleter
    def forward_wamp_message(self):
        del self._forward_wamp_message

    def _invoke_proc_for_message(self, message):
        message.proc_uri = self.expand_uri(message.proc_uri)
        return self.forward_wamp_message(message)
