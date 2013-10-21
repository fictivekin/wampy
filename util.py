from collections import Iterable


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
