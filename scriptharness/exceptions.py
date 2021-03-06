#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Scriptharness exceptions.
"""
from __future__ import absolute_import, division, print_function, \
                       unicode_literals
import six


# py2 unicode help.  This may move into a separate file later.
def to_unicode(obj, encoding='utf-8'):
    """Encode a string as unicode in python2.

    http://farmdev.com/talks/unicode/

    Args:
        obj (str): the string to encode
        encoding (str, optional): the encoding to use

    Returns:
        obj (unicode): the encoded string
    """
    if not isinstance(obj, six.text_type):
        obj = six.text_type(obj, encoding)
    return obj

@six.python_2_unicode_compatible
class ScriptHarnessBaseException(Exception):
    """All scriptharness exceptions should inherit this exception.

    However, in most cases you probably want to catch ScriptHarnessException
    instead.
    """
    def __str__(self):
        """
        """
        if six.PY3:
            string = super(ScriptHarnessBaseException, self).__str__()
        else:
            string = super(ScriptHarnessBaseException, self).message
        string = to_unicode(string, 'utf-8')
        return string

class ScriptHarnessException(ScriptHarnessBaseException):
    """All developer-facing exceptions should inherit this class.

    There is a problem in how scriptharness is being called.
    If you want to catch all developer-facing scriptharness exceptions,
    catch ScriptHarnessException.
    """

class ScriptHarnessError(ScriptHarnessBaseException):
    """User-facing exception.

    Scriptharness has detected an error in the running process.
    """

class ScriptHarnessFatal(SystemExit, ScriptHarnessBaseException):
    """User-facing exception.

    Scriptharness has detected a fatal failure in the running process.
    This exception should result in program termination; using try/except may
    result in unexpected or dangerous behavior.
    """
    def __str__(self):
        return ScriptHarnessBaseException.__str__(self)
