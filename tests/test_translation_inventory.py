import importlib.util
import re
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture(scope="module")
def installer_builder_module():
    source_path = (
        Path(__file__).resolve().parents[1] / "installer_builder" / "__init__.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_installer_builder_translation_inventory_test", source_path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_valid_application_inventory_preserves_package_destination(
    installer_builder_module, tmp_path, monkeypatch
):
    catalog_directory = tmp_path / "locale" / "de" / "LC_MESSAGES"
    catalog_directory.mkdir(parents=True)
    source_catalog = catalog_directory / "Test App.po"
    compiled_catalog = catalog_directory / "Test App.mo"
    source_catalog.write_bytes(b"source")
    compiled_catalog.write_bytes(b"compiled")
    monkeypatch.chdir(tmp_path)
    builder = installer_builder_module.InstallerBuilder(
        name="Test App", has_translations=True
    )

    assert list(builder.find_application_language_data()) == [
        (str(Path("locale") / "de" / "LC_MESSAGES"), [str(compiled_catalog.relative_to(tmp_path))])
    ]


def test_legacy_lowercase_messages_layout_is_valid(
    installer_builder_module, tmp_path, monkeypatch
):
    catalog_directory = tmp_path / "locale" / "ar" / "lc_messages"
    catalog_directory.mkdir(parents=True)
    source_catalog = catalog_directory / "Test App.po"
    compiled_catalog = catalog_directory / "Test App.mo"
    source_catalog.write_bytes(b"source")
    compiled_catalog.write_bytes(b"compiled")
    monkeypatch.chdir(tmp_path)
    builder = installer_builder_module.InstallerBuilder(
        name="Test App", has_translations=True
    )

    assert list(builder.find_application_language_data()) == [
        (str(Path("locale") / "ar" / "lc_messages"), [str(compiled_catalog.relative_to(tmp_path))])
    ]


def test_missing_compiled_catalog_fails(
    installer_builder_module, tmp_path, monkeypatch
):
    catalog_directory = tmp_path / "locale" / "de" / "LC_MESSAGES"
    catalog_directory.mkdir(parents=True)
    (catalog_directory / "Test App.po").write_bytes(b"source")
    monkeypatch.chdir(tmp_path)
    builder = installer_builder_module.InstallerBuilder(
        name="Test App", has_translations=True
    )
    expected_mo_path = Path("locale") / "de" / "LC_MESSAGES" / "Test App.mo"
    expected_message = "Compiled translation catalog not found: %s" % expected_mo_path

    with pytest.raises(FileNotFoundError, match=re.escape(expected_message)):
        list(builder.find_application_language_data())


def test_missing_source_catalog_fails(
    installer_builder_module, tmp_path, monkeypatch
):
    catalog_directory = tmp_path / "locale" / "de" / "LC_MESSAGES"
    catalog_directory.mkdir(parents=True)
    (catalog_directory / "Test App.mo").write_bytes(b"compiled")
    monkeypatch.chdir(tmp_path)
    builder = installer_builder_module.InstallerBuilder(
        name="Test App", has_translations=True
    )
    expected_po_path = Path("locale") / "de" / "LC_MESSAGES" / "Test App.po"
    expected_message = "Source translation catalog not found: %s" % expected_po_path

    with pytest.raises(FileNotFoundError, match=re.escape(expected_message)):
        list(builder.find_application_language_data())


def test_mismatched_application_domain_fails(
    installer_builder_module, tmp_path, monkeypatch
):
    catalog_directory = tmp_path / "locale" / "de" / "LC_MESSAGES"
    catalog_directory.mkdir(parents=True)
    (catalog_directory / "Wrong Domain.po").write_bytes(b"source")
    (catalog_directory / "Wrong Domain.mo").write_bytes(b"compiled")
    monkeypatch.chdir(tmp_path)
    builder = installer_builder_module.InstallerBuilder(
        name="Test App", has_translations=True
    )
    expected_message = (
        "Translation domain mismatch in %s: expected 'Test App', found 'Wrong Domain'"
        % (Path("locale") / "de" / "LC_MESSAGES")
    )

    with pytest.raises(ValueError, match=re.escape(expected_message)):
        list(builder.find_application_language_data())


def test_invalid_catalog_layout_fails(
    installer_builder_module, tmp_path, monkeypatch
):
    application_root = tmp_path / "application" / "locale"
    application_root.mkdir(parents=True)
    application_source = application_root / "Test App.po"
    application_compiled = application_root / "Test App.mo"
    application_source.write_bytes(b"source")
    application_compiled.write_bytes(b"compiled")
    monkeypatch.chdir(tmp_path / "application")
    builder = installer_builder_module.InstallerBuilder(
        name="Test App", has_translations=True
    )
    application_message = (
        "Invalid translation catalog layout: %s; expected "
        "<locale>/(LC_MESSAGES|lc_messages)/<domain>.po or .mo"
        % (Path("locale") / "Test App.mo")
    )

    with pytest.raises(ValueError, match=re.escape(application_message)):
        list(builder.find_application_language_data())

    package_root = tmp_path / "package" / "locale"
    package_directory = package_root / "de" / "Lc_MESSAGES"
    package_directory.mkdir(parents=True)
    package_catalog = package_directory / "wxstd.mo"
    package_catalog.write_bytes(b"compiled")
    package_message = (
        "Invalid translation catalog layout: %s; expected "
        "<locale>/(LC_MESSAGES|lc_messages)/<domain>.mo" % package_catalog
    )

    with pytest.raises(ValueError, match=re.escape(package_message)):
        builder._validate_translation_inventory(str(package_root))


def test_application_appledouble_catalog_is_rejected(
    installer_builder_module, tmp_path, monkeypatch
):
    catalog_directory = tmp_path / "locale" / "de" / "LC_MESSAGES"
    catalog_directory.mkdir(parents=True)
    (catalog_directory / "Test App.po").write_bytes(b"source")
    (catalog_directory / "Test App.mo").write_bytes(b"compiled")
    metadata_catalog = catalog_directory / "._Test App.mo"
    metadata_catalog.write_bytes(b"metadata")
    monkeypatch.chdir(tmp_path)
    builder = installer_builder_module.InstallerBuilder(
        name="Test App", has_translations=True
    )
    expected_message = (
        "Invalid translation catalog metadata: %s; "
        "AppleDouble files are not translation catalogs"
        % metadata_catalog.relative_to(tmp_path)
    )

    with pytest.raises(ValueError, match=re.escape(expected_message)):
        list(builder.find_application_language_data())


def test_compiled_only_localized_package_domains_are_recorded_and_included(
    installer_builder_module, tmp_path, monkeypatch, capsys
):
    package_root = tmp_path / "synthetic_package"
    catalog_directory = package_root / "locale" / "fr" / "LC_MESSAGES"
    catalog_directory.mkdir(parents=True)
    compiled_catalog = catalog_directory / "package_domain.mo"
    compiled_catalog.write_bytes(b"compiled")
    assert not compiled_catalog.with_suffix(".po").exists()
    package_module = SimpleNamespace(__path__=[str(package_root)])
    monkeypatch.setattr(
        installer_builder_module.importlib,
        "import_module",
        lambda package: package_module,
    )
    builder = installer_builder_module.InstallerBuilder(
        name="Test App", localized_packages=["synthetic_package"]
    )
    monkeypatch.setattr(builder, "find_babel_datafiles", lambda: ())

    assert builder.find_datafiles() == [
        (str(Path("locale") / "fr" / "LC_MESSAGES"), [str(compiled_catalog)])
    ]
    assert "package_domain" in capsys.readouterr().out


def test_localized_package_appledouble_catalog_fails(
    installer_builder_module, tmp_path, monkeypatch
):
    package_root = tmp_path / "synthetic_package"
    catalog_directory = package_root / "locale" / "fr" / "LC_MESSAGES"
    catalog_directory.mkdir(parents=True)
    (catalog_directory / "wxstd.mo").write_bytes(b"compiled")
    metadata_catalog = catalog_directory / "._wxstd.mo"
    metadata_catalog.write_bytes(b"metadata")
    package_module = SimpleNamespace(__path__=[str(package_root)])
    monkeypatch.setattr(
        installer_builder_module.importlib,
        "import_module",
        lambda package: package_module,
    )
    builder = installer_builder_module.InstallerBuilder(
        name="Test App", localized_packages=["synthetic_package"]
    )
    expected_message = (
        "Invalid translation catalog metadata: %s; "
        "AppleDouble files are not translation catalogs" % metadata_catalog
    )

    with pytest.raises(ValueError, match=re.escape(expected_message)):
        builder.find_datafiles()


def test_empty_requested_inventory_fails(
    installer_builder_module, tmp_path, monkeypatch
):
    application_root = tmp_path / "application"
    (application_root / "locale").mkdir(parents=True)
    monkeypatch.chdir(application_root)
    builder = installer_builder_module.InstallerBuilder(
        name="Test App", has_translations=True
    )
    application_message = "No translation catalogs found in: locale"

    with pytest.raises(FileNotFoundError, match=re.escape(application_message)):
        list(builder.find_application_language_data())

    package_root = tmp_path / "package" / "locale"
    package_root.mkdir(parents=True)
    package_message = "No compiled translation catalogs found in: %s" % package_root

    with pytest.raises(FileNotFoundError, match=re.escape(package_message)):
        builder._validate_translation_inventory(str(package_root))
