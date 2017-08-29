# UnisonCTRL

UnisonCTRL makes it easier to sync large mostly-read-only datasets with unison by spawning multiple unison instances.

To run, execute `python3 unisonctrl/unisonctrl.py.` This will run everything.

## TODO:
* Get webhooks working for reporting and monitoring
  * Number of new/existing instances
  * Instance information
  * Report on unknown dead instances - this is important
* Turn into a proper terminal tool with options, like force restart all,
  and get stats
