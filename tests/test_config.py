from __future__ import absolute_import
try:
    from unittest.mock import patch, Mock, call
except ImportError:
    from mock import patch, Mock, call
import pytest
import configsource
from configsource import config_source, Config


# Test: config_source() decorator.
class TestConfigSource(object):
    # Test: register new config sources.
    def test_register(self):
        x = lambda x: None
        y = lambda x: None

        with patch.dict('configsource._config_sources', clear=True):
            config_source('one')(x)
            assert configsource._config_sources == dict(one=x)

            config_source('two')(y)
            assert configsource._config_sources == dict(one=x, two=y)

    # Test: register already registered source.
    def test_register_error(self):
        x = lambda x: None
        y = lambda x: None

        with patch.dict('configsource._config_sources', clear=True):
            config_source('one')(x)
            assert configsource._config_sources == dict(one=x)

            with pytest.raises(AssertionError) as e:
                config_source('one')(y)

            assert str(e.value) == 'Already registered: one'

    # Test: already registered sources
    def test_registered(self):
        assert 'env' in configsource._config_sources
        assert 'object' in configsource._config_sources
        assert 'pyfile' in configsource._config_sources


class TestConfig(object):
    # Test: construction without any args.
    def test_construct(self):
        config = Config()

        assert config == dict()
        assert config.data == dict()
        assert config._source_args == dict()

    # Test: construct with source args
    def test_construct_args(self):
        config = Config(source_args=dict(one=1, two=2))

        assert config == dict()
        assert config.data == dict()
        assert config._source_args == dict(one=1, two=2)

    # Test: try load unknown config source.
    def test_load_from_unknown(self):
        config = Config()

        with pytest.raises(configsource.UnknownConfigError) as e:
            config.load_from('bla')
        assert str(e.value) == 'Unknown config source: bla'

    # Test: Call config loader without args.
    @patch.dict('configsource._config_sources')
    def test_load_from_noargs(self):
        mock = Mock()
        config_source('my')(mock)

        config = Config()
        config.load_from('my')

        assert mock.mock_calls == [call(config)]

    # Test: Call config loader with args.
    @patch.dict('configsource._config_sources')
    def test_load_from_args(self):
        mock = Mock()
        config_source('my')(mock)

        config = Config()
        config.load_from('my', 1, 2, k=3, w=4)

        assert mock.mock_calls == [call(config, 1, 2, k=3, w=4)]

    # Test: Call config loader with extra args.
    @patch.dict('configsource._config_sources')
    def test_load_from_args_extra(self):
        mock = Mock()
        config_source('my')(mock)

        config = Config(source_args={'my': dict(x='y')})
        config.load_from('my', 1, k=3)

        # It must add extra args from source_args.
        assert mock.mock_calls == [call(config, 1, k=3, x='y')]

        # 'source_args' must stay unchanged.
        assert config._source_args == {'my': dict(x='y')}

    # Test: load settings from object.
    def test_from_object(self):
        class Cfg:
            PARAM1 = 1
            PARAM_2 = '2'
            lower_param = dict()  # lowercase won't load.

        config = Config()
        config.load_from('object', Cfg)

        assert config == dict(PARAM1=1, PARAM_2='2')

    # Test: load settings from runtime env, without prefixed vars.
    def test_from_env_empty(self):
        config = Config()
        config.load_from('env', prefix='MYTEST')

        assert config == dict()

    # Test: load settings from runtime env.
    @patch.dict('os.environ', MYTEST_ONE='12', MYTEST_TWO='hello')
    def test_from_env(self):
        config = Config()
        config.load_from('env', prefix='MYTEST')

        assert config == dict(ONE='12', TWO='hello')

    # Test: load settings from runtime env, don't trim prefix.
    @patch.dict('os.environ', MYTEST_ONE='12', MYTEST_TWO='hello')
    def test_from_env_notrim(self):
        config = Config()
        config.load_from('env', prefix='MYTEST', trim_prefix=False)

        assert config == dict(MYTEST_ONE='12', MYTEST_TWO='hello')

    # Test: load settings from a file.
    def test_from_pyfile(self, tmpdir):
        myconfig = tmpdir.join('myconfig.py')
        myconfig.write('ONE = 1\nTWO = "hello"')

        config = Config()
        config.load_from('pyfile', str(myconfig))

        assert config == dict(ONE=1, TWO='hello')

    # Test: load settings from a missing file, silent mode.
    def test_from_pyfile_missing_silent(self, tmpdir):
        filename = str(tmpdir.join('myconfig.py'))
        config = Config()
        config.load_from('pyfile', filename, silent=True)

        assert config == dict()

    # Test: load settings from a missing file, not silent mode.
    def test_from_pyfile_missing_nosilent(self, tmpdir):
        filename = str(tmpdir.join('myconfig.py'))
        config = Config()

        with pytest.raises(IOError):
            config.load_from('pyfile', filename)
