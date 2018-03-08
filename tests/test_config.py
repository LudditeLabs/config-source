from __future__ import absolute_import
try:
    from unittest.mock import patch, Mock, call
except ImportError:
    from mock import patch, Mock, call
import pytest
import configsource
from configsource import (
    config_source,
    load_to,
    merge_kwargs,
    ConfigSourceError,
    DictConfig
)


# Test: config_source() decorator.
class TestConfigSource(object):
    # Test: register new config sources for default config type (dict).
    def test_register_default(self):
        x = lambda x: None
        y = lambda x: None

        with patch.dict('configsource._config_sources', clear=True):
            config_source('one')(x)
            assert configsource._config_sources == {'dict': {'one': x}}

            config_source('two')(y)
            assert configsource._config_sources == {'dict': {'one': x,
                                                             'two': y}}

    # Test: register new config sources for various config types.
    def test_register(self):
        x = lambda x: None
        y = lambda x: None

        with patch.dict('configsource._config_sources', clear=True):
            config_source('one', 'xx')(x)
            assert configsource._config_sources == {'xx': {'one': x}}

            config_source('two', 'yy')(y)
            assert configsource._config_sources == {'xx': {'one': x},
                                                    'yy': {'two': y}}

    # Test: register already registered source.
    def test_register_error(self):
        x = lambda x: None
        y = lambda x: None

        with patch.dict('configsource._config_sources', clear=True):
            config_source('one')(x)
            assert configsource._config_sources == {'dict': {'one': x}}

            with pytest.raises(AssertionError) as e:
                config_source('one')(y)

            assert str(e.value) == 'Already registered: one'

    # Test: override already registered source.
    def test_register_override(self):
        x = lambda x: None
        y = lambda x: None

        with patch.dict('configsource._config_sources', clear=True):
            config_source('one')(x)
            assert configsource._config_sources == {'dict': {'one': x}}

            config_source('one', force=True)(y)
            assert configsource._config_sources == {'dict': {'one': y}}

    # Test: already registered sources
    def test_registered(self):
        default = configsource._config_sources.get('dict')
        assert default is not None
        assert 'dict' in default
        assert 'env' in default
        assert 'object' in default
        assert 'pyfile' in default
        assert 'json' in default


# Test: merge_kwargs() function.
class TestMergeKwargs(object):
    # Test: Merge with None defaults.
    def test_none(self):
        kw = merge_kwargs(dict(a=1, b=2), None)
        assert kw == dict(a=1, b=2)

    # Test: Normal merge.
    def test_norm(self):
        kw = merge_kwargs(dict(a=1, b=2), dict(c=3, d=4))
        assert kw == dict(a=1, b=2, c=3, d=4)

    # Test: Merge with override defaults.
    def test_override(self):
        # 'a' will be overridden.
        kw = merge_kwargs(dict(a=1, b=2), dict(a=3, d=4))
        assert kw == dict(a=1, b=2, d=4)


# Test: load_to() function.
class TestLoadTo(object):
    # Test: load to unknown config type.
    def test_unknown_type(self):
        with patch.dict('configsource._config_sources', clear=True):
            with pytest.raises(ConfigSourceError) as e:
                load_to({}, 'env', config_type='bla')
            assert str(e.value) == 'Unknown config type: bla'

    # Test: load from unknown source.
    def test_unknown_src(self):
        with patch.dict('configsource._config_sources', clear=True):
            configsource._config_sources['bla'] = dict()
            with pytest.raises(ConfigSourceError) as e:
                load_to({}, 'env', 'bla')
            assert str(e.value) == 'Unknown source: env (config type: bla)'

    # Test: call mocked loader.
    def test_mock_loader(self):
        loader = Mock(return_value=123)
        config = dict()
        with patch.dict('configsource._config_sources', clear=True):
            config_source('test_source')(loader)
            res = load_to(config, 'test_source', 'dict', 1, a=2)

            assert res == 123
            assert loader.mock_calls == [call(config, 1, a=2)]

    # Test: call real loader.
    # Exmaple of non-dict config.
    def test_loader(self):
        def load_to_list(config, val=1):
            config.append(val)
            return True

        config = []
        with patch.dict('configsource._config_sources', clear=True):
            config_source('value', 'list')(load_to_list)
            res = load_to(config, 'value', 'list')
            assert res is True
            assert config == [1]

            res = load_to(config, 'value', 'list', val=123)
            assert res is True
            assert config == [1, 123]


