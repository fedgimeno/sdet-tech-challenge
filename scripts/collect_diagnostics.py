"""Save container logs and runtime state for investigating failures.

Used locally and in CI, with output saved under reports/diagnostics by default.
"""

import argparse
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", default="sdet-api")
    parser.add_argument("--output", default="reports/diagnostics")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    commands = {
        "container-logs.txt": ["docker", "logs", "--timestamps", args.container],
        "container-state.txt": [
            "docker",
            "inspect",
            "--format",
            "status={{.State.Status}} exit_code={{.State.ExitCode}} image={{.Image}}",
            args.container,
        ],
    }
    for filename, command in commands.items():
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=15)
            text = f"exit_code={result.returncode}\n{result.stdout}{result.stderr}"
        except (OSError, subprocess.TimeoutExpired) as error:
            text = f"Diagnostic command failed: {type(error).__name__}\n"
        (output / filename).write_text(text)
    print(f"Diagnostics saved to {output}")


if __name__ == "__main__":
    main()
