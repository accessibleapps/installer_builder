import sys
from types import SimpleNamespace

import pytest

from installer_builder import AppInstallerBuilder


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
