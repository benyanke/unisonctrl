#

# Path to store PID files

# This does not need to persist between reboots, as it only contains information about running
# unison instances. Typically easiest to mount somewhere in /var/run
data_dir = '/var/run/unisonctl'

# Directory where the unison configuration files are stored
unison_config_dir = '/var/run/unisonctl'

# Directory where the unison configuration file templates are stored
unison_config_template_dir = '/opt/unison/config/templates'

# Log file
# log_file = '/opt/unison/config/templates'
# log_file = '/opt/unison/config/templates'

# If set to true, directories will be made if the paths are not found on the system
# If set to false, program will return an error if the directories do not exist
make_root_directories_if_not_found = True
