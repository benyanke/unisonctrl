# UnisonCTRL

UnisonCTRL makes it easier to sync large mostly-read-only datasets with unison by spawning multiple unison instances.

## TODO:
* Implement better logging
* Create documentation describing config
* Clean up folder structure
* Get ignores working
* Get webhooks working for reporting and monitoring
  * Number of new/existing instances
  * Instance information
  * Report on unknown dead instances - this is important
* Automatic restart of instances when global config changes
  * Currently it only does this when individual instance config changes
* Turn into a proper terminal tool with options, like force restart all,
  and get stats
