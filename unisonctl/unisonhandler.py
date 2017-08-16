#!/usr/bin/env python3

# Unison control script
#
# This script handles the file-based data storage
#

# TODO: Replace DEBUG var with an actual logging framework, including log levels

import subprocess
import json
import os
import glob
import atexit
from datastorage import DataStorage

class UnisonHandler():

    # Object for data storage backend
    data_storage = None

    # configuration values
    config = {}

    # Enables extra output
    DEBUG = True
    # DEBUG = False

    def __init__(self):
        """
        Imports configuration and running script data.

        Paramaters :
            none

        Throws :
            none

        Returns :
            null
        """

        # Register exit handler
        atexit.register(self.exit_handler)

        # Set up configuration
        self.import_config()

        # Set up data storage backend
        self.data_storage = DataStorage(self.DEBUG, self.config)

        # self.data_storage.set_data("key1", {'filekey1':'file value data, yoooooo'})
        data = self.data_storage.get_data("key1")



    def import_config(self):
        """
        Handles config setup and importing, also contains sane defaults
        which are used if there's no given config option set.

        TODO: Implement command line config options here?

        Paramaters :
            none

        Throws :
            'LookupError' exception raised if config is invalid.

        Returns :
            null
        """

        # Get the config file
        import config

        # Get all keys from keyvalue pairs in the config file
        settingsFromConfigFile = [x for x in dir(config) if not x.startswith('__')]

        # Settings validation: specify keys which are valid settings
        # If there are rows in the config file which are not listed here, an error
        # will be raised
        validSettings = {
            'unison_config_template_dir',
            'unison_config_dir',
            'data_dir',
            'log_file',
            'make_root_directories_if_not_found',
            'sync_hierarchy_rules'
        }


        # If a setting contains a directory path, add it's key here and it will be
        # sanatized (whitespace and trailing whitespaces stripped)
        settingPathsToSanitize = {
            'unison_config_template_dir',
            'unison_config_dir',
            'data_dir',
        }


        # Values here are used as config values unless overridden in the config.py file
        defaultSettings = {
            'data_dir':'/var/run/unisonctld',
            'log_file':'/dev/null',
            'make_root_directories_if_not_found':True,
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

        self.config['json_data_dir'] = self.config['data_dir'] + os.sep + "running-unison-data"


        # If you reach here, configuration was read without error.
        return;

    def sanatize_path(self, path):
        """
        Used internally to sanatize directory paths to remove whitespace, as well
        as trailing slashes. Currently only supports unix slashes.

        Paramaters :
            1) directory path to sanatize

        Throws :
            none

        Returns :
            Sanatized directory path

        Doctests :
        >>> US = UnisonHandler()

        >>> US.sanatize_path(" /extra/whitespace ")
        '/extra/whitespace'

        >>> US.sanatize_path("/dir/with/trailing/slash/")
        '/dir/with/trailing/slash'

        >>> US.sanatize_path("  /dir/with/trailing/slash/and/whitepace/   ")
        '/dir/with/trailing/slash/and/whitepace'

        >>> US.sanatize_path("  /dir/with/trailing/slashes////   ")
        '/dir/with/trailing/slashes'

        """

        # Remove extra whitespace
        path = path.strip()

        # Remove slash from end of path
        path = path.rstrip(os.sep)

        return path;

    def exit_handler(self):
        """
        This function is called on exit automatically

        Paramaters :
            none

        Throws :
            none

        Returns :
            null
        """
        if(self.DEBUG):
            print("Starting script shutdown in the class " + self.__class__.__name__);

        # self.write_running_data()

        if(self.DEBUG):
            print("Script shutdown complete in class " + self.__class__.__name__);


# tmp : make this more robust
US = UnisonHandler()
