#!/usr/bin/env python3

# Unison control script
#
# This script handles the file-based data storage
#

# TODO: Replace DEBUG var with an actual logging framework, including log level
# TODO: turn from hardcoded program into a command line utility

import subprocess
import os
import glob
import atexit
import itertools
import hashlib
# import time
import psutil
# import signal
import platform
import copy

# For debugging
# import shlex

from datastorage import DataStorage


class UnisonHandler():
    """Starts, stops and monitors unison instances."""

    # Object for data storage backend
    data_storage = None

    # configuration values
    config = {}

    # Enables extra output
    DEBUG = True

    # self.config['unisonctrl_log_dir'] + os.sep + "unisonctrl.log"
    # self.config['unisonctrl_log_dir'] + os.sep + "unisonctrl.error"

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
        # Handle manual debug setting
        self.DEBUG = debug

        # Set up configuration
        self.import_config()

        # Register exit handler
        atexit.register(self.exit_handler)

        # Set up data storage backend

        # Disabling debugging on the storage layer, it's no longer needed
        self.data_storage = DataStorage(False, self.config)

        if(self.DEBUG):
            print("Constructor complete")

        self.cleanup_dead_processes()

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

    def create_all_sync_instances(self):
        """Create multiple sync instances from the config and filesystem info.

        Parameters
        ----------
        none

        Returns
        -------
        list
            PIDs of dead unison instances which we thought were running.

        Throws
        -------
        none

        """
        # Get directories to sync
        dirs_to_sync_by_sync_instance = self.get_dirs_to_sync(self.config['sync_hierarchy_rules'])

        # Store all known running sync instances here to potentially kill later
        # unhandled_sync_instances = copy.deepcopy(dirs_to_sync_by_sync_instance)
        unhandled_sync_instances = copy.deepcopy(self.data_storage.running_data)

        # print("######## To maybe kill: ")
        # print(unhandled_sync_instances)

        # Loop through each entry in the dict and create a sync instance for it
        for instance_name, dirs_to_sync in dirs_to_sync_by_sync_instance.items():

            # Mark this instance as handled so it's not killed later
            unhandled_sync_instances.pop(instance_name, None)

            # print("######## Not neededing to kill:")
            # print(instance_name)

            # Make new sync instance
            self.create_sync_instance(instance_name, dirs_to_sync)

        # print("######## To kill: ")
        # print(unhandled_sync_instances)

        # Kill any instances in unhandled_sync_instances, because they are
        # no longer required needed
        for inst_to_kill in unhandled_sync_instances:
            self.kill_sync_instance_by_pid(self.data_storage.running_data[inst_to_kill]['pid'])

    def get_dirs_to_sync(self, sync_hierarchy_rules):
        """Start a new sync instance with provided details.

        # Parses the filesystem, and lists l

        Parameters
        ----------
        Pass through sync_hierarchy_rules from config

        Returns
        -------
        dict (nested)
            [syncname] - name of the sync name for this batch
                ['sync'] - directories to sync in this instance
                ['ignore'] - directories to ignore in this instance

        Throws
        -------
        none

        """
        # contains the list of directories which have been handled by the loop
        # so future iterations don't duplicate work
        handled_dirs = []

        # Contains list which is built up within the loop and returned at the
        # end of the method
        all_dirs_to_sync = {}

        for sync_instance in sync_hierarchy_rules:

            # Find full list
            expr = (
                self.config['unison_local_root'] +
                os.sep +
                sync_instance['dir_selector']
            )

            # Get full list of glob directories
            all_dirs_from_glob = glob.glob(self.sanatize_path(expr))

            # Remove any dirs already handled in a previous loop, unless
            # overlap is set
            if (
                'overlap' not in sync_instance or
                sync_instance['overlap'] is False
            ):
                if(self.DEBUG):
                    print("NO OVERLAP ALLOWED")
                before = len(all_dirs_from_glob)
                all_unhandled_dirs_from_glob = [x for x in all_dirs_from_glob if x not in handled_dirs]
                after = len(all_unhandled_dirs_from_glob)

                if(self.DEBUG and before != after):
                    print(str(before) + " down to " + str(after) + " by removing already handled dirs")

            # By default, use 'name_highfirst'
            if 'sort_method' not in sync_instance:
                sync_instance['sort_method'] = 'name_highfirst'

            # Apply sort
            if sync_instance['sort_method'] == 'name_highfirst':
                sorted_dirs = sorted(all_unhandled_dirs_from_glob, reverse=True)
            elif sync_instance['sort_method'] == 'name_lowfirst':
                sorted_dirs = sorted(all_unhandled_dirs_from_glob)
            # Add other sort implementations here
            else:
                raise ValueError(
                    sync_instance['sort_method'] +
                    " is not a valid sort method on sync instance " +
                    sync_instance['syncname']
                )

            # Apply sort_count_offet
            if 'sort_count_offet' in sync_instance:
                if(self.DEBUG):
                    print("OFFSET SET FOR " + sync_instance['syncname'])
                del sorted_dirs[:sync_instance['sort_count_offet']]

            # Apply sort_count
            if 'sort_count' in sync_instance:
                if(self.DEBUG):
                    print("COUNT SET FOR " + sync_instance['syncname'])
                dirs_to_sync = list(itertools.islice(sorted_dirs, 0, sync_instance['sort_count'], 1))
            else:
                dirs_to_sync = sorted_dirs

            # Add all these directories to the handled_dirs so they aren't
            # duplicated later
            handled_dirs += dirs_to_sync

            # add dirs to final output nested dict
            if len(dirs_to_sync) > 0:
                all_dirs_to_sync[sync_instance['syncname']] = dirs_to_sync

            if(self.DEBUG):
                dirstr = "\n   ".join(dirs_to_sync)
                print(
                    sync_instance['syncname'] +
                    " directories :\n   " +
                    dirstr + "\n\n"
                )

        if(self.DEBUG):
            print("All directories synced :\n   " + "\n   ".join(handled_dirs))

        return all_dirs_to_sync

    def create_sync_instance(self, instance_name, dirs_to_sync):
        """Start a new sync instance with provided details, if not already there.

        Parameters
        ----------
        dict
            List of directories to sync with each instance. The key of the dict
            becomes the name of the sync instance. The value of the dict
            becomes the list of directories to sync with that instance.

        Returns
        -------
        list
            PIDs of dead unison instances which we thought were running.

        Throws
        -------
        none

        """
        # Obtain a hash of the requested config to be able to later check if
        # the instance should be killed and restarted or not
        config_hash = hashlib.sha256((str(instance_name) + str(dirs_to_sync)).encode('utf-8')).hexdigest()

        # Get data from requested instance, if there is any
        requested_instance = self.data_storage.get_data(instance_name)

        if requested_instance is None:
            # No instance data found, must start new one
            if(self.DEBUG):
                print("No instance data found for " + instance_name + ", must start new one")
        elif requested_instance['config_hash'] == config_hash:
            # Existing instance data found, still uses same config - no restart
            if(self.DEBUG):
                print("Instance data found for " + instance_name + " - still using same config, no need to restart")
            return
        else:
            # Existing instance data found, but uses different config, so restarting
            if(self.DEBUG):
                print("Instance data found for " + instance_name + " - using different config, killing and restarting")

            self.kill_sync_instance_by_pid(requested_instance['pid'])
            self.data_storage.remove_data(requested_instance['syncname'])

        # Process dirs into a format for unison command line arguments
        dirs_for_unison = []
        trimmed_dirs = []
        amount_to_clip = (len(self.config['unison_local_root']) + 1)

        for dir in dirs_to_sync:

            # Clip off directory from local root
            dir_trimmed = dir[amount_to_clip:]

            # Format for unison command line args
            pathstr = "-path='" + dir_trimmed + "'"

            # Append to list for args
            dirs_for_unison.append(pathstr)

            # Append to list for config storage
            trimmed_dirs.append(dir_trimmed)

        # Basic verification check (by no means complete)

        # Ensure local root exists
        if not os.path.isdir(self.config['unison_local_root']):
            raise IOError("Local root directory does not exist")

        # Convert SSH config info into connection string
        remote_path_connection_string = (
            "" +
            "ssh://" +
            str(self.config['unison_remote_ssh_conn']) +
            "/" +
            str(self.config['unison_remote_root']) +
            ""
        )

        print(remote_path_connection_string)

        # Check if SSH config key is specified
        if self.config['unison_remote_ssh_keyfile'] == "":
            # Key is not specified, use it
            if self.DEBUG:
                print("Key not specified")

        else:
            # Key is specified
            if self.DEBUG:
                print("Key specified: " + self.config['unison_remote_ssh_keyfile'])

            remote_path_connection_string = (
                remote_path_connection_string +
                " -sshargs='-i " +
                self.config['unison_remote_ssh_keyfile'] +
                "'"
            )

        print(remote_path_connection_string)

        # Start unison
        cmd = (
            [self.config['unison_path']] +
            ["" + str(self.config['unison_local_root']) + ""] +
            [remote_path_connection_string] +
            dirs_for_unison + self.config['global_unison_config_options']
        )

        print(cmd)

        print(" ".join(cmd))

        print(self.config['unison_home_dir'])

        mainlog = self.config['unison_log_dir'] + os.sep + instance_name + ".log"
        errorlog = self.config['unison_log_dir'] + os.sep + instance_name + ".error"

        with open(mainlog, "wb") as out, open(errorlog, "wb") as err:
            running_instance_pid = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL, stdout=out, stderr=err,  # close_fds=True,
                env={
                    'UNISONLOCALHOSTNAME': self.config['unison_local_hostname'],
                    'HOME': self.config['unison_home_dir'],
                }
            ).pid

        print("PID: " + str(running_instance_pid) + " now running")
        # exit()

        instance_info = {
            "pid": running_instance_pid,
            "syncname": instance_name,
            "config_hash": config_hash,
            "dirs_to_sync": trimmed_dirs
        }

        print(self.data_storage.running_data)

        # Store instance info
        self.data_storage.set_data(instance_name, instance_info)

        print(self.data_storage.running_data)

    def kill_sync_instance_by_pid(self, pid):
        """Kill unison instance by it's PID.

        Includes build in protection for accidentally killing a non-unison
        program, and even other unison programs not started with this script

        Paramaters
        -------
        int
            pid to kill - must be a PID started in this process

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
        # Get the list of known pids to ensure we only kill one of those
        running_data = self.data_storage.running_data

        if(self.DEBUG):
            print("Attempting to kill PID " + str(pid))

        known_pids = []

        # Gets PIDs of all the known unison processes
        known_pids = [int(running_data[d]['pid']) for d in running_data]

        # TODO: Rewrite this function, it can probably be done with reduce()
        # RESOLUTION: Rewritten above, this kept in case it doesn't work
        # for entry in running_data:
        #    running_data[entry]
        #    known_pids.append(int(running_data[entry]['pid']))

        # TODO: Finish this error checking logic here, currently it doesn't check the PID

        # Try and kill with sigint (same as ctrl+c), if we are allowed to

        # First make sure the process exists
        if not psutil.pid_exists(pid):
            return

        # Then make sure it's a process we started
        elif pid not in known_pids:
            msg = "Process " + str(pid) + " is not managed by UnisonCTRL - refusing to kill"
            raise RuntimeError(msg)

        # Finally, kill the process if it exists and we started it
        else:
            return self.kill_pid(pid)

    def kill_pid(self, pid):
        """Kill a process by it's PID.

        Starts with SIGINT (ctrl + c), then waits 6 seconds, checking
        every 1/3 second. If it doesn't die after 6 seconds, it is
        attempted to be killed with psutil.terminate, then psutil.kill.

        Parameters
        ----------
        int
            PID of a process to kill

        Returns
        -------
        list[int]
            PIDs of unison instances, empty list

        Throws
        -------
        none

        """
        # Ensure it still exists before continuing
        if not psutil.pid_exists(pid):
            return

        # If it did not die nicely, get stronger about killing it
        p = psutil.Process(pid)

        # Try terminating, wait 3 seconds to see if it dies
        p.terminate()  # SIGTERM
        psutil.wait_procs([p], timeout=3)

        # Ensure it still exists before continuing
        if not psutil.pid_exists(pid):
            return

        # Try hard killing, wait 3 seconds to see if it dies
        p.kill()  # SIGKILL
        psutil.wait_procs([p], timeout=3)

        return

    def cleanup_dead_processes(self):
        """Ensure all expected processes are still running.

        Checks the running_data list against the current PID list to ensure
        all expected processes are still running.

        Parameters
        ----------
        none

        Returns
        -------
        list
            PIDs of dead unison instances which we thought were running.

        Throws
        -------
        none

        """
        # Get the list of processes we know are running and we think are running
        # Also, convert each PID to int to make sure we can compare
        actually_running_processes = self.get_running_unison_processes()
        l = self.data_storage.running_data
        supposedly_running_processes = [int(l[d]['pid']) for d in l]

        # Find which instances we think are running but aren't
        dead_instances = [x for x in supposedly_running_processes if x not in actually_running_processes]

        if(self.DEBUG):
            print("supposedly_running:")
            print(supposedly_running_processes)
            print("\n\nactually_running_processes:")
            print(actually_running_processes)

            print("\n\ndead_instances:")
            print(dead_instances)

        # Remove data on dead instances
        for instance_id in dead_instances:
            process = self.get_process_info_by_pid(instance_id)

            if(self.DEBUG):
                print(
                    "Removing, because it's dead: " +
                    str(process['syncname'])
                )
            self.data_storage.remove_data(process['syncname'])

    def get_process_info_by_pid(self, pid):
        """Return the syncname of a process given it's PID.

        Parameters
        ----------
        int
            PID of desired process


        Returns
        -------
        dict
            the full details of the sync process specified by the PID

        Throws
        -------
        none

        """
        for process in self.data_storage.running_data:
            if self.data_storage.running_data[process]['pid'] == pid:
                return self.data_storage.running_data[process]

    def get_running_unison_processes(self):
        """Return PIDs of currently running unison instances.

        Parameters
        ----------
        none


        Returns
        -------
        list[int]
            PIDs of unison instances, empty list

        Throws
        -------
        none

        """
        # Get PIDs
        # Note: throws exception if no instances exist
        try:
            pids = str(subprocess.check_output(["pidof", '/usr/bin/unison']))

            # Parse command output into list by removing junk chars and exploding
            # string with space delimiter
            pids = pids[2:-3].split(' ')

        except subprocess.CalledProcessError:
            # If error caught here, no unison instances are found running
            pids = []

        if self.DEBUG:
            print("Found " + str(len(pids)) + " running instances on this system: " + str(pids))

        # Return, after converting to ints
        return list(map(int, pids))

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

        # Convert config file into dict
        for key in settingsFromConfigFile:
            value = getattr(config, key)
            self.config[key] = value

        # Settings validation: specify keys which are valid settings
        # If there are rows in the config file which are not listed here, an
        # error will be raised
        validSettings = {
            'data_dir',
            'running_data_dir',
            'unison_log_dir',
            'unisonctrl_log_dir',
            'log_file',
            'make_root_directories_if_not_found',
            'sync_hierarchy_rules',
            'unison_local_root',
            'unison_remote_root',
            'unison_path',
            'global_unison_config_options',
            'unison_remote_ssh_conn',
            'unison_remote_ssh_keyfile',
            'unison_local_hostname',
            'unison_home_dir',
        }

        # If a setting contains a directory path, add it's key here and it will
        # be sanatized (whitespace and trailing whitespaces stripped)
        settingPathsToSanitize = {
            'data_dir',
            'unison_home_dir',
            'running_data_dir',
            'unison_log_dir',
            'unisonctrl_log_dir',
        }

        # Values here are used as config values unless overridden in the
        # config.py file
        defaultSettings = {
            'data_dir': '/tmp/unisonctrl',
            'log_file': '/dev/null',
            'make_root_directories_if_not_found': True,
            'unison_path': '/usr/bin/unison',  # Default ubuntu path for unison
            'unison_remote_ssh_keyfile': "",
            'unison_local_hostname': platform.node(),
            'running_data_dir': self.config['data_dir'] + os.sep + "running-sync-instance-information",
            'unison_log_dir': self.config['data_dir'] + os.sep + "unison-logs",
            'unisonctrl_log_dir': self.config['data_dir'] + os.sep + "unisonctrl-logs",

        }

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

        # If you reach here, configuration was read and imported without error
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

        # Clean up dead processes
        self.cleanup_dead_processes()

        if(self.DEBUG):
            print(
                "Script shutdown complete in class " +
                self.__class__.__name__
            )


# tmp : make this more robust
US = UnisonHandler(True)
# US = UnisonHandler(False)

# US.kill_sync_instance_by_pid(11701)

US.create_all_sync_instances()
