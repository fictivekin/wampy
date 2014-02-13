from collections import Iterable
from weakref import ref
from inspect import getargspec
import re


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

    try:
        argspec = getargspec(fn.__call__)
        implied_self = True
    except (TypeError, AttributeError):
        argspec = getargspec(fn)
        implied_self = False
    accepts_n = len(argspec.args) if argspec.args else 0
    if implied_self or (getattr(fn, '__self__', None) is not None):
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


class AttributeFactoryMixin(object):

    """
    a meta-class mix-in that auto-generates class instances

    When an attribute is accessed as a class attribute, if the attribute
    is not found via the standard attribute resolution mechanism, a new
    instance of the class will be created, using the attribute name as
    a parameter to the __new__ class method.

    E.g, MyClass.foo will first try to find the 'foo' attribute
    if MyClass and, failing that, will use the value of
    MyClass.__new__('foo') (and store that value for further accesses

    NB: this mixin should be applied to the metaclass
    """

    _attr_re = re.compile("has no attribute '(.*)'$")

    @staticmethod
    def _get_or_memoize(cls, name, value=None, new=None):
        get = super(AttributeFactoryMixin, cls).__getattribute__
        try:
            return get(name)
        except AttributeError as e:
            match = AttributeFactoryMixin._attr_re.search(e.message)
            new_name = name if match is None else match.group(1)
            new_value = value or new_name
            new = new or get('__new__')
            setattr(cls, new_name, new(cls, new_value))
            return get(name)

    def __getattribute__(cls, name):
        return AttributeFactoryMixin._get_or_memoize(cls, name)


class _EnumishMixin(object):

    """
    a mixin for creating enum-ish classes

    Classes with this mixin can be instantiated by int or str,
    where the parameters are constrained to be in the _values list,
    i.e., an int must be less than len(cls._values), and a str must
    be in cls.values
    """

    class EnumishMetaclass(AttributeFactoryMixin, type):
        pass

    __metaclass__ = EnumishMetaclass
    _values = NotImplemented
    _basetype = NotImplemented

    def __new__(cls, value):
        if isinstance(value, int):
            if value >= len(cls._values):
                raise AttributeError("%s: %d is not a valid value" %
                                     (cls.__name__, value))
            values = {int: value, str: cls._values[value]}
        elif isinstance(value, basestring):
            if value not in cls._values:
                raise AttributeError("%s: '%s' is not a valid value" %
                                     (cls.__name__, value))
            values = {int: cls._values.index(value), str: value}
        else:
            raise TypeError("%s: argument must be <int> or <str>" %
                            cls.__name__)
        return cls.__metaclass__._get_or_memoize(
            cls, values[str], values[cls._basetype], cls._basetype.__new__)


class EnumishStr(_EnumishMixin, str):

    """ an enumish class where each instance is a str """

    _basetype = str


class EnumishInt(_EnumishMixin, int):

    """ an enumish class where each instance is an int """

    _basetype = int