class TestDictConfig(object):
    # Test: construction without args.
    def test_construct(self):
        config = DictConfig()

        assert config == dict()
        assert config.data == dict()
        assert config._defaults == dict()

    # Test: construct with defaults.
    def test_construct_args(self):
        config = DictConfig(defaults=dict(one=1, two=2))

        assert config == dict()
        assert config.data == dict()
        assert config._defaults == dict(one=1, two=2)

    # Test: try load unknown config source.
    def test_load_from_unknown(self):
        config = DictConfig()
        with pytest.raises(ConfigSourceError) as e:
            config.load_from('test_env')
        assert str(e.value) == 'Unknown source: test_env (config type: dict)'

    # Test: Call config loader without args.
    @patch.dict('configsource._config_sources', clear=True)
    def test_load_from_noargs(self):
        mock = Mock()
        config_source('my')(mock)

        config = DictConfig()
        config.load_from('my')

        assert mock.mock_calls == [call(config)]

    # Test: Call config loader with args.
    @patch.dict('configsource._config_sources', clear=True)
    def test_load_from_args(self):
        mock = Mock()
        config_source('my')(mock)

        config = DictConfig()
        config.load_from('my', 1, 2, k=3, w=4)

        assert mock.mock_calls == [call(config, 1, 2, k=3, w=4)]

    # Test: Call config loader with extra args.
    @patch.dict('configsource._config_sources', clear=True)
    def test_load_from_args_extra(self):
        mock = Mock()
        config_source('my')(mock)

        config = DictConfig(defaults={'my': dict(x='y')})
        config.load_from('my', 1, k=3)

        # It must add extra args from source_args.
        assert mock.mock_calls == [call(config, 1, k=3, x='y')]

        # 'source_args' must stay unchanged.
        assert config._defaults == {'my': dict(x='y')}

    # Test: load settings from object.
    def test_from_object(self):
        class Cfg:
            PARAM1 = 1
            PARAM_2 = '2'
            lower_param = dict()  # lowercase won't load.

        config = DictConfig()
        config.load_from('object', Cfg)

        assert config == dict(PARAM1=1, PARAM_2='2')

    # Test: load settings from dict.
    def test_from_dict(self):
        src = dict(
            PARAM1=1,
            PARAM_2='2',
            lower_param=None  # lowercase won't load.
        )

        config = DictConfig()
        config.load_from('dict', src)

        assert config == dict(PARAM1=1, PARAM_2='2')

    # Test: load settings from runtime env, without prefixed vars.
    def test_from_env_empty(self):
        config = DictConfig()
        config.load_from('env', prefix='MYTEST')

        assert config == dict()

    # Test: load settings from runtime env.
    @patch.dict('os.environ', MYTEST_ONE='12', MYTEST_TWO='hello')
    def test_from_env(self):
        config = DictConfig()
        config.load_from('env', prefix='MYTEST')

        assert config == dict(ONE='12', TWO='hello')

    # Test: load settings from runtime env, don't trim prefix.
    @patch.dict('os.environ', MYTEST_ONE='12', MYTEST_TWO='hello')
    def test_from_env_notrim(self):
        config = DictConfig()
        config.load_from('env', prefix='MYTEST', trim_prefix=False)

        assert config == dict(MYTEST_ONE='12', MYTEST_TWO='hello')

    # Test: load settings from a python file.
    def test_from_pyfile(self, tmpdir):
        myconfig = tmpdir.join('myconfig.py')
        myconfig.write('ONE = 1\nTWO = "hello"\nthree = 3')

        config = DictConfig()
        config.load_from('pyfile', str(myconfig))

        # three won't load because it's lowercase.
        assert config == dict(ONE=1, TWO='hello')

    # Test: load settings from a missing python file, silent mode.
    def test_from_pyfile_missing_silent(self, tmpdir):
        filename = str(tmpdir.join('myconfig.py'))
        config = DictConfig()
        config.load_from('pyfile', filename, silent=True)

        assert config == dict()

    # Test: load settings from a missing file, not silent mode.
    def test_from_pyfile_missing_nosilent(self, tmpdir):
        filename = str(tmpdir.join('myconfig.py'))
        config = DictConfig()

        with pytest.raises(IOError):
            config.load_from('pyfile', filename)

    # Test: load settings from a json file.
    def test_from_json(self, tmpdir):
        myconfig = tmpdir.join('myconfig.json')
        myconfig.write('{"ONE": 1, "TWO": "hello", "three": 3}')

        config = DictConfig()
        config.load_from('json', str(myconfig))

        # three won't load because it's lowercase.
        assert config == dict(ONE=1, TWO='hello')

    # Test: load settings from a missing json file, silent mode.
    def test_from_json_missing_silent(self, tmpdir):
        filename = str(tmpdir.join('myconfig.json'))
        config = DictConfig()
        config.load_from('json', filename, silent=True)

        assert config == dict()

    # Test: load settings from a missing file, not silent mode.
    def test_from_json_missing_nosilent(self, tmpdir):
        filename = str(tmpdir.join('myconfig.json'))
        config = DictConfig()

        with pytest.raises(IOError):
            config.load_from('json', filename)
