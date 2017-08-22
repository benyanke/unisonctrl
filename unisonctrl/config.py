#!/usr/bin/env python3

# Path to store PID files

# This does not need to persist between reboots, as it only contains
# information about running unison instances. Typically easiest to mount
# somewhere in /var/run, or /tmp
data_dir = "/tmp/unisonctrl"

# Directory where the unison configuration files are stored
unison_config_dir = "/opt/unison/config"

# Directory where the unison configuration file templates are stored
unison_config_template_dir = "/opt/unison/config/templates"

# Define unsion root directories
# unison_local_root = "/mnt/local/pcnart"
unison_local_root = "/mnt/network-shares/pcnart"
unison_remote_root = "/mnt/local/pcnart"

# Path to unison if we can not find it by default
# unison_path = "/usr/bin/unison"
unison_path = "/usr/bin/unison_STOP"

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
        # Name of the unison profile which will be created
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
        "sort_count": 4,
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
    },

]

# These options are passed through to unison on every run
global_unison_config_options = [
    # Test for space handling
    # "copyquoterem = true",

    # Propagate file modification times
    "-times=true",

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

    # File ignore settings - these will not be synced
    # swp files (often created by vim and nano)
    "-ignore = 'Name {.*.swp}'",
    # hidden files (files starting with a dot are hidden in a unix env)
    "-ignore = 'Name {.*}'",
    # Other unsyncable extensions
    "-ignore = 'Name {*.tmp}'",
    "-ignore = 'Name {cifs*}'",

    # Linux extensions
    "-ignore = 'Name {*~}'",
    "-ignore = 'Name {.fuse_hidden*}'",
    "-ignore = 'Name {.directory}'",
    "-ignore = 'Name {.Trash-*}'",
    "-ignore = 'Name {.nfs*}'",

    # Mac extensions
    "-ignore = 'Name {*.DS_Store}'",
    "-ignore = 'Name {.AppleDouble}'",
    "-ignore = 'Name {.LSOverride}'",
    "-ignore = 'Name {._*}'",
    "-ignore = 'Name {.DocumentRevisions-V100}'",
    "-ignore = 'Name {.fseventsd}'",
    "-ignore = 'Name {.Spotlight-V100}'",
    "-ignore = 'Name {.TemporaryItems}'",
    "-ignore = 'Name {.Trashes}'",
    "-ignore = 'Name {.VolumeIcon.icns}'",
    "-ignore = 'Name {.com.apple.timemachine.donotpresent}'",
    "-ignore = 'Name {.AppleDB}'",
    "-ignore = 'Name {.AppleDesktop}'",
    "-ignore = 'Name {Network Trash Folder}'",
    "-ignore = 'Name {Temporary Items}'",
    "-ignore = 'Name {.apdisk}'",
    "-ignore = 'Name {*.DS_Store}'",
    "-ignore = 'Name {*.DS_Store}'",
    "-ignore = 'Name {*.DS_Store}'",

    # Windows extensions
    "-ignore = 'Name {Thumbs.db}'",
    "-ignore = 'Name {ehthumbs.db}'",
    "-ignore = 'Name {ehthumbs_vista.db}'",
    "-ignore = 'Name {*.stackdump}'",
    "-ignore = 'Name {Desktop.ini}'",
    "-ignore = 'Name {$RECYCLE.BIN/}'",
    "-ignore = 'Name {*.cab}'",
    "-ignore = 'Name {*.msi}'",
    "-ignore = 'Name {*.msm}'",
    "-ignore = 'Name {*.msp}'",
    "-ignore = 'Name {*.lnk}'",

    # Software specific lock files
    # Adobe InDesign
    "-ignore = 'Name {*.idlk}'",
    # Adobe FrameMaker
    "-ignore = 'Name {*.lck}'",
    # Microsoft Word
    "-ignore = 'Name {~.doc*}'",
    # Microsoft Excel
    "-ignore = 'Name {~$*.xls}'",
    "-ignore = 'Name {*.xlk}'",
    # Microsoft PowerPoint
    "-ignore = 'Name {~$*.ppt}'",
    # Visio autosave temporary files
    "-ignore = 'Name {*.~vsd*}'",
    # LibreOffice Lockfiles
    "-ignore = 'Name {.~lock.*#}'",

]

# Log file
# log_file = "/opt/unison/config/templates"
# log_file = "/opt/unison/config/templates"

# If set to true, directories will be made if the paths are not found
# on the system
# If set to false, program will return an error if the directories do
# not exist
make_root_directories_if_not_found = True
