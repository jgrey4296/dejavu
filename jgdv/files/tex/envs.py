#!/usr/bin/env python3
"""


See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

# import abc
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

from jgdv.files.tex.base import TexStatement_i, TexEnvironment_i

class TexFigure(TexEnvironment_i):
    pass

class TexEquation(TexEnvironment_i):
    pass

class TexProof(TexEnvironment_i):
    pass

class TexVerbatim(TexEnvironment_i):
    pass

class TexItemList(TexEnvironment_i):
    pass

class TexTikz(TexEnvironment_i):
    pass

class TexGantt(TexTiz):
    pass


class TexFont(TexEnvironment_i):
    pass

class TexMath(TexEnvironment_i):
    pass
