"""
Sandbox executor — runs agent-submitted Python code in a subprocess with:
  - a hard wall-clock timeout
  - a temp working directory (cleaned up after each run)
  - no network access (relies on OS-level restrictions in the container)
  - captured stdout/stderr
"""

import os
import subprocess
import tempfile
import textwrap
from typing import Tuple


TIMEOUT_SECONDS = 30


def run_agent_code(
    code: str,
    data_files: dict,  # {filename: csv_string}
    output_filename: str = "output.csv",
    timeout: int = TIMEOUT_SECONDS,
) -> Tuple[bool, str, str]:
    """
    Execute agent code in a temp directory.

    Returns:
        (success: bool, output_csv: str, error_trace: str)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write data files
        data_dir = os.path.join(tmpdir, "data")
        os.makedirs(data_dir)
        for fname, content in data_files.items():
            with open(os.path.join(data_dir, fname), "w") as f:
                f.write(content)

        # Write agent code
        script_path = os.path.join(tmpdir, "solution.py")
        with open(script_path, "w") as f:
            f.write(code)

        # Run with timeout
        try:
            result = subprocess.run(
                ["python", "solution.py"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
            )
        except subprocess.TimeoutExpired:
            return False, "", f"TimeoutError: script exceeded {timeout}s"
        except Exception as e:
            return False, "", f"ExecutionError: {e}"

        if result.returncode != 0:
            error = (result.stderr or result.stdout or "Unknown error")[:2000]
            return False, "", error

        # Read output
        output_path = os.path.join(tmpdir, output_filename)
        if not os.path.exists(output_path):
            return False, "", "OutputError: output.csv not found — did the script call df.to_csv('output.csv')?"

        with open(output_path, "r") as f:
            output_csv = f.read()

        return True, output_csv, ""
