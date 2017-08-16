from distutils.core import setup

setup(
  name = 'unisonctl',
  version = '0.0.1',
  description = 'A frontend for unison allowing it to handle some read-only large datasets more efficently.',
  author = 'Ben Yanke',
  author_email = 'ben@benyanke.com',
  #url = 'https://github.com/benyanke/unisonctl', # use the URL to the github repo
  # download_url = 'https://github.com/benyanke/unisonctl/archive/0.1.tar.gz', # I'll explain this in a second
  keywords = ['unsion', 'synchronization', 'sync', 'bigdata', 'large', 'dataset', 'replication', 'dataset', 'file'],
  packages = ['unisonctl'], # this must be the same as the name above
  classifiers = [],
  zip_safe=False
)
