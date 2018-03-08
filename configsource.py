from __future__ import absolute_import
import os
import os.path as op
from types import ModuleType
from future.moves.collections import UserDict
from future.utils import PY2, iteritems
import pkg_resources
import json
from collections import defaultdict

__version__ = '0.0.3'

# Configuration sources registry.
_config_sources = defaultdict(dict)


class ConfigSourceError(Exception):
    """Configuration source error."""
    pass


def config_source(source, config_type='dict', force=False):
    """Decorator to register config source.

    Configuration source is a callable with one required argument -
    configuration object to populate. It may have other required and optional
    arguments.

    Example::

        @config_source('json')
        def load_from_json(config, filename, silent=True):
            ...

    Args:
        source: Config source name.
        force: Force override if source is already registered.
        config_type: Configuration object type.

    See Also:
        :func:`load_to`.
    """
    def wrapper(f):
        group = _config_sources[config_type]
        if source in group and not force:
            raise AssertionError('Already registered: %s' % source)
        group[source] = f
        return f
    return wrapper


def load_to(config, from_source, config_type, *args, **kwargs):
    """Load configuration from given source to ``config``.

    Args:
        config: Destination configuration object.
        from_source: Configuration source name.
        config_type: ``config`` type.
        *args: Arguments for source loader.
        **kwargs: Keyword arguments for source loader.

    Returns:
        ``True`` if configuration is successfully loaded from the source
        and ``False`` otherwise.

    Raises:
        ConfigError: if config type or source is not found.

    See Also:
        :func:`config_source`.
    """
    group = _config_sources.get(config_type)
    if group is None:
        raise ConfigSourceError('Unknown config type: %s' % config_type)

    loader = group.get(from_source)
    if loader is None:
        raise ConfigSourceError('Unknown source: %s (config type: %s)'
                                % (from_source, config_type))

    return loader(config, *args, **kwargs)


def merge_kwargs(kwargs, defaults):
    """Helper function to merge ``kwargs`` into ``defaults``.

    Args:
        kwargs: Keyword arguments.
        defaults: Default keyword arguments.

    Returns:
        Merged keyword arguments (``kwargs`` overrides ``defaults``).
    """
    if defaults is not None:
        kw = defaults.copy()
        kw.update(kwargs)
    else:
        kw = kwargs
    return kw


class DictConfig(UserDict):
    """Dict-like configuration.

    This class provides API to populate itself with values from various sources.

    Example usage::

        config = DictConfig()
        config.load_from('env', prefix='APP)
        config.load_from('pyfile', 'config.py')

    You may set default keyword arguments for various config sources::

        config = DictConfig(defaults={
            'env': {'prefix': 'APP', 'trim_prefix': False},
            'pyfile: {'silent': True}
        })

        config.load_from('env')
        config.load_from('pyfile', 'config.py')

    Args:
        defaults: :class:`dict` with default keyword arguments
            for config sources. They merge with those that will be passed to
            :meth:`load_from`.
    """
    def __init__(self, defaults=None):
        # UserDict in py 2.X is old-style class so we can't use super().
        if PY2:  # pragma: no cover
            UserDict.__init__(self)
        else:  # pragma: no cover
            super(DictConfig, self).__init__()
        self._defaults = defaults or dict()

    def load_from(self, source, *args, **kwargs):
        """Load configuration from the given ``source``.

        Args:
            source: Config source name.
            *args: Arguments for config source loader.
            **kwargs: Keyword arguments for config source loader.

        Returns:
            ``True`` if configuration is successfully loaded from the source
            and ``False`` otherwise.

        See Also:
            :func:`load_to`, :func:`merge_kwargs`.
        """
        kwargs = merge_kwargs(kwargs, self._defaults.get(source))
        return load_to(self, source, 'dict', *args, **kwargs)


# -- Default configuration sources.

@config_source('object')
def load_from_object(config, obj):
    """Update ``config`` with values from the given ``object``.

    Only uppercase attributes will be loaded into ``config``.

    Args:
        config: Dict-like config.
        obj: Object with configuration.

    Returns:
        ``True`` if at least one attribute is loaded to ``config``.
    """
    has = False
    for key in dir(obj):
        if key.isupper():
            has = True
            config[key] = getattr(obj, key)
    return has


@config_source('dict')
def load_from_dict(config, obj):
    """Update ``config`` with values from the given dict-like object.

    Only uppercase keys will be loaded into ``config``.

    Args:
        config: Dict-like config.
        obj: Dict-like object.

    Returns:
        ``True`` if at least one key is loaded to ``config``.
    """
    has = False
    for key, val in iteritems(obj):
        if key.isupper():
            has = True
            config[key] = val
    return has


@config_source('env')
def load_from_env(config, prefix, trim_prefix=True):
    """Update ``config`` with values from current environment.

    Args:
        config: Dict-like config.
        prefix: Environment variables prefix.
        trim_prefix: Include or not prefix to result config name.

    Returns:
        ``True`` if at least one environment variable is loaded.
    """
    has = False
    prefix = prefix.upper()

    for key, value in iteritems(os.environ):
        if key.startswith(prefix):
            # drop prefix: <prefix>_<name>
            if trim_prefix:
                key = key[len(prefix) + 1:]
            config[key] = value
            has = True

    return has


@config_source('pyfile')
def load_from_pyfile(config, filename, silent=False):
    """Update ``config`` with values from the given python file.

    Args:
        config: Dict-like config.
        filename: Python filename.
        silent: Don't raise an error on missing files.

    Returns:
        ``True`` if at least one variable from the file is loaded.
    """
    d = ModuleType('config')
    d.__file__ = filename

    if not op.exists(filename):
        if not silent:
            raise IOError('File is not found: %s' % filename)
        return False

    with open(filename, mode='rb') as config_file:
        exec(compile(config_file.read(), filename, 'exec'), d.__dict__)
    return config.load_from('object', d)


@config_source('json')
def load_from_json(config, filename, silent=False):
    """Update ``config`` with values from the given JSON file.

    Args:
        config: Dict-like config.
        filename: JSON filename.
        silent: Don't raise an error on missing files.

    Returns:
        ``True`` if at least one variable from the file is loaded.
    """
    d = ModuleType('config')
    d.__file__ = filename

    if not op.exists(filename):
        if not silent:
            raise IOError('File is not found: %s' % filename)
        return False

    with open(filename) as f:
        d = json.load(f)
    return config.load_from('dict', d)


# -- Configuration sources from plugins.

for entry_point in pkg_resources.iter_entry_points('configsource.sources'):
    entry_point.load()
