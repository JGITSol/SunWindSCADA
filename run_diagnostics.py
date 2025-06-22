#!/usr/bin/env python3
"""
SunWindSCADA Project Diagnostics Tool

This script runs various diagnostics on the SunWindSCADA project, including:
- Code formatting checks (Black, isort)
- Python linting (Flake8)
- Static type checking (mypy)
- Security scanning (Bandit)
- Dependency vulnerability checking (Safety)
- Django system checks
- Running tests (Django backend and Reflex frontend)

Usage:
    python run_diagnostics.py [options]

Options:
    --all                Run all diagnostics (default)
    --format             Run only formatting checks (Black, isort)
    --lint               Run only linting checks (Flake8)
    --types              Run only type checking (mypy)
    --security           Run only security scanning (Bandit, Safety)
    --django-checks      Run only Django system checks
    --tests              Run only tests
    --backend-tests      Run only Django backend tests
    --frontend-tests     Run only Reflex frontend tests
    --verbose            Show detailed output
    --fix                Fix formatting issues where possible
    --help               Show this help message
"""

import argparse
import os
import platform
import subprocess
import sys
import traceback
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple


# ANSI color codes for terminal output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class DiagnosticResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    WARNING = "WARNING"


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
DJANGO_ROOT = PROJECT_ROOT / "django_backend"
REFLEX_ROOT = PROJECT_ROOT / "reflex_frontend"

# Global verbose flag
VERBOSE = False


