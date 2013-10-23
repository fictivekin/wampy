from collections import Iterable
from weakref import ref
from inspect import getargspec, ismethod


def none_or_equal(a, b):
    """ returns True if a is None or a == b """
    return a is None or a == b


def iterablate(target, wrapper_cls=tuple, also_wrap=None):
    """ convert target variable to a list-ish type variable

    If target is not an iterable (and is not derived from a basestring
    or a dict), wrap target inside an iterable.  This can facilitate,
    e.g., bi-modal parameters to functions (i.e., functions that accept
    a value or a list of values in the same parameter).

    Keyword arguments:
    target: the object to iterablate
    wrapper_cls: the iterable class that will be used to wrap target
    also_wrap: additional classes to wrap (whether iterable or not)

    Return value:
    an iterable, either target (unmodified), or an instance of wrapper_cls
    that contains target
    """
    if target is None:
        return wrapper_cls()
    also_wrap = iterablate(also_wrap)
    for also_cls in also_wrap:
        if isinstance(target, also_cls):
            return wrapper_cls([target])
            break
    if (isinstance(target, basestring) or
        isinstance(target, dict) or
            not isinstance(target, Iterable)):
        return wrapper_cls([target])
    return target


def check_signature(_callable, num_args=None, min_args=0, max_args=None):
    """ Checks the call signature of a provided callable

    Ensures a priori that the callable can accept the specified
    number(s) of arguments

    Keyword arguments:
    _callable: the callable that will be inspected

    num_args: exact number of arguments to check function compatibility.
    If num_args is not None, min_args and max_args are ignored

    min_args, max_args: specify range of argument list lengths to check
    function compatibility.  A value of None for max_args indicates no upper
    bound on the number of arguments the callable must accept
    """
    if num_args is not None:
        min_args = num_args
        max_args = num_args
    if max_args is not None:
        assert(max_args >= min_args), \
            "max_args(%d) < min_args(%d)" % (max_args, min_args)

    argspec = getargspec(_callable)
    call_arg_num = len(argspec.args) if argspec.args else 0
    if hasattr(_callable, '__self__'):
        call_arg_num -= 1
    defaults_num = len(argspec.defaults) if argspec.defaults else 0
    required = call_arg_num - defaults_num
    if required >= 0:
        assert min_args >= required, \
            "min_args(%d) < required by callable(%d)" % (min_args, required)
    if not argspec.varargs:
        assert max_args is not None, \
            "max_args is not defined, callable must accept *args"
        assert max_args <= call_arg_num, \
            "max_args(%d) > accepted by callable(%d)" % (
                max_args, call_arg_num)


class WeaklyBoundCallable(object):

    """
    a callable that can be weakly bound to an object

    Normally, a bound function (e.g., a bound method) will retain the
    bound parameter and prevent garbage collection thereof.  This class
    simulates the call semantics of a bound function, but only holds
    a weak reference to the bound object.

    If the wrapped function is a bound method, this will "unbind" it
    for memory management purposes and "rebind" it on call.
    """

    def __init__(self, fn):
        self.__func__ = getattr(fn, '__func__', fn)
        try:
            self.__self__ = getattr(fn, '__self__')
            self._is_bound = True
        except AttributeError:
            self._is_bound = False

    @property
    def __self__(self):
        return self.__self() if self.__self is not None else None

    @__self__.setter
    def __self__(self, value):
        self.__self = ref(value) if value is not None else None

    @__self__.deleter
    def __self__(self):
        del self.__self

    def __call__(self, *args, **kwargs):
        if self._is_bound:
            return self.__func__(self.__self__, *args, **kwargs)
        else:
            return self.__func__(*args, **kwargs)

    def __eq__(self, other):
        if isinstance(other, WeaklyBoundCallable):
            f = self.__func__ == getattr(other, '__func__', other)
            b = self._is_bound == other._is_bound
            s = self.__self__ == other.__self__
            return f and b and s
        return False

    def __ne__(self, other):
        return not (self.__eq__(other))

    def __hash__(self):
        return id(self.__func__) ^ id(self.__self__)
