#!/usr/bin/env python3
"""
Pytest testing fixtures
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

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

import pytest
import os
import doot

##-- imports
import tempfile
##-- end imports

# with tempfile.TemporaryDirectory() as temp_dir:
#      assert(isisntance(temp_dir, str))
#      # Do Stuff

# On Exit of context manager, dir is deleted

def _add_prop(m, name, val):
    setattr(type(m), name, PropertyMock(return_value=val))


def filter_str_warns():
    warnings.warn(DeprecationWarning("invalid escape sequence"))
    return 1

# @pytest.mark.filterwarnings("ignore:filter_str_warns")
# def test_...


@pytest.fixture
def wrap_tmp(tmp_path):
    """ create a new temp directory, and change cwd to it,
      returning to original cwd after the test
      """
    logging.debug("Moving to temp dir")
    orig     = pl.Path().cwd()
    new_base = tmp_path / "test_root"
    new_base.mkdir()
    os.chdir(new_base)
    doot.locs._root = new_base
    yield new_base
    logging.debug("Returning to original dir")
    os.chdir(orig)
    doot.locs._root = orig
