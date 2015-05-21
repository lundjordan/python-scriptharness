#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Python scripting harness / framework.

Core principles:
  Full logging.
  Flexible configuration.
  Modular actions.
"""
from __future__ import absolute_import, division, print_function, \
                       unicode_literals
import os
import scriptharness.actions
from scriptharness.exceptions import ScriptHarnessException
import scriptharness.script

__all__ = [
    'get_script', 'get_config', 'set_action_class', 'set_script_class',
]


# ScriptManager {{{1
class ScriptManager(object):
    """Manage the various script objects; this is largely here to avoid
    multiple globals that pylint would complain about.

    Attributes:
      all_scripts (dict): a dict of name:script
      action_class (class): the class to instantiate for new actions
      script_class (class): the class to instantiate for new scripts
    """
    def __init__(self):
        self.all_scripts = {}
        self.script_class = scriptharness.script.Script
        self.action_class = scriptharness.actions.Action

    def get_script(self, name="root", *args, **kwargs):
        """Back end for scriptharness.get_script().

        Most python scripts will have a single `script`, but there may be more
        when parallel execution is desired.
        """
        if name not in self.all_scripts:
            self.all_scripts[name] = self.script_class(
                *args, **kwargs
            )
        return self.all_scripts[name]

    def get_config(self, name="root"):
        """Back end for scriptharness.get_config().
        """
        if name not in self.all_scripts:
            raise ScriptHarnessException(os.linesep.join([
                "scriptharness.get_config(): %s not in all_scripts!" % name,
                "use scriptharness.get_script(%s, ...) first!",
            ]))
        if not hasattr(self.all_scripts[name], 'config'):
            raise ScriptHarnessException(os.linesep.join([
                "all_scripts[%s] doesn't have an attribute 'config'!" % name,
                "No idea how that happened."
            ]))
        return self.all_scripts[name].config

    def set_action_class(self, action_class):
        """Back end for scriptharness.set_action_class().
        """
        self.action_class = action_class

    def set_script_class(self, script_class):
        """Back end for scriptharness.set_script_class().
        """
        self.script_class = script_class

MANAGER = ScriptManager()


# API functions {{{1
# These intentionally break the Don't-Repeat-Yourself rule in the docs +
# args/kwargs.  Specifying these as *args and **kwargs and being more vague
# in the documentation would be cleaner from a coding perspective, and more
# difficult from a "how do I use this?" discovery perspective.
def get_script(name="root", *args, **kwargs):
    """This will retrieve an existing script or create one and return it.

    Args:
      name (str, optional):  The name of the script to retrieve/create.
        Defaults to "root".

      *args: args to pass to MANAGER.get_script(); these will be passed to
        Script.__init__()

      **kwargs: kwargs to pass to MANAGER.get_script(); these will be passed
        to Script.__init__()

    Returns:
      The script instance.
    """
    return MANAGER.get_script(name=name, *args, **kwargs)

def get_config(name="root"):
    """This will return the config from an existing script.

    Args:
      name (str, optional):  The name of the script to retrieve/create.
        Defaults to "root".

    Raises:
      scriptharness.exceptions.ScriptHarnessException, if there is no script
        of name `name`.

    Returns:
      config (dict): By default scriptharness.structures.LoggingDict
    """
    return MANAGER.get_config(name=name)

def set_action_class(action_class):
    """By default new actions use the scriptharness.actions.Action class.
     Override here.

    Args:
      action_class (class): use this class for new actions.
    """
    return MANAGER.set_action_class(action_class)

def set_script_class(script_class):
    """By default new scripts use the scriptharness.script.Script class.
    Override here.

    Args:
      script_class (class): use this class for new scripts.
    """
    return MANAGER.set_script_class(script_class)
