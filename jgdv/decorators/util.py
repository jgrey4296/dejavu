"""
Utility decorators
"""
#pylint: disable=invalid-sequence-index
##-- imports
from __future__ import annotations

import logging as logmod
from enum import Enum
from functools import wraps
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Dict, Generic,
                    Iterable, Iterator, List, Mapping, Match, MutableMapping,
                    Optional, ParamSpec, Sequence, Set, Tuple, TypeAlias,
                    TypeVar, Union, cast)

##-- end imports

logging = logmod.getLogger(__name__)
T = TypeVar('T')
P = ParamSpec('P')

JGDV_ANNOTATIONS : Final[str]                = "__JGDV_ANNOTATIONS__"
KEYS_HANDLED   : Final[str]                = "_jgdv_keys_handler"
ORIG_ARGS      : Final[str]                = "_jgdv_orig_args"
KEY_ANNOTS     : Final[str]                = "_jgdv_keys"
FUNC_WRAPPED   : Final[str]                = "__wrapped__"
PARAM_PREFIX   : Final[str] = "_"
PARAM_SUFFIX   : Final[str] = "_ex"

def ForceListArgDecorator(f:Callable[..., T]) -> Callable[..., T]:
    """ Force the first arg to be a list """

    @wraps(f)
    def wrapped(self, *the_args, **the_kwargs):
        forced = []
        if isinstance(the_args[0], list):
            forced = the_args
        else:
            forced.append([the_args[0]])
            forced += the_args[1:]

        return f(self, *forced, **the_kwargs)

    return wrapped

def cache(f:Callable[..., T]) -> Callable[..., T]:
    cache_key : str = f"{f.__name__}.__cached_val"

    @wraps(f)
    def wrapped(self, *args, **kwargs):
        if hasattr(self, cache_key): #type:ignore
            return cast(T, getattr(self, cache_key)) #type:ignore

        object.__setattr__(self, cache_key, f(self, *args, **kwargs)) #type:ignore
        return getattr(self, cache_key) #type:ignore

    wrapped.__name__ = f"Cached({f.__name__})"
    return wrapped #type:ignore

def invalidate_cache(f:Callable[..., T]) -> Callable[..., T]:
    cache_key = f"{f.__name__}__cached_val"

    @wraps(f)
    def wrapped(self, *args, **kwargs):
        if hasattr(self, cache_key): #type:ignore
            object.__setattr__(self, cache_key, None) #type:ignore

        return f(self, *args, **kwargs)

    wrapped.__name__ = f"CacheInvalidatator({f.__name__})"
    return wrapped

def HandleSignal(sig : str) -> Callable[..., Any]:
    """
    Utility to easily add a signal to classes for use in the handler system
    """

    def __add_sig(sig, method):
        """ used to add 'signal' as an argument to a class' init method """

        @wraps(method)
        def wrapper(self, *args, **kwargs):
            if 'signal' not in kwargs:
                kwargs['signal'] = sig #type:ignore
            return method(self, *args, **kwargs)

        return wrapper

    def wrapper(cls):
        cls.__init__ = __add_sig(sig, cls.__init__) #type:ignore
        return cls

    return wrapper

def factory(f:Callable[..., T]) -> Callable[..., T]:
    """
    Curry a constructor, naming it in a useful way

    """

    @wraps(f)
    def awaiting_arg(first_arg:Any) -> Callable[..., T]:

        @wraps(f)
        def ready_to_apply(*args:Any, **kwargs:Any) -> T:
            return f(first_arg, *args, **kwargs)

        ready_to_apply.__name__ = f"{f.__name__} partial"
        return ready_to_apply

    return awaiting_arg #type:ignore

