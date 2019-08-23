config-source
=============

.. image:: https://travis-ci.org/LudditeLabs/config-source.svg?branch=master
   :target: https://travis-ci.org/LudditeLabs/config-source

This package provides extensible configuration loading from various sources.

Features:

* Dict-like configuration loading from:

  - python dictionaries
  - python objects
  - python files
  - environment variables
  - JSON files

* Custom configuration sources and objects.

Basically ``config-source`` provides a way to register configuration loaders and
call them by names. The loader accepts optional arguments, reads configuration
from a specific source and populates a configuration object.

Example::

    from config_source import DictConfig
    from config_source import DictConfigLoader

    config = DictConfig()
    config.load_from('pyfile', '/path/to/config.py')
    config.load_from('json', '/path/to/config.json')
    config.load_from('env', prefix='MYCFG_')

    loader = DictConfigLoader(config)
    loader.load('/path/to/config.py')
    loader.load('/path/to/config.json')
    loader.load(SomeClassWithConfigs)

Usage
-----

Out of the box you could use:

* Low level ``load_to()`` function.
* ``DictConfig`` class.
* ``DictConfigLoader`` class to assist in configurations loading.


``load_to()`` calls a loader registered for a specific source and populates
a config object passed to it::

    load_to(config, 'source_name', ...)

* ``config`` - configuration object to populate.
* ``source_name`` - configuration source name.

``DictConfig`` behaves like a regular python dictionary and provides
``load_from`` method to load configurations from various sources (it uses
``load_to()`` internally)::

    config = DictConfig()
    config.load_from(<source_name>, *args, **kwargs)

* ``<source_name>`` - configuration source name;

* ``*args`` and ``**kwargs`` - arguments for configuration loader.

The following sources are provided out of the box for *dict-like*
configurations.

**Note**: *dict-like* means any object with mapping interface can be used as
configuration object::

    config = {}
    load_to(config, 'env', ...)

    dictconfig = DictConfig()
    dictconfig.load_from('env', ...)
    load_to(dictconfig, 'env', ...)

* ``object`` - load configuration from a python ``object``. It reads attributes
  with uppercase names::


      config.load_from('object', <object>)

  Example::

      class MyConfig:
          SECRET_KEY = 123
          DEBUG = False

      ...

      config.load_from('object', MyConfig)

* ``dict`` - load configuration from a python dictionary. Reads only uppercase
  keys::

      config.load_from('dict', <dict>)

  Example::

      myconfig = dict(SECRET_KEY=123, DEBUG=False)
      config.load_from('dict', myconfig)

* ``env`` - load configuration from current runtime environment::

      config.load_from('env', prefix=<name_prefix>, trim_prefix=True)


  - ``prefix`` - Environment variable name prefix.

  - ``trim_prefix`` - Include or not prefix to result config name

  Example::

      # Load vars with names MYCFG_*, like MYCFG_SECRET.
      config.load_from('env', prefix='MYCFG_')

* ``pyfile`` - load configuration from a python file. Reads only uppercase
  attributes::

      config.load_from('env', filename, silent=False)

  - ``filename`` - filename to load.

  - ``silent`` - Don't raise an error on missing files.

  Example::

      config.load_from('pyfile', 'config.py')

* ``json`` - load configuration from a json file. Reads only uppercase keys::

      config.load_from('json', filename, silent=False)

  - ``filename`` - filename to load.

  - ``silent`` - Don't raise an error on missing files.

  Example::

      config.load_from('json', '/path/to/config.json')

``DictConfigLoader`` auto-detects source name from input configuration source::

    loader = DictConfigLoader(config)
    loader.load('/path/to/file.py')

    # Same as:
    config.load_from('pyfile', '/path/to/file.py')

You may subclass to extend auto-detection.

Add source
----------

``config_source`` decorator is used to register additional configuration
sources::

    from config_source import config_source

    @config_source('source_name')
    def myloader(config, arg1, arg2):
        config['XX'] = arg1 + arg2

    config.load_from('source_name', 1, arg2=2)

Configuration loader must be a callable with at least one argument -
configuration object to populate. Other arguments are optional and loader specific.

There is a possibility to register configuration sources by implementing
a package with entry point::

    setup(
        ...
        entry_points={'config_source.sources': '<source> = <package name>'},
        ...
    )

In the package you use ``config_source`` decorator.

For more info on entry points see

* https://packaging.python.org/guides/creating-and-discovering-plugins/
* http://setuptools.readthedocs.io/en/latest/pkg_resources.html#entry-points
* http://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins

**Note**: you could specify single entry point even if your package adds
multiple sources.

Defaults
--------

Instead of always passing parameters to configuration loaders you could set
defaults in ``DictConfig``::

    config = DictConfig(defaults={
        'env': {'prefix': 'MYAPP_'},
        'pyfile': {'filename': '/path/to/file.py'}
    })

    # 'prefix' will be set to MYAPP_ for 'env' config source.
    # Load from 'MYAPP_*' vars by default.
    config.load_from('env')

    # Load from 'MY_*' vars
    config.load_from('env', 'MY_')

    # Load from '/path/to/file.py' by default.
    config.load_from('pyfile')

    # Load from '/path/to/another/file.py'.
    config.load_from('pyfile', '/path/to/another/file.py')

``defaults`` is a map where keys are source names and values are keyword
parameters to be passed to loaders.

Custom configuration type
-------------------------

You can register configuration source for specific type
(by default it's a ``dict``)::

    @config_source('source_name', config_type='mytype')
    def mytype_loader(config):
        ....

``config_type`` here is a string defining configuration object type.

Now you populate your config object using that loader::

    load_to(config, 'source_name', config_type='mytype')

where ``config`` is object implementing ``mytype`` interface.

``list`` configuration example::

    from config_source import config_source, load_to


    @config_source('object', config_type='list')
    def object_loader(config, obj):
    has = False
    for key in dir(obj):
        if key.isupper():
            has = True
            config.append(getattr(obj, key))
    return has


    class MyConfig:
        SECRET = 1
        DEBUG = False


    cfg = []
    load_to(cfg, 'object', config_type='list')

    # cfg = [1, False]

    # Fails because by default it calls loader for 'dict' configuration.
    # load_to(cfg, 'object')

