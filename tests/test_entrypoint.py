import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_robot as cli
from benchmark import offline_io
from simulator import Source, SyntheticSimulator


class EntrypointTests(unittest.TestCase):
    def test_no_connection_without_explicit_flag(self):
        with patch.object(
            sys, "argv", ["run_robot.py", "--problem", "4", "--case-code", "offline"]
        ):
            with patch.object(cli, "xin_jiekou") as transport:
                self.assertEqual(cli.main(), 0)
                transport.assert_not_called()

    def test_default_entrypoint_runs_selected_fast_and_records_completion(self):
        world = SyntheticSimulator(
            [Source(c, (0.0, 0.0), 1000.0) for c in range(1, 11)]
        )
        transport = offline_io(world.transport)
        with tempfile.TemporaryDirectory() as folder:
            argv = [
                "run_robot.py",
                "--problem",
                "3",
                "--case-code",
                "offline",
                "--connect",
                "--output",
                folder,
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(cli, "xin_jiekou", return_value=transport),
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(cli.main(), 0)
            output = next(Path(folder).iterdir())
            metadata = json.loads((output / "metadata.json").read_text())
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(metadata["policy_revision"], "20260912-shared-service-r4")
            self.assertIsNone(summary["error"])
            self.assertEqual(len(world.cleared), 10)
            self.assertFalse(world.active)
