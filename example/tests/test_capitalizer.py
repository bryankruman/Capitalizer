import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from capitalizer import capitalize_name


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("quicksilver", "Quicksilver"),
        ("silverlakedesign", "SilverLakeDesign"),
        ("darkstoneforge.com", "DarkStoneForge.com"),
        ("northwindtravel.org", "NorthWindTravel.org"),
        ("notepilot", "NotePilot"),
        ("meetingflow", "MeetingFlow"),
        ("packora", "Packora"),
        ("cleancarton", "CleanCarton"),
        ("savvio", "Savvio"),
        ("brightbalance", "BrightBalance"),
        ("campaignbuilder", "CampaignBuilder"),
    ],
)
def test_capitalize_name_examples(raw: str, expected: str) -> None:
    assert capitalize_name(raw) == expected


def test_cli_outputs_expected_lines(tmp_path: Path) -> None:
    """Smoke-test the CLI using a subset of examples."""
    project_root = Path(__file__).resolve().parents[1]
    script = project_root / "capitalizer.py"

    examples = [
        ("quicksilver", "Quicksilver"),
        ("darkstoneforge.com", "DarkStoneForge.com"),
        ("packora", "Packora"),
    ]

    names = [raw for raw, _ in examples]
    expected_lines = [expected for _, expected in examples]

    completed = subprocess.run(
        [sys.executable, str(script), *names],
        check=True,
        capture_output=True,
        text=True,
    )

    output_lines = [line for line in completed.stdout.splitlines() if line.strip()]
    assert output_lines == expected_lines

