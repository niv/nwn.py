import locale

import pytest

from nwn import environ as env


def _reset_caches():
    env._get_settings_tml.cache_clear()
    env._get_aliases.cache_clear()
    env.resolve_alias.cache_clear()
    env.get_setting.cache_clear()
    env.get_user_directory.cache_clear()
    env.get_install_directory.cache_clear()
    env.get_codepage.cache_clear()
    env.get_language.cache_clear()


@pytest.fixture(autouse=True)
def reset_env_caches():
    _reset_caches()
    yield
    _reset_caches()


def test_settings_tml(user_dir):
    user_dir.mkdir()
    with open(user_dir / "settings.tml", "wb") as f:
        toml_str = '[game.language]\noverride = "fr"\ncodepage = "cp1252"\n'
        f.write(toml_str.encode())
    assert env.get_setting("game.language.override") == "fr"
    assert env.get_setting("game.language.codepage") == "cp1252"
    assert env.get_setting("invalid") is None


def test_get_setting_not_found():
    assert env.get_setting("game.language.nonexistent") is None


def test_get_language_default():
    assert env.get_language() == env.Language.ENGLISH


def test_language_locale(monkeypatch):
    assert env.get_language() == env.Language.ENGLISH
    monkeypatch.setattr(locale, "getlocale", lambda: ("fr_FR", "UTF-8"))
    env.get_language.cache_clear()
    assert env.get_language() == env.Language.FRENCH


def test_language_change_env(monkeypatch):
    assert env.get_language() == env.Language.ENGLISH
    monkeypatch.setenv("NWN_LANGUAGE", "fr")
    env.get_language.cache_clear()
    assert env.get_language() == env.Language.FRENCH


def test_language_env_invalid(monkeypatch):
    monkeypatch.setenv("NWN_LANGUAGE", "invalid_lang_code")
    assert env.get_language() == env.Language.ENGLISH


def test_language_env_uppercase(monkeypatch):
    monkeypatch.setenv("NWN_LANGUAGE", "FR")
    assert env.get_language() == env.Language.FRENCH


def _monkey_get_setting(key):
    if key == "game.language.override":
        return "fr"
    if key == "game.language.codepage":
        return "cp1252"
    return None


def test_language_override_setting():
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(env, "get_setting", _monkey_get_setting)
        assert env.get_language() == env.Language.FRENCH


def test_get_codepage(monkeypatch):
    assert env.get_codepage() == env.CodePage.CP1252
    monkeypatch.setenv("NWN_LANGUAGE", "pl")
    assert env.get_codepage() == env.CodePage.CP1252
    env.get_codepage.cache_clear()
    assert env.get_codepage() == env.CodePage.CP1252
    env.get_codepage.cache_clear()
    env.get_language.cache_clear()
    assert env.get_codepage() == env.CodePage.CP1250


def test_alias_str_lookup(user_dir):
    user_dir.mkdir()
    assert env.resolve_alias("MODULES") == user_dir / "modules"


def test_invalid_alias(user_dir):
    user_dir.mkdir()
    with pytest.raises(ValueError, match="not a valid Alias"):
        env.resolve_alias("INVALID_ALIAS")


def test_alias_no_user_dir():
    with pytest.raises(FileNotFoundError, match="Could not locate NWN user directory;"):
        env.resolve_alias(env.Alias.MODULES)


def test_alias_user_dir(user_dir):
    user_dir.mkdir()
    assert env.resolve_alias(env.Alias.MODULES) == user_dir / "modules"


def test_alias_builtin(user_dir):
    user_dir.mkdir()
    assert env.resolve_alias(env.Alias.HD0) == env.get_user_directory()
    assert env.resolve_alias(env.Alias.HD0INSTALL) == env.get_install_directory()
    assert (
        env.resolve_alias(env.Alias.HD0LOCINSTALL)
        == env.get_install_language_directory()
    )


def test_nwn_ini_alias_override(user_dir):
    user_dir.mkdir()
    ini_path = user_dir / "nwn.ini"
    with open(ini_path, "w") as f:
        f.write("[Alias]\nMODULES = custom_modules\n")
    assert env.resolve_alias(env.Alias.MODULES) == user_dir / "custom_modules"
