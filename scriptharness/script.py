#!/usr/bin/env python
"""Modular actions.

Attributes:
  LOGGER_NAME (str): logging.Logger name to use
  STRINGS (dict): strings for actions.  In the future these may be in a
    function to allow for localization.
  STATUSES (dict): constants to use for action statuses
  VALID_LISTENER_TIMING (tuple): valid timing for Script.add_listener()
"""
from __future__ import absolute_import, division, print_function, \
                       unicode_literals
import argparse
from copy import deepcopy
import logging
import os
from scriptharness import ScriptHarnessError, ScriptHarnessException, \
                          ScriptHarnessFatal
import scriptharness.config as shconfig
from scriptharness.structures import iterate_pairs, LoggingDict
import sys
import time


LOGGER_NAME = "scriptharness.script"
STRINGS = {
    "action": {
        "run_message": "Running action %(name)s",
        "skip_message": "Skipping action %(name)s",
        "error_message": "Action %(name)s error!",
        "fatal_message": "Fatal %(name)s exception: %(exc_info)s",
        "success_message": "Action %(name)s: finished successfully",
    }
}
STATUSES = {
    'success': 0,
    'error': 1,
    'fatal': -1,
}
VALID_LISTENER_TIMING = (
    "pre_run",
    "post_run",
    "pre_action",
    "post_action",
    "post_fatal",
)

# Action {{{1
class Action(object):
    """Action object.

    Attributes:
      name (str): action name for logging
      enabled (bool): skip if not enabled
      strings (dict): strings for log messages
      logger_name (str): logger name
      function (function): function to call
      history (dict): history of the action (return_value, status, timestamps)
    """

    def __init__(self, name, function=None, enabled=False):
        self.name = name
        self.enabled = enabled
        self.strings = deepcopy(STRINGS['action'])
        self.logger_name = "scriptharness.script.%s" % self.name
        self.history = {'timestamps': {}}
        self.function = function or \
                        globals().get(self.name.replace('-', '_'))
        if not callable(self.function):
            raise ScriptHarnessException(
                "No callable function for action %s!" % name
            )

    def run_function(self, config):
        """Run self.function.  Called from run() for subclassing purposes.

        Args:
          config (data structure): the config from the calling Script
            (passed from run()).
        """
        self.history['return_value'] = self.function(config)

    def run(self, config):
        """Run the action.

        Args:
          config (data structure): the config from the calling Script.
        """
        self.history['timestamps']['start_time'] = time.time()
        logger = logging.getLogger(self.logger_name)
        try:
            self.history['return_value'] = self.run_function(config)
        except ScriptHarnessError as exc_info:
            self.history['status'] = STATUSES['error']
            logger.error(self.strings['error_message'], {"name": self.name})
        except ScriptHarnessFatal as exc_info:
            self.history['status'] = STATUSES['fatal']
            logger.critical(self.strings['fatal_message'], {
                "name": self.name,
                "exc_info": exc_info,
            })
            raise
        else:
            self.history['status'] = STATUSES['success']
            logger.info(self.strings['success_message'], {"name": self.name})
        self.history['timestamps']['end_time'] = time.time()
        return self.history['status']


# Helper functions {{{1
def get_action_parser(all_actions):
    """Create an action option parser from the action list.

    Actions to run are specified as the argparse.REMAINDER options.

    Args:
      all_actions (list): a list of all possible Action objects for the script
      **kwargs: additional kwargs for ArgumentParser

    Returns:
      ArgumentParser with action options
    """
    parser = argparse.ArgumentParser(add_help=False)
    message = []
    for name, enabled in iterate_pairs(all_actions):
        string = "  "
        if enabled:
            string = "* "
        string += name
        message.append(string)
    def list_actions():
        """Helper function to list all actions (enabled shown with a '*')"""
        print(os.linesep.join(message))
        sys.exit(0)
    parser.add_argument(
        "--list-actions", action='store_const', const=list_actions,
        help="List all actions (default prepended with '*') and exit."
    )
    parser.add_argument(
        "--actions", nargs='+', choices=all_actions.keys(), metavar="ACTION",
        help="Specify the actions to run."
    )
    return parser