def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    capture_output: bool = True,
    step: str = "",
    env: dict = None,
) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, and stderr. Always print output if verbose or on error."""
    if VERBOSE or step:
        print(
            f"\n{Colors.OKBLUE}Running command [{step}]: {' '.join(cmd)}{Colors.ENDC}"
        )
    try:
        pass
        result = subprocess.run(
            [c for c in cmd if c],
            cwd=cwd or PROJECT_ROOT,
            capture_output=capture_output,
            text=True,
            check=False,
            env=env,
        )
        if VERBOSE or result.returncode != 0:
            print(f"{Colors.BOLD}Return code:{Colors.ENDC} {result.returncode}")
            if result.stdout is not None:
                print(f"{Colors.BOLD}Stdout:{Colors.ENDC}\n{result.stdout.strip()}")
            else:
                print(f"{Colors.BOLD}Stdout:{Colors.ENDC} <None>")
            if result.stderr is not None:
                print(f"{Colors.BOLD}Stderr:{Colors.ENDC}\n{result.stderr.strip()}")
            else:
                print(f"{Colors.BOLD}Stderr:{Colors.ENDC} <None>")
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        print(f"{Colors.FAIL}Exception running command [{step}]: {e}{Colors.ENDC}")
        traceback.print_exc()
        return 1, "", str(e)


def print_result(name: str, result: DiagnosticResult, message: str = "") -> None:
    result_colors = {
        DiagnosticResult.PASS: Colors.OKGREEN,
        DiagnosticResult.FAIL: Colors.FAIL,
        DiagnosticResult.SKIP: Colors.WARNING,
        DiagnosticResult.WARNING: Colors.WARNING,
    }
    color = result_colors.get(result, "")
    print(f"{Colors.BOLD}{name}{Colors.ENDC}: {color}{result.value}{Colors.ENDC}")
    if message:
        print(f"  {message}")
    print()


def check_dependencies() -> DiagnosticResult:
    print(f"{Colors.HEADER}Checking Python dependencies...{Colors.ENDC}")
    try:
        pass
        returncode, stdout, stderr = run_command(
            ["pip", "install", "-q", "-r", "requirements-dev.txt"],
            step="pip install main dev reqs",
        )
        if returncode != 0:
            print_result(
                "Development Dependencies",
                DiagnosticResult.FAIL,
                f"Failed to install development dependencies: {stderr}",
            )
            return DiagnosticResult.FAIL
        returncode, stdout, stderr = run_command(
            ["pip", "install", "-q", "-r", "requirements-dev.txt"],
            cwd=REFLEX_ROOT,
            step="pip install reflex dev reqs",
        )
        if returncode != 0:
            print_result(
                "Reflex Development Dependencies",
                DiagnosticResult.FAIL,
                f"Failed to install Reflex development dependencies: {stderr}",
            )
            return DiagnosticResult.FAIL
        return DiagnosticResult.PASS
    except Exception as e:
        print(f"{Colors.FAIL}Exception in check_dependencies: {e}{Colors.ENDC}")
        traceback.print_exc()
        return DiagnosticResult.FAIL


def check_black(fix: bool = False) -> DiagnosticResult:
    print(f"{Colors.HEADER}Checking Black formatting...{Colors.ENDC}")
    cmd = ["black", ".", "--check" if not fix else ""]
    if not VERBOSE:
        cmd.append("--quiet")
    returncode, stdout, stderr = run_command(cmd, step="black")
    if returncode == 0:
        return DiagnosticResult.PASS
    elif fix:
        return DiagnosticResult.WARNING
    else:
        return DiagnosticResult.FAIL


def check_isort(fix: bool = False) -> DiagnosticResult:
    print(f"{Colors.HEADER}Checking isort imports...{Colors.ENDC}")
    cmd = ["isort", ".", "--check-only" if not fix else ""]
    if not VERBOSE:
        cmd.append("--quiet")
    returncode, stdout, stderr = run_command(cmd, step="isort")
    if returncode == 0:
        return DiagnosticResult.PASS
    elif fix:
        return DiagnosticResult.WARNING
    else:
        return DiagnosticResult.FAIL


def check_flake8() -> DiagnosticResult:
    print(f"{Colors.HEADER}Running Flake8...{Colors.ENDC}")
    cmd = ["flake8", "."]
    returncode, stdout, stderr = run_command(cmd, step="flake8")
    if returncode == 0:
        return DiagnosticResult.PASS
    else:
        return DiagnosticResult.FAIL


def check_mypy() -> DiagnosticResult:
    print(f"{Colors.HEADER}Running mypy...{Colors.ENDC}")
    cmd = ["mypy", "django_backend", "reflex_frontend"]
    returncode, stdout, stderr = run_command(cmd, step="mypy")
    if returncode == 0:
        return DiagnosticResult.PASS
    else:
        return DiagnosticResult.FAIL


def check_bandit() -> DiagnosticResult:
    print(f"{Colors.HEADER}Running Bandit security scan...{Colors.ENDC}")
    # Only scan project source directories, not the root or venvs
    source_dirs = ["django_backend", "reflex_frontend"]
    existing_dirs = [d for d in source_dirs if (Path(__file__).parent / d).is_dir()]
    if not existing_dirs:
        print("No source directories found to scan with Bandit. Skipping.")
        return DiagnosticResult.SKIP
    bandit_cmd = [
        sys.executable,
        "-m",
        "bandit",
        "-r",
        *existing_dirs,
        "-x",
        "tests,reflex_frontend/.web/node_modules",
        "-v",
        "--format",
        "json",
    ]
    bandit_env = os.environ.copy()
    bandit_env["PYTHONIOENCODING"] = "utf-8"
    bandit_returncode, bandit_stdout, bandit_stderr = run_command(
        bandit_cmd, step="bandit", env=bandit_env
    )
    if bandit_returncode == 0:
        print("Bandit: PASS (no issues found in project code)")
        return DiagnosticResult.PASS
    else:
        print("Bandit: FAIL (issues found in project code)")
        return DiagnosticResult.FAIL


def check_safety() -> DiagnosticResult:
    print(f"{Colors.HEADER}Running Safety vulnerability check...{Colors.ENDC}")
    safety_cmd = [
        sys.executable,
        "-m",
        "safety",
        "scan",
        "--file",
        "requirements.txt",
    ]
    safety_returncode, safety_stdout, safety_stderr = run_command(
        safety_cmd, step="safety (main)"
    )
    cmd_reflex = ["safety", "check", "--file", str(REFLEX_ROOT / "requirements.txt")]
    if not VERBOSE:
        cmd_reflex.append("--quiet")
    returncode_reflex, stdout_reflex, stderr_reflex = run_command(
        cmd_reflex, step="safety (reflex)"
    )
    if safety_returncode == 0 and returncode_reflex == 0:
        return DiagnosticResult.PASS
    else:
        return DiagnosticResult.WARNING


def check_django_system() -> DiagnosticResult:
    print(f"{Colors.HEADER}Running Django system checks...{Colors.ENDC}")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        pass

    except ImportError:
        print(
            f"{Colors.WARNING}Django not installed, skipping Django system checks.{Colors.ENDC}"
        )
        return DiagnosticResult.SKIP
    cmd = [sys.executable, "manage.py", "check"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    returncode, stdout, stderr = run_command(
        cmd, cwd=DJANGO_ROOT, env=env, step="django check"
    )
    if returncode == 0:
        cmd_migrations = [
            "python",
            "manage.py",
            "makemigrations",
            "--check",
            "--dry-run",
        ]
        returncode_migrations, stdout_migrations, stderr_migrations = run_command(
            cmd_migrations,
            cwd=DJANGO_ROOT,
            step="django makemigrations --check --dry-run",
        )
        if returncode_migrations == 0:
            return DiagnosticResult.PASS
        else:
            return DiagnosticResult.WARNING
    else:
        return DiagnosticResult.FAIL


def run_django_tests() -> DiagnosticResult:
    print(f"{Colors.HEADER}Running Django backend tests...{Colors.ENDC}")
    cmd = [sys.executable, "manage.py", "test"]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    returncode, stdout, stderr = run_command(
        cmd, cwd=DJANGO_ROOT, env=env, step="django test"
    )
    if returncode == 0:
        return DiagnosticResult.PASS
    else:
        return DiagnosticResult.FAIL


def run_reflex_tests() -> DiagnosticResult:
    print(f"{Colors.HEADER}Running Reflex frontend tests...{Colors.ENDC}")
    try:
        pass

    except ImportError:
        print(
            f"{Colors.WARNING}pytest not installed, skipping Reflex frontend tests.{Colors.ENDC}"
        )
        return DiagnosticResult.SKIP
    cmd = [sys.executable, "-m", "pytest", "scripts/test_app_smoke.py"]
    returncode, stdout, stderr = run_command(
        cmd, cwd=REFLEX_ROOT, step="pytest reflex smoke"
    )
    if returncode == 0:
        return DiagnosticResult.PASS
    else:
        return DiagnosticResult.FAIL


def print_env_info():
    print(
        f"{Colors.BOLD}Python version:{Colors.ENDC} {platform.python_version()} ({sys.executable})"
    )
    print(f"{Colors.BOLD}Platform:{Colors.ENDC} {platform.platform()}")
    print(f"{Colors.BOLD}Working directory:{Colors.ENDC} {os.getcwd()}")
    print(f"{Colors.BOLD}PROJECT_ROOT:{Colors.ENDC} {PROJECT_ROOT}")


def main() -> int:
    global VERBOSE
    try:
        pass
        parser = argparse.ArgumentParser(
            description="Run SunWindSCADA project diagnostics"
        )
        parser.add_argument(
            "--all", action="store_true", help="Run all diagnostics (default)"
        )
        parser.add_argument(
            "--format", action="store_true", help="Run only formatting checks"
        )
        parser.add_argument(
            "--lint", action="store_true", help="Run only linting checks"
        )
        parser.add_argument(
            "--types", action="store_true", help="Run only type checking"
        )
        parser.add_argument(
            "--security", action="store_true", help="Run only security scanning"
        )
        parser.add_argument(
            "--django-checks", action="store_true", help="Run only Django system checks"
        )
        parser.add_argument("--tests", action="store_true", help="Run only tests")
        parser.add_argument(
            "--backend-tests", action="store_true", help="Run only Django backend tests"
        )
        parser.add_argument(
            "--frontend-tests",
            action="store_true",
            help="Run only Reflex frontend tests",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Show detailed output"
        )
        parser.add_argument(
            "--fix", action="store_true", help="Fix formatting issues where possible"
        )
        args = parser.parse_args()
        VERBOSE = args.verbose
        print_env_info()
        run_all = (
            not args.format
            and not args.lint
            and not args.types
            and not args.security
            and not args.django_checks
            and not args.tests
            and not args.backend_tests
            and not args.frontend_tests
        )
        if run_all or args.all:
            print(
                f"{Colors.HEADER}{Colors.BOLD}Running all SunWindSCADA diagnostics...{Colors.ENDC}\n"
            )
        else:
            print(
                f"{Colors.HEADER}{Colors.BOLD}Running selected SunWindSCADA diagnostics...{Colors.ENDC}\n"
            )
        print(f"{Colors.BOLD}Checking dependencies...{Colors.ENDC}")
        deps_result = check_dependencies()
        print_result("Dependencies", deps_result)
        results = {}
        if run_all or args.all or args.format:
            results["Black"] = check_black(fix=args.fix)
            print_result("Black", results["Black"])
            results["isort"] = check_isort(fix=args.fix)
            print_result("isort", results["isort"])
        if run_all or args.all or args.lint:
            results["Flake8"] = check_flake8()
            print_result("Flake8", results["Flake8"])
        if run_all or args.all or args.types:
            results["mypy"] = check_mypy()
            print_result("mypy", results["mypy"])
        if run_all or args.all or args.security:
            results["Bandit"] = check_bandit()
            print_result("Bandit", results["Bandit"])
            results["Safety"] = check_safety()
            print_result("Safety", results["Safety"])
        if run_all or args.all or args.django_checks:
            results["Django System"] = check_django_system()
            print_result("Django System", results["Django System"])
        if run_all or args.all or args.tests or args.backend_tests:
            results["Django Tests"] = run_django_tests()
            print_result("Django Tests", results["Django Tests"])
        if run_all or args.all or args.tests or args.frontend_tests:
            results["Reflex Tests"] = run_reflex_tests()
            print_result("Reflex Tests", results["Reflex Tests"])
        print(f"{Colors.HEADER}{Colors.BOLD}Diagnostics Summary:{Colors.ENDC}")
        failures = sum(
            1 for result in results.values() if result == DiagnosticResult.FAIL
        )
        warnings = sum(
            1 for result in results.values() if result == DiagnosticResult.WARNING
        )
        passes = sum(
            1 for result in results.values() if result == DiagnosticResult.PASS
        )
        skips = sum(1 for result in results.values() if result == DiagnosticResult.SKIP)
        print(f"Total checks: {len(results)}")
        print(f"{Colors.OKGREEN}Passed: {passes}{Colors.ENDC}")
        print(f"{Colors.WARNING}Warnings: {warnings}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {failures}{Colors.ENDC}")
        print(f"{Colors.WARNING}Skipped: {skips}{Colors.ENDC}")
        if failures > 0:
            print(
                f"\n{Colors.FAIL}Some diagnostics failed. Please fix the issues and run again.{Colors.ENDC}"
            )
            return 1
        elif warnings > 0:
            print(
                f"\n{Colors.WARNING}Some diagnostics generated warnings. Please review them.{Colors.ENDC}"
            )
            return 0
        else:
            print(f"\n{Colors.OKGREEN}All diagnostics passed!{Colors.ENDC}")
            return 0
    except Exception:
        print(f"{Colors.FAIL}FATAL ERROR in diagnostics script:{Colors.ENDC}")
        traceback.print_exc()
        print(
            f"{Colors.FAIL}Diagnostics aborted due to an unhandled exception.{Colors.ENDC}"
        )
        return 2


if __name__ == "__main__":
    sys.exit(main())
