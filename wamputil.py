from collections import Iterable
from weakref import ref
from inspect import getargspec


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


def check_signature(fn, num_args=None, min_args=0, max_args=None):
    """ Checks the call signature of a provided callable

    Ensures a priori that the callable can accept the specified
    number(s) of arguments

    Keyword arguments:
    fn: the callable that will be inspected

    num_args: exact number of arguments to check function compatibility.
    If num_args is not None, min_args and max_args are ignored

    min_args, max_args: specify range of argument list lengths to check
    function compatibility.  A value of None for max_args indicates no upper
    bound on the number of arguments the callable must accept
    """
    if num_args is not None:
        min_args = num_args
        max_args = num_args
    if max_args is not None and max_args < min_args:
        raise ValueError("max_args cannot be less than min_args(%d)")

    argspec = getargspec(fn)
    accepts_n = len(argspec.args) if argspec.args else 0
    if hasattr(fn, '__self__'):
        accepts_n -= 1
    defaults = len(argspec.defaults) if argspec.defaults else 0
    required = accepts_n - defaults
    if required >= 0 and min_args < required:
        raise TypeError("%s requires at least %d free parameters"
                        " but might be called with as few as %d" %
                        (str(fn), required, min_args))
    if not argspec.varargs:
        if max_args is None or max_args > accepts_n:
            if max_args is None:
                detail = "%d or more" % min_args
            else:
                detail = "%d" % max_args
            raise TypeError("%s can't accept more than %d free parameters"
                            " but might be called with %s" %
                            (str(fn), accepts_n, detail))


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
            self.__self__ = fn.__self__
            self._is_bound = True
        except AttributeError:
            self._is_bound = False
        self._stored_hash = id(self.__func__) ^ id(self.__self__)

    @property
    def __self__(self):
        return self._ref() if hasattr(self, '_ref') else None

    @__self__.setter
    def __self__(self, value):
        if value is not None:
            self._ref = ref(value)

    @__self__.deleter
    def __self__(self):
        del self._ref

    def reverted(self):
        """ returns copy of callable with original bind state"""

        if self._is_bound:
            return self.__func__.__get__(self.__self__)
        else:
            return self.__func__

    def __call__(self, *args, **kwargs):
        if self._is_bound:
            return self.__func__(self.__self__, *args, **kwargs)
        else:
            return self.__func__(*args, **kwargs)

    def __eq__(self, other):
        if isinstance(other, WeaklyBoundCallable):
            h = self._stored_hash == other._stored_hash
            f = self.__func__ == getattr(other, '__func__', other)
            b = self._is_bound == other._is_bound
            s = self.__self__ == other.__self__
            return h and f and b and s
        return False

    def __ne__(self, other):
        return not (self.__eq__(other))

    def __hash__(self):
        return self._stored_hash


class UppercaseAliasingMixin(object):

    """
    a mix-in that aliases attributes to UPPERCASE equivalents

    E.g., assuming a class with method `MY_METHOD`, this mixin
    aliases `instance.my_method`, `instance.mY_mEtHoD`, etc.

    If you want this to affect class methods, this mixin should
    be added to the relevant metaclass
    """

    def __getattribute__(this, name):
        super_proxy = super(UppercaseAliasingMixin, this)
        try:
            return super_proxy.__getattribute__(name)
        except AttributeError:
            upper_name = name.upper()
            return super_proxy.__getattribute__(upper_name)


class AttributeFactoryMixin(object):

    """
    a meta-class mix-in that auto-generates class instances

    When an attribute is accessed as a class attribute, if the attribute
    is not found via the standard attribute resolution mechanism, a new
    instance of the class will be created, using the attribute name as
    a parameter to the __new__ class method.

    E.g, MyClass.foo will first try to find the 'foo' attribute
    if MyClass and, failing that, will return MyClass.__new__('foo')

    NB: this mixin should be applied to the metaclass
    """

    def __getattribute__(cls, name):
        super_proxy = super(AttributeFactoryMixin, cls)
        try:
            return super_proxy.__getattribute__(name)
        except AttributeError:
            return cls.__new__(cls, name)
