#!/usr/bin/env python3

# Path to store PID files

# Logfile paths
unisonctrl_log_dir = "/var/log/unisonctrl"
unison_log_dir = "/var/log/unisonctrl/unison-instance-logs"

# This does not need cto persist between reboots, as it only contains
# information about running unison instances. Typically easiest to mount
# somewhere in /var/run, or /tmp
data_dir = "/tmp/unisonctrl"

# This is where unison will store data which *DOES* need to persist. Typically
# easiest to pass the home directory of the running user, or a folder in /opt
# or /var
unison_home_dir = "/home/syncd"

# This is the user you're running as. Needed for unison to run correctly
# Often, python can detect this automatically, but if it can't, this
# setting can override the auto-detected value
# unison_user = "syncd"

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
        # This is for debugging, to ensure each instance restarts every tim
        "sort_count": 5,
    },

    # Sync the next 3 highest-counted folders starting with "11" in their
    # own unison instance
    {
        "syncname": "recent-phone-orders-batch-2",
        "dir_selector": "Art Department/11*",
        "sort_method": "name_highfirst",

        "sort_count": 3,
    },

    # Sync the next 4 highest-counted folders starting with "11" in their
    # own unison instance
    {
        "syncname": "recent-phone-orders-batch-3",
        "dir_selector": "Art Department/11*",
        "sort_method": "name_highfirst",

        "sort_count": 4,
    },

    # Sync the next 8 highest-counted folders starting with "11" in their
    # own unison instance
    {
        "syncname": "recent-phone-orders-batch-4",
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

        "sort_count": 3,
    },

    # Sync the next 3 highest-counted folders starting with "M" in their
    # own unison instance
    {
        "syncname": "recent-magento-orders-batch-2",
        "dir_selector": "Art Department/M0*",
        "sort_method": "name_highfirst",

        "sort_count": 3,
    },

    # Sync the next 6 highest-counted folders starting with "M" in their
    # own unison instance
    {
        "syncname": "recent-magento-orders-batch-3",
        "dir_selector": "Art Department/M0*",
        "sort_method": "name_highfirst",

        "sort_count": 4,
    },


    # Sync the next 6 highest-counted folders starting with "M" in their
    # own unison instance
    {
        "syncname": "recent-magento-orders-batch-4",
        "dir_selector": "Art Department/M0*",
        "sort_method": "name_highfirst",

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
        "sort_count": 3,
    },

    # Sync the next 6 highest-counted folders starting with 'O' in their
    # own unison instance
    {
        "syncname": "recent-web-orders-batch-3",
        "dir_selector": "Art Department/O*",
        "sort_method": "name_highfirst",
        "sort_count": 4,
    },

    # Sync the next 6 highest-counted folders starting with 'O' in their
    # own unison instance
    {
        "syncname": "recent-web-orders-batch-4",
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
        # "include_ignores": True,
    },
]

# Log rotation
# First option is "off", which logs to a single file and never rotates.
# Second is "time", which rotates daily, keeping the past 14 days.
# The third option is "size", which rotates once a file reaches 50 MB.
#
# "timed" is default if this config entry isn't found.
#
rotate_logs = "time"

# These options are passed through to unison on every run
global_unison_config_options = [
    # Test for space handling
    "-copyquoterem=true",

    # Speeds up comparison
    "-fastcheck",

    # Needed for Windows share to work properly
    "-ignorecase",

    # Define conflict handling rules
    "-auto",
    "-copyonconflict",
    "-prefer=newer",

    # Don't bother with permissions
    "-perms=0",
    "-dontchmod=true",

    # Retry params
    "-retry=10",
    "-repeat=5",

    # Not entirely sure what these do, so....
    # "-maxerrors=20",
    # "-contactquietly",
    "-dumbtty",

    # Run interaction-free
    "-auto",
    "-batch",

    # Ignore lockfiles, since we'll be managing the processes ourselves
    "-ignorelocks",

    # Propagate file modification times
    "-times=true",

    # A misc settings
    "-watch=false",
    "-servercmd=/usr/bin/unison",
    # "-terse=true",

    # Enable unison debugging if needed
    # "-debug=all",

    # consider using this to make more efficent with large changesets
    "-sortbysize",

    # Other unsyncable extensions
    "-ignore=Name {*.tmp}",
    "-ignore=Name {cifs*}",

    # Linux extensions
    "-ignore=Name {*~}",
    "-ignore=Name {.fuse_hidden*}",
    "-ignore=Name {.directory}",
    "-ignore=Name {.Trash-*}",
    "-ignore=Name {.nfs*}",
    "-ignore=Name {.*.swp}",

    # Mac extensions
    "-ignore=Name {*.DS_Store}",
    "-ignore=Name {.AppleDouble}",
    "-ignore=Name {.LSOverride}",
    "-ignore=Name {._*}",
    "-ignore=Name {.DocumentRevisions-V100}",
    "-ignore=Name {.fseventsd}",
    "-ignore=Name {.Spotlight-V100}",
    "-ignore=Name {.TemporaryItems}",
    "-ignore=Name {.Trashes}",
    "-ignore=Name {.VolumeIcon.icns}",
    "-ignore=Name {.com.apple.timemachine.donotpresent}",
    "-ignore=Name {.AppleDesktop}",
    "-ignore=Name {.AppleDB}",
    "-ignore=Name {Network Trash Folder}",
    "-ignore=Name {Temporary Items}",
    "-ignore=Name {.apdisk}",
    "-ignore=Name {*.DS_Store}",
    "-ignore=Name {*.DS_Store}",
    "-ignore=Name {*.DS_Store}",

    # Windows extensions
    "-ignore=Name {Thumbs.db}",
    "-ignore=Name {ehthumbs.db}",
    "-ignore=Name {ehthumbs_vista.db}",
    "-ignore=Name {*.stackdump}",
    "-ignore=Name {Desktop.ini}",
    "-ignore=Name {$RECYCLE.BIN/}",
    "-ignore=Name {*.cab}",
    "-ignore=Name {*.msi}",
    "-ignore=Name {*.msm}",
    "-ignore=Name {*.msp}",
    "-ignore=Name {*.lnk}",

    # Software specific lock files
    # Adobe InDesign
    "-ignore=Name {*.idlk}",
    # Adobe FrameMaker
    "-ignore=Name {*.lck}",
    # Microsoft Word
    "-ignore=Name {~.doc*}",
    # Microsoft Excel
    "-ignore=Name {~$*.xls}",
    "-ignore=Name {*.xlk}",
    # Microsoft PowerPoint
    "-ignore=Name {~$*.ppt}",
    # Visio autosave temporary files
    "-ignore=Name {*.~vsd*}",
    # LibreOffice Lockfiles
    "-ignore=Name {.~lock.*#}",

]

# These options are passed through to unison on every run
webhooks = [

]

# If set to true, directories will be made if the paths are not found
# on the system
# If set to false, program will return an error if the directories do
# not exist
make_root_directories_if_not_found = True