class DecorationUtils:

    _annot = JGDV_ANNOTATIONS

    @staticmethod
    def _unwrap(fn:callable) -> callable:
        # if not hasattr(fn, FUNC_WRAPPED):
        #     return fn

        # return getattr(fn, FUNC_WRAPPED)
        return inspect.unwrap(fn)

    @staticmethod
    def verify_signature(fn, head:list, tail:list=None) -> bool:
        match fn:
            case inspect.Signature():
                sig = fn
            case _:
                sig = inspect.signature(fn, follow_wrapped=False)

        params      = list(sig.parameters)
        tail        = tail or []
        for x,y in zip(params, head):
            if x != y:
                logging.debug("Mismatch in signature head: %s != %s", x, y)
                return False

        for x,y in zip(params[::-1], tail[::-1]):
            key_str = str(y)
            if x.startswith(PARAM_PREFIX) or x.endswith(PARAM_SUFFIX):
                continue
            if keyword.iskeyword(key_str):
                logging.debug("Key is a keyword, the function sig needs to use _{} or {}_ex: %s : %s", x, y)
                return False
            if not key_str.isidentifier():
                logging.debug("Key is not an identifier, the function sig needs to use _{} or {}_ex: %s : %s", x,y)
                return False

            if x != y:
                logging.debug("Mismatch in signature tail: %s != %s", x, y)
                return False

        return True

    def verify_action_signature(fn:Signature|callable, args:list) -> bool:
        match fn:
            case inspect.Signature():
                sig = fn
            case _:
                sig = inspect.signature(fn, follow_wrapped=False)

        match sig.parameters.get("self", None):
            case None:
                head_sig = ["spec", "state"]
            case _:
                head_sig = ["self", "spec", "state"]

        return DecorationUtils.verify_signature(sig, head_sig, args)

    @staticmethod
    def manipulate_signature(fn, args) -> callable:
        pass

    @staticmethod
    def has_annotations(fn, *keys) -> bool:
        if not hasattr(fn, JGDV_ANNOTATIONS):
            return False

        annots = getattr(fn, JGDV_ANNOTATIONS)
        return all(key in annots for key in keys)

    @staticmethod
    def annotate(fn:callable, annots:dict|set) -> callable:
        match annots:
            case dict():
                fn.__dict__.update(annots)
            case set():
                if not hasattr(fn, JGDV_ANNOTATIONS):
                    setattr(fn, JGDV_ANNOTATIONS, set())

                annotations = getattr(fn, JGDV_ANNOTATIONS)
                annotations.update(annots)
        return fn

    @staticmethod
    def truncate_signature(fn):
        """
           actions are (self?, spec, state)
          with and extracted keys from the spec and state.
          This truncates the signature of the action to what is *called*, not what is *used*.

          TODO: could take a callable as the prototype to build the signature from
        """
        sig = inspect.signature(fn)
        min_index = len(sig.parameters) - len(getattr(fn, KEY_ANNOTS))
        newsig = sig.replace(parameters=list(sig.parameters.values())[:min_index])
        fn.__signature__ = newsig
        return fn

    @staticmethod
    def _update_key_annotations(fn, keys:list[JGDVKey]) -> True:
        """ update the declared expansion keys on the wrapped action """
        sig = inspect.signature(fn)

        # prepend annotations, so written decorator order is the same as written arg order:
        # (ie: @wrap(x) @wrap(y) @wrap(z) def fn (x, y, z), even though z's decorator is applied first
        new_annotations = keys + getattr(fn, KEY_ANNOTS, [])
        setattr(fn, KEY_ANNOTS, new_annotations)

        if not DecorationUtils.verify_action_signature(sig, new_annotations):
            raise doot.errors.DootKeyError("Annotations do not match signature", sig)

        return True

    @staticmethod
    def prepare_expansion(keys:list[JGDVKey], fn):
        """ used as a partial fn. adds declared keys to a function,
          and idempotently adds the expansion decorator
        """
        is_func = True
        match DecorationUtils._unwrap(fn):
            case x if DecorationUtils.has_annotations(x, KEYS_HANDLED):
                DecorationUtils._update_key_annotations(x, keys)
                return fn
            case orig:
                is_func = inspect.signature(orig).parameters.get("self", None) is None
                DecorationUtils._update_key_annotations(x, keys)
                DecorationUtils.annotate(orig, {KEYS_HANDLED})

        match is_func:
            case False:
                wrapper = DecorationUtils.add_method_expander(fn)
            case True:
                wrapper = DecorationUtils.add_fn_expander(fn)

        return wrapper

    @staticmethod
    def add_method_expander(fn):

        @ftz.wraps(fn)
        def method_action_expansions(self, spec, state, *call_args, **kwargs):
            try:
                expansions = [x(spec, state) for x in getattr(fn, KEY_ANNOTS)]
            except KeyError as err:
                printer.warning("Action State Expansion Failure: %s", err)
                return False
            all_args = (*call_args, *expansions)
            return fn(self, spec, state, *all_args, **kwargs)

        # -
        return method_action_expansions

    @staticmethod
    def add_fn_expander(fn):

        @ftz.wraps(fn)
        def fn_action_expansions(spec, state, *call_args, **kwargs):
            try:
                expansions = [x(spec, state) for x in getattr(fn, KEY_ANNOTS)]
            except KeyError as err:
                printer.warning("Action State Expansion Failure: %s", err)
                return False
            all_args = (*call_args, *expansions)
            return fn(spec, state, *all_args, **kwargs)

        # -
        return fn_action_expansions
