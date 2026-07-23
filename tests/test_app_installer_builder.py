import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from installer_builder import AppInstallerBuilder, InstallerBuilder


def make_application(**capabilities):
    identity = {
        "name": "Test App",
        "version": "1.0.0",
        "author": "Accessible Apps",
        "website": "https://example.test",
    }
    return SimpleNamespace(**identity, **capabilities)


@pytest.fixture(autouse=True)
def packaging_data_modules(monkeypatch):
    monkeypatch.setitem(sys.modules, "babel", SimpleNamespace(__path__=["babel"]))
    monkeypatch.setitem(
        sys.modules,
        "certifi",
        SimpleNamespace(__file__="certifi/cacert.pem"),
    )


def test_false_capabilities_do_not_add_packaging_inputs(monkeypatch):
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    application = make_application(
        output=False,
        sound=False,
        UI_sounds=False,
        update_endpoint="",
        activation_module=None,
        main_window_class=None,
    )

    builder = AppInstallerBuilder(application=application, main_module="main.pyw")

    assert builder.datafile_packages == []
    assert builder.localized_packages == []
    assert builder.extra_packages == []
    assert builder.includes == []
    assert builder.create_update is False
    assert builder.extra_files_to_sign == []


def test_true_capabilities_preserve_existing_packaging_inputs(monkeypatch):
    monkeypatch.setattr(
        "importlib.util.find_spec",
        lambda name: object() if name == "app_elements" else None,
    )
    application = make_application(
        output=True,
        sound=True,
        UI_sounds=False,
        update_endpoint="https://example.test/updates",
        activation_module="activation",
        main_window_class="gui.main_window.MainWindow",
    )

    builder = AppInstallerBuilder(application=application, main_module="main.pyw")

    assert builder.datafile_packages == [
        "accessible_output2",
        "sound_lib",
        "autoupdate",
    ]
    assert builder.localized_packages == ["product_key", "wx", "app_elements"]
    assert builder.extra_packages == ["product_key"]
    assert builder.includes == ["activation", "gui.main_window"]
    assert builder.create_update is True
    assert builder.extra_files_to_sign == ["bootstrap.exe"]


def test_gui_without_app_elements_does_not_add_its_locale_data(monkeypatch):
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    application = make_application(main_window_class="gui.main_window.MainWindow")

    builder = AppInstallerBuilder(application=application, main_module="main.pyw")

    assert builder.localized_packages == ["wx"]
    assert builder.includes == ["gui.main_window"]


def test_py2exe_command_uses_current_freeze_api(monkeypatch):
    freeze = Mock()
    monkeypatch.setattr("py2exe.freeze", freeze)
    monkeypatch.setattr(
        "setuptools.setup",
        lambda **kwargs: pytest.fail("py2exe must not use the removed setuptools command"),
    )
    monkeypatch.setattr(sys, "argv", ["setup.py", "py2exe"])
    builder = InstallerBuilder(
        main_module="main.pyw",
        name="Test App",
        version="1.0.0",
        author="Accessible Apps",
        datafiles=[("data", ["cards.csv"])],
    )

    builder.build_installer()

    call = freeze.call_args.kwargs
    assert call["console"] == []
    assert call["windows"][0]["script"] == "main.pyw"
    assert call["windows"][0]["dest_base"] == "Test App"
    assert call["data_files"] == [("data", ["cards.csv"])]
    assert call["options"]["bundle_files"] == 3
    assert call["version_info"] == {
        "version": "1.0.0",
        "company_name": "Accessible Apps",
        "copyright": builder.get_copyright(),
        "product_name": "Test App",
        "product_version": "1.0.0",
    }


def test_innosetup_command_freezes_before_setuptools_dispatch(monkeypatch):
    freeze = Mock()
    setup = Mock(side_effect=lambda **kwargs: assert_freeze_called())

    def assert_freeze_called():
        assert freeze.called

    monkeypatch.setattr("py2exe.freeze", freeze)
    monkeypatch.setattr("setuptools.setup", setup)
    monkeypatch.setattr(sys, "argv", ["setup.py", "innosetup"])
    builder = InstallerBuilder(
        main_module="main.pyw",
        name="Test App",
        version="1.0.0",
        author="Accessible Apps",
    )

    builder.build_installer()

    freeze.assert_called_once()
    setup.assert_called_once()
