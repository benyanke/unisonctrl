# UnisonCTRL

[![Coverage Status](https://coveralls.io/repos/github/benyanke/unisonctrl/badge.svg?branch=master)](https://coveralls.io/github/benyanke/unisonctrl?branch=master)

UnisonCTRL makes it easier to sync large mostly-read-only datasets with unison by spawning multiple unison instances ("threads"). Using the unisonctrl configuration file, instances can be tuned so that each unison instance is only responsible for a specific subset of the data, allowing large datasets to be synced efficently. Additionally, using this technique, an administrator can split up hot-data into smaller groups (allowing faster syncing) and colder data into larger groups (allowing slower syncing with less resources).

To run, execute `python3 unisonctrl/unisonctrl.py.` This is designed to be run in cron, once per minute.

## TODO:
* Get webhooks working for reporting and monitoring
  * Number of new/existing instances
  * Instance information
  * Report on unknown dead instances - this is important
* Turn into a proper terminal tool with options, like force restart all,
  and get stats
