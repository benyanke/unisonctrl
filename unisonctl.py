#!/usr/bin/env python3

# Unison control script
#
# This script controls multiple unison instances to better handle syncing a large
# dataset
#

# TODO: Replace DEBUG var with an actual logging framework, including log levels

import subprocess
import json
import os
import glob
import atexit

class UnisonCtl():

    # data associated with each running unison instance
    running_data = {}

    # configuration values
    config = {}

    # Enables extra output
    DEBUG = True

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

        # Process configuration details
        self.import_config()

        # Get data associated with running unison instances
        self.import_running_data()

        # Debug line
        if(self.DEBUG):
            print(self.running_data);


    def import_running_data(self):
        """
        Parses the filesystem location specified in config option 'data_dir'
        and loads information about each running unison instance in to the
        'self.import_running_data' attribute.

        TODO: TESTME

        Paramaters :
            none

        Throws :
            'IOError' exception raised if directories could not be read or created

        Returns :
            null
        """

        # Ensure permissions are properly set before continuing
        self.check_data_dir_permissions()

        # Make dir for pid files, if config allows it
        if  (not os.path.exists(self.config['data_dir'])) and (config['make_root_directories_if_not_found']):
            os.makedirs(self.config['data_dir'])

        # If directory doesn't exist and config doesn't allow new ones to be
        # created, throw exception
        elif (not os.path.exists(self.config['data_dir'])):
            raise IOError(
            "The directory '" + self.config['data_dir'] + "' does not " +
            "and auto-creation is disabled");

        # Make directory for json files
        if not os.path.exists(self.config['json_data_dir']):
            os.makedirs(self.config['json_data_dir'])

        # Get files by extension
        json_data_files = glob.glob(self.config['json_data_dir'] + os.sep + "*.json")

        if(self.DEBUG):
            all_data_files = glob.glob(self.config['json_data_dir'] + os.sep + "*")
            extra_files = list(set(all_data_files)-set(json_data_files))

            if len(extra_files) > 0:
                print("There are unrecognized files in '" + self.config['json_data_dir'] + ":\n    * " + "\n    * ".join(extra_files) + "\n\n");


        # Calculates the list of uncategorized_files
        all_files = glob.glob(self.config['data_dir'] + "/*")
        uncategorized_files = list(set(all_files)-set(json_data_files))

        # Loop through json files and import their content into self.running_data
        for json_data_filename in json_data_files:
            if(self.DEBUG):
                print(json_data_filename);

            content = self.file_get_contents(json_data_filename)

            # Check for valid json. If so, import it
            try:
                # Get the filename to use as the key
                key = self.get_filename_from_path(json_data_filename)

                # remove ".json" from the end
                key = key[:-5]

                self.running_data[key] = json.loads(content)
            except ValueError:
                # TODO: Add logging here
                if(self.DEBUG):
                    print("Warning: corrupted json data")
                raise ValueError("Datafile '" + json_data_filename + "' contained invalid json")

        return

    def check_data_dir_permissions(self):
        """
        Checks the directory specified in 'data_dir' to ensure it there are
        sufficient permissions to write, edit, and delete files within this dir.

        TODO: TESTME

        Paramaters :
            none

        Throws :
            'IOError' exception raised if directory could not be found

        Returns :
            true  - if permissions were correct or could be corrected
            false - if permissions were incorrect and could not be corrected
        """

        # raise IOError("The directory '" + self.config['data_dir'] + "' does not exist")

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
        >>> UC = UnisonCtl()

        >>> UC.sanatize_path(" /extra/whitespace ")
        '/extra/whitespace'

        >>> UC.sanatize_path("/dir/with/trailing/slash/")
        '/dir/with/trailing/slash'

        >>> UC.sanatize_path("  /dir/with/trailing/slash/and/whitepace/   ")
        '/dir/with/trailing/slash/and/whitepace'

        >>> UC.sanatize_path("  /dir/with/trailing/slashes////   ")
        '/dir/with/trailing/slashes'

        """

        # Remove extra whitespace
        path = path.strip()

        # Remove slash from end of path
        path = path.rstrip(os.sep)

        return path;

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
            'make_root_directories_if_not_found'
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

    def file_get_contents(self, filename):
        """
        Small helper function to read a file and returns it's contents

        TODO: TESTME

        Paramaters :
            none

        Throws :
            none

        Returns :
            file content
        """
        with open(filename) as f:
            return f.read()

    # TODO: Implement me
    def file_put_contents(self, filename, filecontent):
        """
        Small helper function to write a file

        TODO: TESTME

        Paramaters :
            none

        Throws :
            none

        Returns :
            file content
        """

        # Open file descriptor
        f = open(filename,"w")

        # Write to file
        f.write(filecontent)

        # Close file descriptor
        f.close()

        return

    def get_filename_from_path(self, filepath):
        """
        Small helper function to find a filename from a filepath

        TODO: TESTME

        Paramaters :
            none

        Throws :
            none

        Returns :
            file content

        Doctests :
        >>> UC = UnisonCtl()

        >>> UC.get_filename_from_path("/extra/whitespace/filename")
        'filename'

        >>> UC.get_filename_from_path("/extra/whitespace/filename.json")
        'filename.json'

        >>> UC.get_filename_from_path("/fileAtRoot.ini")
        'fileAtRoot.ini'

        """
        return os.path.basename(filepath)

    def write_running_data(self):
        """
        This function writes the contents of self.running_data to json files in
        config['data_dir'].

        Paramaters :
            none

        Throws :
            none

        Returns :
            null
        """
        if(self.DEBUG):
            print("Writing data to files")

        if(self.DEBUG):
            print(self.running_data)

        # Looping through self.running_data to write each entry to it's own file
        for key in self.running_data:
            self.file_put_contents(self.config['json_data_dir']  + os.sep + key + ".json", json.dumps(self.running_data[key]))

            if(self.DEBUG):
                print("Writing " + key + ".json data file")

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
            print("Starting script shutdown");

        self.write_running_data()

        if(self.DEBUG):
            print("Script shutdown complete");

    def start(self):
        print("tmp")

# tmp : make this more robust
uc = UnisonCtl()
uc.start()
