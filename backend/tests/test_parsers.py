from pathlib import Path

from ariadne.parsers.cti_parser import parse_cti_report
from ariadne.parsers.iac_parser import parse_docker_compose
from ariadne.parsers.sbom_parser import parse_cyclonedx_sbom

DATA = Path(__file__).resolve().parent.parent / "data"


def test_parse_cti_report_extracts_log4shell_fields() -> None:
    text = (DATA / "sample_cti" / "log4shell.txt").read_text()

    cti = parse_cti_report(text, source_report="log4shell.txt")

    assert cti.cve_id == "CVE-2021-44228"
    assert cti.target_software == "log4j-core"
    assert "2.14.1" in cti.affected_versions


def test_parse_docker_compose_flags_published_ports_as_internet_facing() -> None:
    nodes, edges = parse_docker_compose(DATA / "mock_topology" / "docker-compose.yml")

    nginx = next(n for n in nodes if n.id == "nginx")
    auth_api = next(n for n in nodes if n.id == "auth-api")

    assert nginx.internet_facing is True
    assert auth_api.internet_facing is False
    assert any(e.source == "nginx" and e.target == "auth-api" for e in edges)
    assert any(e.source == "auth-api" and e.target == "auth-db" for e in edges)


def test_parse_cyclonedx_sbom_links_components_to_owning_service() -> None:
    nodes, edges = parse_cyclonedx_sbom(
        DATA / "mock_topology" / "auth-api-sbom.json", service_id="auth-api"
    )

    assert any(n.id == "log4j-core@2.14.1" for n in nodes)
    assert any(e.source == "auth-api" and e.target == "log4j-core@2.14.1" for e in edges)
