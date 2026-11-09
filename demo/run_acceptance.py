"""Run an acceptance script with a process-tree timeout and preserve its exit code."""
import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", choices=["quick_acceptance", "real_world_acceptance", "test_p0", "test_p1", "test_p3", "test_p4"])
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    script = Path(__file__).with_name(args.script + ".py")
    process = subprocess.Popen(  # noqa: S603 - fixed script choices and current interpreter
        [sys.executable, "-u", str(script)], stdin=subprocess.DEVNULL,
        start_new_session=os.name != "nt",
    )
    try:
        return process.wait(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print(f"Acceptance timed out after {args.timeout}s; terminating its process tree", file=sys.stderr)
        if os.name == "nt":
            taskkill = str(Path(os.environ["SystemRoot"]) / "System32" / "taskkill.exe")
            subprocess.run([taskkill, "/PID", str(process.pid), "/T", "/F"],  # noqa: S603 - owned PID only
                           stdin=subprocess.DEVNULL, timeout=15, check=False)
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)
        return 124


if __name__ == "__main__":
    sys.exit(main())
