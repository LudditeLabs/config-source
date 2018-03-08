from __future__ import absolute_import
import os
import errno
from types import ModuleType
from future.moves.collections import UserDict
from future.utils import PY2, iteritems
import pkg_resources

__version__ = '0.0.2'

_config_sources = dict()


def config_source(source):
    def wrapper(f):
        assert source not in _config_sources, 'Already registered: %s' % source
        _config_sources[source] = f
        return f
    return wrapper


class UnknownConfigError(Exception):
    """This error is raised if requested config source is not found."""
    pass


class Config(UserDict):
    """Dict-like configuration.

    This class provides API to populate itself with values from various sources.
    """
    def __init__(self, source_args=None):
        if PY2:  # pragma: no cover
            UserDict.__init__(self)
        else:  # pragma: no cover
            super(Config, self).__init__()
        self._source_args = source_args or dict()

    def load_from(self, source, *args, **kwargs):
        getter = _config_sources.get(source)
        if getter is None:
            raise UnknownConfigError('Unknown config source: %s' % source)

        kw = self._source_args.get(source)
        if kw is not None:
            kw = kw.copy()
            kw.update(kwargs)
        else:
            kw = kwargs

        return getter(self, *args, **kw)


@config_source('object')
def load_from_object(config, obj):
    for key in dir(obj):
        if key.isupper():
            config[key] = getattr(obj, key)


@config_source('env')
def load_from_env(config, prefix, trim_prefix=True):
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
    d = ModuleType('config')
    d.__file__ = filename

    try:
        with open(filename, mode='rb') as config_file:
            exec(compile(config_file.read(), filename, 'exec'), d.__dict__)
    except IOError as e:
        if silent and e.errno in (errno.ENOENT, errno.EISDIR):
            return False
        raise

    return config.load_from('object', d)


for entry_point in pkg_resources.iter_entry_points('configsource.sources'):
    entry_point.load()
