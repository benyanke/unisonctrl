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
import getpass
import platform
import copy

import logging
import logging.handlers

from datastorage import DataStorage


class UnisonHandler():
    """Starts, stops and monitors unison instances."""

    # Object for data storage backend
    data_storage = None

    # configuration values
    config = {}

    # Enables extra output
    INFO = True

    # Logging Object
    # logging

    # self.config['unisonctrl_log_dir'] + os.sep + "unisonctrl.log"
    # self.config['unisonctrl_log_dir'] + os.sep + "unisonctrl.error"

    def __init__(self):
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
        self.import_config()
        # Set up configuration

        # Register exit handler
        atexit.register(self.exit_handler)

        # Set up logging
        self.logger = logging.getLogger('unisonctrl')
        self.logger.setLevel(logging.INFO)

        # Set up main log file logging
        logFileFormatter = logging.Formatter(
            fmt='[%(asctime)-s] %(levelname)-9s : %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p'
        )

        # Size based log rotation
        if (self.config['rotate_logs'] == "size"):
            logfileHandler = logging.handlers.RotatingFileHandler(
                self.config['unisonctrl_log_dir'] + os.sep + 'unisonctrl.log',
                # maxBytes=50000000,  # 50mb
                maxBytes=5000,  # 50mb
                backupCount=20
            )

        # Timed log rotation
        elif (self.config['rotate_logs'] == "time"):
            logfileHandler = logging.handlers.TimedRotatingFileHandler(
                self.config['unisonctrl_log_dir'] + os.sep + 'unisonctrl.log',
                when="midnight",
                backupCount=14,  # Keep past 14 days
            )

        # No log rotation
        elif (self.config['rotate_logs'] == "off"):
            logfileHandler = logging.FileHandler()

        else:
            logfileHandler = logging.FileHandler()

        logfileHandler.setLevel(logging.DEBUG)
        logfileHandler.setFormatter(logFileFormatter)
        self.logger.addHandler(logfileHandler)

        # Send logs to console when running
        consoleFormatter = logging.Formatter('[%(asctime)-22s] %(levelname)s : %(message)s')
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.INFO)
        consoleHandler.setFormatter(consoleFormatter)
        self.logger.addHandler(consoleHandler)

        # Disabling debugging on the storage layer, it's no longer needed
        self.data_storage = DataStorage(False, self.config)

        self.logger.info("UnisonCTRL Starting")

        # Clean up dead processes to ensure data files are in an expected state
        self.cleanup_dead_processes()

    def run(self):
        """General wrapper to ensure running instances are up to date.

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
        self.create_all_sync_instances()

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

        # Loop through each entry in the dict and create a sync instance for it
        for instance_name, dirs_to_sync in dirs_to_sync_by_sync_instance.items():

            # Mark this instance as handled so it's not killed later
            unhandled_sync_instances.pop(instance_name, None)

            # Make new sync instance
            self.create_sync_instance(instance_name, dirs_to_sync)

        # Kill any instances in unhandled_sync_instances, because they are
        # no longer required needed

        for inst_to_kill in unhandled_sync_instances:
            self.logger.debug(
                "Cleaning up instance '" + inst_to_kill + "'" +
                " which is no longer needed."
            )
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
        # Contains the list of directories which have been handled by the loop
        # so future iterations don't duplicate work
        handled_dirs = []

        # Contains list which is built up within the loop and returned at the
        # end of the method
        all_dirs_to_sync = {}

        self.logger.debug(
            "Processing directories to sync. " +
            str(len(sync_hierarchy_rules)) + " rules to process."
        )

        for sync_instance in sync_hierarchy_rules:

            self.logger.debug(
                "Instance '" + sync_instance['syncname'] + "' " +
                "Parsing rules and directories."
            )

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

                self.logger.debug(
                    "Instance '" + sync_instance['syncname'] + "' " +
                    "Removing already handled directories."
                )

                before = len(all_dirs_from_glob)
                all_unhandled_dirs_from_glob = [x for x in all_dirs_from_glob if x not in handled_dirs]
                after = len(all_unhandled_dirs_from_glob)

                # Log event if the duplication handler remove directories
                # Added 'False and' to disable this section. TMI in the logs
                if(before != after):
                    self.logger.debug(
                        "Instance '" + sync_instance['syncname'] + "' " +
                        "Parse result: " + str(before) + " dirs down to " +
                        str(after) + " dirs by removing already handled dirs"
                    )

            # By default, use 'name_highfirst'
            if 'sort_method' not in sync_instance:
                sync_instance['sort_method'] = 'name_highfirst'

            # Apply sort
            if sync_instance['sort_method'] == 'name_highfirst':
                sorted_dirs = sorted(all_unhandled_dirs_from_glob, reverse=True)
            elif sync_instance['sort_method'] == 'name_lowfirst':
                sorted_dirs = sorted(all_unhandled_dirs_from_glob)
            # Add other sort implementations here later, if wanted
            else:

                # Message for exception and self.logger
                msg = (
                    "'" + sync_instance['sort_method'] + "'" +
                    " is not a valid sort method on sync instance " +
                    "'" + sync_instance['syncname'] + "'. " +
                    "Instance will not be created."
                )

                # Send message to self.logger
                self.logger.warn(msg)

                # Uncomment this to raise an exception instead of returning blank
                # raise ValueError(msg)

                # Return blank dir set, since sort was invalid
                return {}

            # Apply sort_count, if it's set
            if 'sort_count' in sync_instance:

                if (not isinstance(sync_instance['sort_count'], int)):
                    # if not int, throw warning
                    self.logger.warning(
                        "Instance '" + sync_instance['syncname'] + "' " +
                        "sort_count '" + str(sync_instance['sort_count']) + "'" +
                        " is not castable to int. Setting sort_count to a " +
                        "default of '3'."
                    )

                    # Then set a default
                    sync_instance['sort_count'] = 3

                else:
                    # If it's a valid int, use it
                    self.logger.debug(
                        "Instance '" + sync_instance['syncname'] + "' " +
                        "sort_count set at " + str(sync_instance['sort_count']) + "."
                    )

                dirs_to_sync = list(
                    itertools.islice(
                        sorted_dirs, 0, sync_instance['sort_count'], 1
                    )
                )

            else:
                # if sort_count is not set, sync all dirs
                dirs_to_sync = sorted_dirs

            # Add all these directories to the handled_dirs so they aren't
            # duplicated later
            handled_dirs += dirs_to_sync

            # add dirs to final output nested dict
            if len(dirs_to_sync) > 0:
                all_dirs_to_sync[sync_instance['syncname']] = dirs_to_sync

            self.logger.debug(
                "Instance '" + sync_instance['syncname'] + "' " +
                "Syncing " + str(len(dirs_to_sync)) + " directories."
            )

            # Shouldn't need this, except when in deep debugging
            # If you need it, turn it on
            if(False):
                dirstr = "\n   ".join(dirs_to_sync)
                print(
                    sync_instance['syncname'] +
                    " directories :\n   " +
                    dirstr + "\n\n"
                )

        self.logger.debug(
            "Sync rule parsing complete. " +
            "Syncing " + str(len(handled_dirs)) + " explicit directories " +
            "in all instances combined"
        )

        # Shouldn't need this, except when in deep debugging
        # If you need it, turn it on
        if(False):
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
        bool
            True if new instance was created
            False if no new instance was needed

        Throws
        -------
        none

        """
        # TODO: check global config hash here too, not just instance-specific config
        self.logger.debug(
            "Processing instance '" + instance_name + "' , deciding whether" +
            "to kill or not"
        )

        # Obtain a hash of the requested config to be able to later check if
        # the instance should be killed and restarted or not.
        # This hash will be stored with the instance data, and if it changes,
        # the instance will be killed and restarted so that new config can be
        # applied.
        config_hash = hashlib.sha256((

            # Include the instance name in the config hash
            str(instance_name) +

            # Include the directories to sync in the config hash
            str(dirs_to_sync) +

            # Include the global config in the config hash
            str(self.config['global_unison_config_options'])

        ).encode('utf-8')).hexdigest()

        # Get data from requested instance, if there is any
        requested_instance = self.data_storage.get_data(instance_name)

        if requested_instance is None:

            # No instance data found, must start new one
            self.logger.info(
                "Instance '" + instance_name + "' " +
                "No instance data found, starting new sync instance."
            )

        elif requested_instance['config_hash'] == config_hash:
            # Existing instance data found, still uses same config - no restart
            self.logger.debug(
                "Instance '" + instance_name + "' " +
                "Instance data found, config still unchanged."
            )
            return False
        else:
            # Existing instance data found, but uses different config, so restarting
            self.logger.info(
                "Instance '" + instance_name + "' " +
                "Instance data found, but config or directories to sync have" +
                " changed. Restarting instance."
            )

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
            pathstr = "-path=" + dir_trimmed + ""

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

        # todo: add '-label' here

        # print(remote_path_connection_string)

        # Check if SSH config key is specified
        if self.config['unison_remote_ssh_keyfile'] == "":
            # Key is not specified, don't use it
            # TODO: reformat this entry
            self.logger.debug("SSH key not specified")

        else:
            # Key is specified
            # TODO: reformat this entry
            self.logger.debug("Key specified: " + self.config['unison_remote_ssh_keyfile'])

            remote_path_connection_string = (
                remote_path_connection_string +
                " -sshargs='-i " +
                self.config['unison_remote_ssh_keyfile'] +
                "'"
            )

        # print(remote_path_connection_string)

        # Set env vars to pass to unison
        envvars = {
            'UNISONLOCALHOSTNAME': self.config['unison_local_hostname'],
            'HOME': self.config['unison_home_dir'],
            'USER': self.config['unison_user'],
            'LOGNAME': self.config['unison_user'],
            'PWD': self.config['unison_home_dir'],
        }

        logfile = self.config['unison_log_dir'] + os.sep + instance_name + ".log"
        self.touch(logfile)

        # Start unison
        cmd = (
            [self.config['unison_path']] +
            ["" + str(self.config['unison_local_root']) + ""] +
            [remote_path_connection_string] +
            ["-label=unisonctrl-" + instance_name] +
            dirs_for_unison +
            self.config['global_unison_config_options'] +
            ["-log=true"] +
            [
                "-logfile=" +
                logfile
            ]
        )

        # self.logger.info(" ".join(cmd))

        running_instance_pid = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,  # close_fds=True,
            env=envvars
        ).pid

        instance_info = {
            "pid": running_instance_pid,
            "syncname": instance_name,
            "config_hash": config_hash,
            "dirs_to_sync": trimmed_dirs
        }

        self.logger.info(
            "New instance '" + instance_name + "' " +
            " (PID " + str(instance_info['pid']) + ")."
        )

        # Store instance info
        self.data_storage.set_data(instance_name, instance_info)

        # New instance was created, return true
        return True

    def touch(self, fname, mode=0o644, dir_fd=None, **kwargs):
        """Python equuivilent for unix "touch".

        Paramaters
        -------
        str
            filename to touch

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
        flags = os.O_CREAT | os.O_APPEND
        with os.fdopen(os.open(fname, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
            os.utime(
                f.fileno() if os.utime in os.supports_fd else fname,
                dir_fd=None if os.supports_fd else dir_fd, **kwargs
            )
            with open(fname, 'a'):
                os.utime(fname, None)

    def kill_sync_instance_by_pid(self, pid):
        """Kill unison instance by it's PID.

        Includes built-in protection for accidentally killing a non-unison
        program, and even other unison programs not started with this script.
        This ensures that this function will never kill a PID that we have not
        started with unisonctrl.

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

        self.logger.debug(
            "Attempting to kill PID '" + str(pid) + "'"
        )

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
            self.logger.info(
                "PID " + str(pid) + " was not found. Perhaps already dead?"
            )
            return

        # Then make sure it's a process we started
        elif pid not in known_pids:

            shortmsg = (
                "PID #" + str(pid) + " is not managed by UnisonCTRL. " +
                "Refusing to kill.  See logs for more information."
            )

            longmsg = (
                "PID #" + str(pid) + " is not managed by UnisonCTRL. " +
                "Refusing to kill. Your data files are likely corrupted. " +
                "Kill all running unison instances on this system, " +
                "delete everything in '" + self.config['running_data_dir'] +
                "/*', and run UnisonCTRL again."
            )

            self.logger.critical(longmsg)

            raise RuntimeError(shortmsg)

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
        None

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
            self.logger.debug(
                "PID " + str(pid) + " was killed with SIGTERM successfully."
            )
            return

        # Try hard killing, wait 3 seconds to see if it dies
        p.kill()  # SIGKILL
        psutil.wait_procs([p], timeout=3)

        self.logger.info(
            "PID " + str(pid) + " could not be killed with SIGTERM, and " +
            "was killed with SIGKILL."
        )

        return

    def cleanup_dead_processes(self):
        """Ensure all expected processes are still running.

        Checks the running_data list against the current PID list to ensure
        all expected processes are still running. Note that if everything works
        as expected and does not crash, there should never be dead instances.

        As such, if dead instances appear on a regular basis, consider digging
        into *why* they are appearing.

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

        # Note: if nothing crashes, dead instances should never exist.
        if(len(dead_instances) > 0):
            self.logger.warn(
                "Found " + str(len(dead_instances)) + " unexpected dead " +
                "instances. Cleaning up data files now."
            )
        else:
            self.logger.debug(
                "Found " + str(len(dead_instances)) + " unexpected dead " +
                "instances to clean up."
            )

        # Remove data on dead instances
        for instance_id in dead_instances:
            process = self.get_process_info_by_pid(instance_id)

            self.logger.debug(
                "Removing data on '" + str(process['syncname']) + "' " +
                "because it is not running as expected."
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
        # TODO: discuss if self.logger needs to happen here? I think not? -BY

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

        self.logger.debug(
            "Found " + str(len(pids)) + " running instances on this system: PIDs " +
            ", ".join(pids)
        )

        # Return, after converting to ints
        return list(map(int, pids))

    def import_config(self):
        """Import config from config, and apply details where needed.

        Parameters
        ----------
        none

        Returns
        -------
        True
            if success

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
            'unison_user',
            'webhooks',
            'rotate_logs',
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
            'unison_user': getpass.getuser(),
            'rotate_logs': "time",
        }

        # TODO: Implement allowedSettings, which force settings to be
        # in a given list of options

        # Apply default settings to fill gaps between explicitly set ones
        for key in defaultSettings:
            if (key not in self.config):
                self.config[key] = defaultSettings[key]

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

        return True

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
        self.logger.debug(
            "Starting script shutdown in the class " +
            self.__class__.__name__
        )

        # Clean up dead processes before exiting
        self.cleanup_dead_processes()
        """
        print("FAKELOG: [" + time.strftime("%c") + "] [UnisonCTRL] Exiting\n")
        """
        self.logger.debug(
            "Script shutdown complete in class " +
            self.__class__.__name__
        )

        self.logger.info("Exiting UnisonCTRL")
