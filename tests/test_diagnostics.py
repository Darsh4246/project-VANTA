import os
import pytest
from vanta.tools.cpu import get_cpu_data
from vanta.tools.memory import get_memory_data
from vanta.tools.storage import get_storage_data
from vanta.tools.network import get_network_data
from vanta.diagnostics.health import calculate_health_scores
from vanta.database.history import init_db, log_session, get_history
from vanta.diagnostics.engine import run_rule_based_diagnostics

def test_cpu_data_collection():
    data = get_cpu_data()
    assert "cpu_percent" in data
    assert "logical_cores" in data
    assert "per_cpu_percent" in data
    assert data["logical_cores"] >= 1

def test_memory_data_collection():
    data = get_memory_data()
    assert "ram_percent" in data
    assert "ram_total_gb" in data
    assert "ram_used_gb" in data
    assert data["ram_total_gb"] > 0

def test_storage_data_collection():
    data = get_storage_data()
    assert "partitions" in data
    assert "warnings" in data
    if data["partitions"]:
        p = data["partitions"][0]
        assert "fstype" in p
        assert p["total_gb"] > 0

def test_network_data_collection():
    data = get_network_data()
    assert "local_ip" in data
    assert "gateway" in data
    assert data["internet_reachable"] in (True, False)

def test_health_scoring():
    scores = calculate_health_scores()
    assert "CPU" in scores
    assert "Memory" in scores
    assert "Storage" in scores
    assert "Network" in scores
    assert "OVERALL" in scores
    assert 0 <= scores["OVERALL"] <= 100

def test_sqlite_history(tmp_path):
    # Set DB path env to a temp file for test isolation
    os.environ["WORKSPACE_DIR"] = str(tmp_path)
    # Re-import config/db variables so they load the new env
    from importlib import reload
    import vanta.config
    import vanta.database.history
    reload(vanta.config)
    reload(vanta.database.history)
    
    vanta.database.history.init_db()
    
    # Log session
    vanta.database.history.log_session(
        request="test scan",
        tools_used=["cpu_diagnostics"],
        findings=[{"title": "test finding", "category": "CPU", "severity": "WARNING"}],
        recommendations="test recommend",
        action_approved=False,
        action_completed=False,
        verification="done"
    )
    
    hist = vanta.database.history.get_history()
    assert len(hist) >= 1
    assert hist[0]["request"] == "test scan"
    assert "cpu_diagnostics" in hist[0]["tools"]

def test_rule_based_diagnostics_report():
    report = run_rule_based_diagnostics()
    assert report.overall_health_score >= 0
    assert isinstance(report.findings, list)
    assert report.categories_scores
