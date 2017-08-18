#!/usr/bin/env python3

# Unison control script
#
# This script handles the file-based data storage
#

# TODO: Replace DEBUG var with an actual logging framework, including log level

# import subprocess
from subprocess import check_output
# im002-psport json
import os
# import glob
import atexit
from datastorage import DataStorage


class UnisonHandler():
    """Starts, stops and monitors unison instances."""

    # Object for data storage backend
    data_storage = None

    # configuration values
    config = {}

    # Enables extra output
    DEBUG = True

    def __init__(self, debug=DEBUG):
        """Prepare UnisonHandler to manage unison instances.

        Parameters
        ----------
        none

        Returns
        -------
        null

        Throws
        -------
        none

        Doctests
        -------

        """
        # Register exit handler
        atexit.register(self.exit_handler)

        # Handle manual debug setting
        self.DEBUG = debug

        # Set up configuration
        self.import_config()

        # Set up data storage backend
        self.data_storage = DataStorage(self.DEBUG, self.config)

        if(self.DEBUG):
            print("Constructor complete")
    """

    # Algo required

    commands:

    unisonctrl status-not sure, maybe combine with list

    unisonctrl list-list currently running unison instances by reading pidfiles
    and perhaps:
        - confirming they're still running (pidcheck, simple)
        - confirming they're not stuck (logs? pid communicaton?)
        - when was last loop? (logs? wrapper script?)

    unisonctrl update-check directory structure and make sure rules don't need
    to be changed because of a change or

    unisonctrl restart-stop + start

    unisonctrl stop-stop all running unison instances, delete files in tmp dir

    unisonctrl start-recalculate directory structure and regenerate config
    files, restart unison instances


    other features not sure where to put:/public/img should work, and is not
    caught by .gitignore

        # Get the
     * check for unexpected dead processes and check logs
     * parse logs and send stats to webhook
     * calculate average sync latency

    """

    def get_running_unison_processes(self):
        """Return PIDs of currently running unison instances.

        Parameters
        ----------
        none

        Returns
        -------
        list
            PIDs of unison instances

        Throws
        -------
            'LookupError' if config is invalid.

        """
        # Get PIDs
        out = str(check_output(["pidof", 'unison']))

        # Parse command output into list
        out = out[2:-3].split(' ')

        # out = os.system("ps aux | grep \"unison\"")
        print(out)

        return None

    def import_config(self):
        """Import config from config, and apply details where needed.

        Parameters
        ----------
        none

        Returns
        -------
        null

        Throws
        -------
            'LookupError' if config is invalid.

        """
        # Get the config file
        import config

        # Get all keys from keyvalue pairs in the config file
        settingsFromConfigFile = [x for x in dir(config) if not x.startswith('__')]

        # Settings validation: specify keys which are valid settings
        # If there are rows in the config file which are not listed here, an
        # error will be raised
        validSettings = {
            'unison_config_template_dir',
            'unison_config_dir',
            'data_dir',
            'log_file',
            'make_root_directories_if_not_found',
            'sync_hierarchy_rules',
            'unison_local_root',
            'unison_remote_root',
            'unison_path',
        }

        # If a setting contains a directory path, add it's key here and it will
        # be sanatized (whitespace and trailing whitespaces stripped)
        settingPathsToSanitize = {
            'unison_config_template_dir',
            'unison_config_dir',
            'data_dir',
        }

        # Values here are used as config values unless overridden in the
        # config.py file
        defaultSettings = {
            'data_dir': '/var/run/unisonctrld',
            'log_file': '/dev/null',
            'make_root_directories_if_not_found': True,
            'unison_path': '/usr/bin/unison',  # Default ubuntu path for unison
        }

        # Convert config file into dict
        for key in settingsFromConfigFile:
            value = getattr(config, key)
            self.config[key] = value

        # Apply default settings to fill gaps between explicitly set ones
        for key in defaultSettings:
            if (key not in self.config):
                self.config[key] = defaultSettings[key].strip()

        # Ensure all required keys are specified
        for key in validSettings:
            if (key not in self.config):
                raise LookupError("Required config entry '" + key + "' not specified")

        # Ensure no additional keys are specified
        for key in self.config:
            if (key not in validSettings):
                raise LookupError("Unknown config entry: '" + key + "'")

        # Sanatize directory paths
        for key in settingPathsToSanitize:
            self.config[key] = self.sanatize_path(self.config[key])

        # A few hardcoded config values
        self.config['data_dir'] = self.config['data_dir'] + os.sep + "running-sync-instances"

        # If you reach here, configuration was read without error.
        return

    def sanatize_path(self, path):
        """Sanitize directory paths by removing whitespace and trailing slashes.

        Currently only tested on Unix, but should also work on Windows.
        TODO: Test on windows to ensure it works properly.

        Parameters
        ----------
        1) str
            directory path to sanatize

        Returns
        -------
        str
            sanatized directory path

        Throws
        -------
        none

        Doctests
        -------
        >>> US = UnisonHandler(False)

        >>> US.sanatize_path(" /extra/whitespace ")
        '/extra/whitespace'

        >>> US.sanatize_path("/dir/with/trailing/slash/")
        '/dir/with/trailing/slash'

        >>> US.sanatize_path("  /dir/with/trailing/slash/and/whitepace/   ")
        '/dir/with/trailing/slash/and/whitepace'

        >>> US.sanatize_path("  /dir/with/many/trailing/slashes////   ")
        '/dir/with/many/trailing/slashes'

        """
        # Remove extra whitespace
        path = path.strip()

        # Remove slash from end of path
        path = path.rstrip(os.sep)

        return path

    def exit_handler(self):
        """Is called on exit automatically.

        Paramaters
        -------
        none

        Throws
        -------
        none

        Returns
        -------
        none

        Throws
        -------
        none

        Doctests
        -------

        """
        if(self.DEBUG):
            print(
                "Starting script shutdown in the class " +
                self.__class__.__name__
            )

        self.data_storage.write_running_data()

        if(self.DEBUG):
            print(
                "Script shutdown complete in class " +
                self.__class__.__name__
            )


# tmp : make this more robust
US = UnisonHandler(True)
US.get_running_unison_processes()
