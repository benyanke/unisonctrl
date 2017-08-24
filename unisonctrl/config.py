#!/usr/bin/env python3

# Path to store PID files

# This does not need to persist between reboots, as it only contains
# information about running unison instances. Typically easiest to mount
# somewhere in /var/run, or /tmp
data_dir = "/tmp/unisonctrl"

# This is where unison will store data which *DOES* need to persist. Typically
# easiest to pass the home directory of the running user, or a folder in /opt
# or /var
unison_home_dir = "/home/syncd"

# Define unsion root directories
# unison_local_root="/mnt/local/pcnart"
unison_local_root = "/mnt/lan/pcnart"


# This is used by unison to properly set the local hostname
# Unison will do a complete rescan every time this changes, and it needs to be
# different than the remote hostname. Typically it should be set to the same
# as the system's hostname, but it can really be any alphanumerics str.
#
# By default, you don't need this, but sometimes you might, if unison isn't
# working without it. By default, it is the system hostname as found by
# platform.node().
unison_local_hostname = "pcnartsync"

# Note: this script uses ssh to connect

# Absolute path
unison_remote_root = "/mnt/local/pcnart"

# SSH connection string
# typical example: 'jdoe@example.com'
# another valid example, paired with ~/.ssh/config entry: 'syncserver'
unison_remote_ssh_conn = "aws-artshare-sync"
# unison_remote_ssh_conn = "aws-artshare-appserver"
# unison_remote_ssh_conn = "syncd@10.100.1.247"

# This keyfile will be specified if this is set
# unison_remote_ssh_keyfile = "/home/syncd/.ssh/keys/pcnartsync_unison_key"


# Path to unison if we can not find it by default
# unison_path="/usr/bin/unison"

# Important directories - these will get their own unison instances
# to speed up replication

# NOTE: Order matters. The rules are run in sequential order. Each rule
# can only capture files not already captured in a previous rule, to
# ensure that syncs don"t overlap, unless the "overlap" paramater is set
# to true for a given rule

sync_hierarchy_rules = [

    # Sync the 3 highest-counted folders starting with "11" in their
    # own unison instance
    {
        # Name = of the unison profile which will be created
        # can be any alphanumeric string (a-z, A-Z, 1-9) to identify the sync
        "syncname": "recent-phone-orders-batch-1",

        # Select the directories which will be synced with this profile
        # Use standard shell globbing to select files from the root directory
        # TODO: rewrite that wording
        "dir_selector": "Art Department/11*",

        # Select a method to sort the files
        # Current options:
        #   name_highfirst
        #   name_highfirst
        # FUTURE:
        #   creation_date_highfirst
        #   creation_date_lowfirst
        "sort_method": "name_highfirst",
        # Select X from the top of the list you sorted above
        # "sort_count": 4,
        "sort_count": 3,
    },

    # Sync the 3 highest-counted folders starting with "11" in their
    # own unison instance
    {
        "syncname": "recent-phone-orders-batch-2",
        "dir_selector": "Art Department/11*",
        "sort_method": "name_highfirst",

        "sort_count": 8,
    },

    # Sync the 3 highest-counted folders starting with "M" in their
    # own unison instance
    {
        "syncname": "recent-magento-orders-batch-1",
        "dir_selector": "Art Department/M0*",
        "sort_method": "name_highfirst",

        # You can also use offset to start the count down the list. For
        # example,this search would capture directores 4-6 in the search,
        # because after implementing the offset of 3, they are the next 3
        "sort_count": 3,
    },


    # Sync the next 6 highest-counted folders starting with "M" in their
    # own unison instance
    {
        "syncname": "recent-magento-orders-batch-2",
        "dir_selector": "Art Department/M0*",
        "sort_method": "name_highfirst",

        # You can also use offset to start the count down the list. For
        # example,this search would capture directores 4-6 in the search,
        # because after implementing the offset of 3, they are the next 3
        "sort_count": 6,
    },

    # Sync the 3 highest-counted folders starting with 'O' in their
    # own unison instance
    {
        "syncname": "recent-web-orders-batch-1",
        "dir_selector": "Art Department/O*",
        "sort_method": "name_highfirst",
        "sort_count": 3,
    },

    # Sync the next 3 highest-counted folders starting with 'O' in their
    # own unison instance
    {
        "syncname": "recent-web-orders-batch-2",
        "dir_selector": "Art Department/O*",
        "sort_method": "name_highfirst",
        "sort_count": 6,
    },

    # Sync any files not caught above in their own instance
    {
        "syncname": "catch-all",
        "dir_selector": "*",

        # NOTE: This option not yet implemented
        # This generates ignore statements for each of the directories
        # already handled in other instances, to ensure no overlap
        "include_ignores": True,
    },
]

# These options are passed through to unison on every run
global_unison_config_options = [
    # Test for space handling
    # "-copyquoterem",

    # Propagate file modification times
    "-times",

    # Speeds up comparison
    "-fastcheck",

    # Needed for Windows share to work properly
    "-ignorecase",

    # Define conflict handling rules
    "-auto",
    "-copyonconflict",
    "-prefer=newer",

    # Retry params
    "-retry=10",
    "-perms=0",
    "-repeat=1",

    # Not entirely sure what these do, so....
    "-maxerrors=20",
    "-contactquietly",
    "-dumbtty",

    # Run interaction-free
    "-auto",
    "-batch",

    # Ignore lockfiles, since we'll be managing the processes ourselves
    "-ignorelocks",
    "-ignorearchives",

    # TODO: Copy in entries from "ignores-to-add-back-later" before deployment

]

# Log file
# log_file="/opt/unison/config/templates"
# log_file="/opt/unison/config/templates"

# If set to true, directories will be made if the paths are not found
# on the system
# If set to false, program will return an error if the directories do
# not exist
make_root_directories_if_not_found = True
