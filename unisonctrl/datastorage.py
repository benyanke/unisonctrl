#!/usr/bin/env python3

# This script handles the file-based data storage, acting as a backend for the
# other parts of the script

# TODO: Replace DEBUG var with an actual logging framework, including log levels

# import subprocess
import json
import os
import glob
import atexit

class DataStorage():

    # data associated with each running unison instance
    running_data = {}

    # configuration values
    config = {}

    # Enables extra output
    DEBUG = False

    def __init__(self, debug, config):
        """
        Imports configuration and running script data.

        Paramaters :
            none

        Throws :
            none

        Returns :
            null
        """

        # Pass along parent's debug status
        self.DEBUG = debug

        # Import config from parent
        self.config = config

        # Register exit handler
        atexit.register(self.exit_handler)

        # Get data associated with running unison instances
        self.import_file_data()

    def get_data(self,key):
        """
        A getter method for the data

        Paramaters :
            key of the data to get

        Throws :
            none

        Returns :
            requested data (or null, if not existing)
        """
        # Note: this might not be accurate if multiple processes are
        # reading/writing the data

        # If the key exists in the array, return the data
        if key in self.running_data:
            return self.running_data[key]

    def set_data(self,key,data):
        """
        A setter method for the data.

        Paramaters :
            key of the data to get, value to set

        Throws :
            none

        Returns :
            requested data (or null, if not existing)
        """

        # Store the data to the array
        self.running_data[key] = data

        # Also store back to files, for data persistence
        self.write_running_data

    def import_file_data(self):
        """
        Parses the filesystem location specified in config option 'data_dir'
        and loads information about each running unison instance in to the
        'self.import_file_data' attribute.

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
        if  (not os.path.exists(self.config['data_dir'])) and (self.config['make_root_directories_if_not_found']):
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

        if(self.DEBUG):
            print("It appears the file data was successfully imported");

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
        >>> DS = DataStorage()

        >>> DS.get_filename_from_path("/extra/whitespace/filename")
        'filename'

        >>> DS.get_filename_from_path("/extra/whitespace/filename.json")
        'filename.json'

        >>> DS.get_filename_from_path("/fileAtRoot.ini")
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
            print("Writing data to files now")


        # Looping through self.running_data to write each entry to it's own file
        for key in self.running_data:

            if(self.DEBUG):
                print("Writing to " + key + ".json: " + str(json.dumps(self.running_data[key])))

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
            print("Starting script shutdown in the class " + self.__class__.__name__);

        self.write_running_data()

        if(self.DEBUG):
            print("Script shutdown complete in class " + self.__class__.__name__);
