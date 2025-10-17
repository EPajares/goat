from pathlib import Path

from goatlib.io.remote_source.wfs_reader import WFSReader


def test_get_layers_parses_names() -> None:
    """Ensure get_layers() correctly extracts layer names."""
    reader = WFSReader()
    layers = reader.get_layers(
        "https://geoservices.bayern.de/wfs/v1/ogc_atkis_basisdlm.cgi?SERVICE=WFS&request=GetCapabilities"
    )
    assert "adv:AX_Wald" in layers
    assert "adv:AX_Strasse" in layers


def test_build_datasource_creates_xml(tmp_path: Path) -> None:
    """Ensure build_datasource() writes a valid XML file."""
    reader = WFSReader()
    url = "https://geo.example/wfs?SERVICE=WFS&VERSION=2.0.0"
    xml_path = reader.build_datasource(url)
    content = xml_path.read_text(encoding="utf-8")
    assert xml_path.exists()
    assert "<OGRWFSDataSource>" in content
    assert url in content


def test_can_handle() -> None:
    """Detect only WFS URLs."""
    reader = WFSReader()
    assert reader.can_handle("https://x/service=WFS")
    assert not reader.can_handle("https://x/service=WMS")