def get_config_parser():
    """Create a config option parser.

    Args:
      kwargs: additional kwargs for ArgumentParser

    Returns:
      ArgumentParser with config options
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '--config-file', '--cfg', '-c', action='append', dest='config_files',
        metavar="CONFIG_FILE", help="Specify required config files/urls"
    )
    # TODO optional config files
    return parser


def get_parser(all_actions=None, parents=None, **kwargs):
    """Create a script option parser.

    Args:
      parents (list, optional): ArgumentParsers to set as parents of the parser
      **kwargs: additional kwargs for ArgumentParser

    Returns:
      ArgumentParser with config options
    """
    if parents is None:
        parents = []
        if all_actions:
            parents.append(get_action_parser(all_actions))
        parents.append(get_config_parser())
    parser = argparse.ArgumentParser(parents=parents, **kwargs)
    # TODO populate
    return parser


def parse_args(parser, cmdln_args=None):
    """Build the parser and parse the commandline args.

    Args:
      parser (ArgumentParser): specify the parser to use
      initial_config (dict): specify a script-level config to set defaults
        post-parser defaults, but pre-config files and commandline args
      cmdln_args (optional): override the commandline args with these

    Returns:
      tuple(ArgumentParser, parsed_args, unknown_args)
    """
    cmdln_args = cmdln_args or []
    parsed_args, unknown_args = parser.parse_known_args(*cmdln_args)
    if hasattr(parsed_args, 'list_actions') and \
            callable(parsed_args.list_actions):
        parsed_args.list_actions()
    return (parser, parsed_args, unknown_args)


def get_actions(all_actions):
    """Build a tuple of Action objects for the script.

    Args:
      all_actions (data structure): ordered mapping of action_name:enabled
        bool, as accepted by iterate_pairs()

    Returns:
      tuple of Action objects
    """
    action_list = []
    for action_name, value in iterate_pairs(all_actions):
        action = Action(action_name, enabled=value)
        action_list.append(action)
    return tuple(action_list)

def get_actions_from_lists(all_actions, default_actions):
    """Helper method to generate the ordered mapping for get_actions().

    Args:
      all_actions (list): ordered list of all action names
      default_actions (list): list of all actions that are enabled by default

    Returns:
      tuple of Action objects
    """
    if not set(default_actions).issubset(set(all_actions)):
        raise ScriptHarnessException(
            "default_actions not a subset of all_actions!",
            default_actions, all_actions
        )
    action_list = []
    for action in all_actions:
        if action in default_actions:
            action_list.append((action, True))
        else:
            action_list.append((action, False))
    return get_actions(action_list)


# Script {{{1
class Script(object):
    """This maintains the context of the config + actions.

    In general there is a single Script object per run, but the intent is to
    allow for parallel processing by instantiating multiple Script objects when
    it makes sense.

    Attributes:
      config (LoggingDict): the config for the script
      strict (bool): In strict mode, warnings are fatal; config is read-only.
      actions (tuple): Action objects to run.
      listeners (dict): callbacks for run()
    """
    config = None

    def __init__(self, actions, parser, **kwargs):
        """Script.__init__

        Args:
          actions (tuple): Action objects to run.
          parser (ArgumentParser): parser to use
        """
        self.actions = actions
        self.listeners = {}
        for timing in VALID_LISTENER_TIMING:
            self.listeners.setdefault(timing, [])
        self.build_config(parser, **kwargs)
        # TODO dump config
        # TODO dump actions

    def __setattr__(self, name, *args):
        if name == 'config' and self.config:
            raise ScriptHarnessException(
                "Changing script config after config is already set!"
            )
        return super(Script, self).__setattr__(name, *args)

    def build_config(self, parser, cmdln_args=None, initial_config=None):
        """Create self.config from the parsed args.

        Args:
          parser (ArgumentParser): parser to use
          cmdln_args (tuple, optional): override the commandline args
          initial_config (dict, optional): initial config dict to apply

        Returns:
          parsed_args from parse_known_args()
        """
        cmdln_args = cmdln_args or []
        (parsed_args, unknown_args) = parser.parse_known_args(*cmdln_args)
        config = shconfig.build_config(parser, parsed_args, initial_config)
        # TODO parsed_args_defaults - config files - commandline args
        # differentiate argparse defaults from cmdln set? - parser.get_default(arg)
        if unknown_args:
            raise ScriptHarnessFatal(
                "Unknown arguments passed to script!", unknown_args
            )
        self.config = self.dict_to_config(config)
        self.enable_actions(parsed_args)

    @staticmethod
    def dict_to_config(config):
        """Here for subclassing.
        """
        return LoggingDict(config, logger_name=LOGGER_NAME)

    def enable_actions(self, parsed_args):
        """If parsed_args has 'actions' set, use those as the enabled actions.

        Args:
          parsed_args (argparse Namespace)
        """
        if hasattr(parsed_args, 'actions'):
            for action in self.actions:
                if action.name in parsed_args.actions:
                    action.enabled = True
                else:
                    action.enabled = False

    def add_listener(self, listener, timing, action_names=None):
        """Add a callback for specific script timing.

        For pre_ and post_run, run at the beginning and end of the script,
        respectively.

        For pre_ and post_action, run at the beginning and end of actions,
        respectively.  If action_names are specified, only run before/after
        those action(s).

        Args:
          listener (function): Function to call at the right time.
          timing (str): When to run the function.  Choices in
            VALID_LISTENER_TIMING.
          action_names (iterable): for pre/post action timing listeners,
            only run before/after these action(s).
        """
        if timing not in VALID_LISTENER_TIMING:
            raise ScriptHarnessException(
                "Invalid timing for add_listener!", listener.__qualname__,
                timing, action_names
            )
        if action_names and 'action' not in timing:
            raise ScriptHarnessException(
                "Only specify action_names for pre/post action timing!",
                listener.__qualname__, timing, action_names
            )
        logger = logging.getLogger(LOGGER_NAME)
        logger.debug("Adding listener to script: %s %s %s.",
                     listener.__qualname__, timing, action_names)
        self.listeners[timing].append((listener, action_names))

    def run(self):
        """Run all enabled actions.
        """
        # TODO listeners
        # TODO run actions with try/except for postfatal. send config as arg
        pass
