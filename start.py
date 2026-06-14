#!/usr/bin/env python3
"""Start the full TriReason development stack."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = ROOT / "venv"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"

POSTGRES_HOST = "127.0.0.1"
POSTGRES_PORT = 5432
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379


def print_step(message: str) -> None:
    print(f"\n==> {message}")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def get_venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def find_npm() -> str:
    candidates = ["npm.cmd", "npm"] if os.name == "nt" else ["npm"]
    for candidate in candidates:
        if shutil.which(candidate):
            return candidate
    fail("Node.js/NPM not found in PATH. Install Node.js 18+ and retry.")
    raise AssertionError("unreachable")


def detect_docker_compose() -> list[str] | None:
    docker = shutil.which("docker")
    if docker:
        result = subprocess.run(
            [docker, "compose", "version"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            return [docker, "compose"]

    docker_compose = shutil.which("docker-compose")
    if docker_compose:
        return [docker_compose]

    return None


def load_dotenv_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        cleaned = value.strip().strip("'").strip('"')
        values[key.strip()] = cleaned

    return values


def ensure_env_file() -> None:
    if ENV_FILE.exists():
        return
    if not ENV_EXAMPLE.exists():
        fail("Missing .env and .env.example.")
    ENV_FILE.write_text(ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    print_step("Created .env from .env.example")


def build_runtime_env(overrides: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.update(load_dotenv_values(ENV_FILE))
    if overrides:
        env.update(overrides)
    return env


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> None:
    printable = " ".join(command)
    location = str(cwd or ROOT)
    print(f"[run] {printable} (cwd={location})")
    subprocess.run(command, cwd=cwd or ROOT, check=True, env=env)


def is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0


def wait_for_port(host: str, port: int, *, timeout: int = 60, service_name: str) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                print(f"[ok] {service_name} is reachable on {host}:{port}")
                return
        time.sleep(1)
    fail(f"{service_name} did not become reachable on {host}:{port} within {timeout} seconds.")


def parse_database_url(database_url: str) -> tuple[str, int]:
    parsed = urlsplit(database_url)
    if parsed.hostname is None:
        fail(f"Invalid DATABASE_URL host: {database_url}")
    port = parsed.port or 5432
    return parsed.hostname, port


def replace_database_port(database_url: str, new_port: int) -> str:
    parsed = urlsplit(database_url)
    hostname = parsed.hostname or "localhost"
    username = parsed.username
    password = parsed.password

    auth = ""
    if username is not None:
        auth = quote(unquote(username), safe="")
        if password is not None:
            auth += f":{quote(unquote(password), safe='')}"
        auth += "@"

    if ":" in hostname and not hostname.startswith("["):
        host_part = f"[{hostname}]"
    else:
        host_part = hostname

    netloc = f"{auth}{host_part}:{new_port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def find_available_port(start_port: int, *, attempts: int = 20) -> int:
    for offset in range(attempts):
        candidate = start_port + offset
        if not is_port_open(POSTGRES_HOST, candidate):
            return candidate
    fail(f"No available PostgreSQL host port found starting from {start_port}.")
    raise AssertionError("unreachable")


def can_connect_to_database(
    venv_python: Path,
    runtime_env: dict[str, str],
) -> tuple[bool, str]:
    check_script = """
import asyncio
import os
import sys

import asyncpg
from urllib.parse import urlsplit, urlunsplit


async def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    parsed = urlsplit(database_url)
    if parsed.scheme.startswith("postgresql+"):
        safe_url = urlunsplit(("postgresql", parsed.netloc, parsed.path, parsed.query, parsed.fragment))
    else:
        safe_url = database_url
    connection = await asyncpg.connect(safe_url)
    await connection.close()


try:
    asyncio.run(main())
except Exception as exc:
    print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
    raise
""".strip()

    result = subprocess.run(
        [str(venv_python), "-c", check_script],
        cwd=ROOT,
        env=runtime_env,
        capture_output=True,
        text=True,
        check=False,
    )
    details = (result.stderr or result.stdout).strip()
    return result.returncode == 0, details


def start_support_services(
    compose: list[str],
    *,
    runtime_env: dict[str, str],
    start_db: bool,
) -> None:
    services = ["redis"]
    if start_db:
        services.insert(0, "db")

    print_step(f"Starting {' and '.join(services)} via Docker Compose")
    run_command([*compose, "up", "-d", *services], env=runtime_env)

    if start_db:
        host, port = parse_database_url(runtime_env["DATABASE_URL"])
        wait_for_port(host, port, timeout=60, service_name="PostgreSQL")
    wait_for_port(REDIS_HOST, REDIS_PORT, timeout=30, service_name="Redis")


def ensure_database_runtime(
    venv_python: Path,
    runtime_env: dict[str, str],
) -> tuple[dict[str, str], bool]:
    database_url = runtime_env.get("DATABASE_URL")
    if not database_url:
        fail("DATABASE_URL is not configured.")

    host, port = parse_database_url(database_url)
    compose = detect_docker_compose()

    can_connect, details = can_connect_to_database(venv_python, runtime_env)
    if can_connect:
        print_step(f"Using reachable PostgreSQL from DATABASE_URL ({host}:{port})")
        return runtime_env, False

    local_host = host in {"localhost", "127.0.0.1"}
    if compose is None or not local_host:
        fail(
            "Cannot connect to PostgreSQL using DATABASE_URL. "
            f"Last error: {details or 'unknown error'}"
        )

    chosen_port = port
    if is_port_open(host, port):
        chosen_port = find_available_port(port + 1)
        runtime_env = dict(runtime_env)
        runtime_env["DATABASE_URL"] = replace_database_port(database_url, chosen_port)
        runtime_env["POSTGRES_HOST_PORT"] = str(chosen_port)
        print_step(
            f"Port {port} is already serving a different PostgreSQL instance; "
            f"TriReason will start its own database on port {chosen_port}"
        )
    else:
        runtime_env = dict(runtime_env)
        runtime_env["POSTGRES_HOST_PORT"] = str(port)

    start_support_services(compose, runtime_env=runtime_env, start_db=True)

    can_connect, details = can_connect_to_database(venv_python, runtime_env)
    if not can_connect:
        fail(
            "TriReason PostgreSQL started but the application still cannot connect. "
            f"Last error: {details or 'unknown error'}"
        )

    return runtime_env, True


def run_migrations(venv_python: Path, *, runtime_env: dict[str, str]) -> None:
    print_step("Running database migrations")
    run_command([str(venv_python), "-m", "alembic", "upgrade", "head"], env=runtime_env)


def stream_output(name: str, process: subprocess.Popen[str]) -> None:
    assert process.stdout is not None
    for line in process.stdout:
        print(f"[{name}] {line}", end="")


def launch_process(
    name: str,
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> tuple[subprocess.Popen[str], threading.Thread]:
    print(f"[start] {name}: {' '.join(command)} (cwd={cwd})")
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    thread = threading.Thread(target=stream_output, args=(name, process), daemon=True)
    thread.start()
    return process, thread


def terminate_process(name: str, process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    print(f"[stop] Terminating {name}")
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        print(f"[stop] Killing {name}")
        process.kill()
        process.wait(timeout=5)


def monitor_processes(processes: dict[str, subprocess.Popen[str]]) -> int:
    try:
        while True:
            for name, process in processes.items():
                exit_code = process.poll()
                if exit_code is not None:
                    print_step(f"{name} exited with code {exit_code}")
                    return exit_code
            time.sleep(1)
    except KeyboardInterrupt:
        print_step("Shutdown requested")
        return 0


def main() -> None:
    venv_python = get_venv_python()
    if not venv_python.exists():
        fail("Virtual environment not found. Run `python install.py` first.")

    ensure_env_file()
    runtime_env = build_runtime_env()
    runtime_env, started_db = ensure_database_runtime(venv_python, runtime_env)

    compose = detect_docker_compose()
    if compose is not None and not started_db:
        start_support_services(compose, runtime_env=runtime_env, start_db=False)

    run_migrations(venv_python, runtime_env=runtime_env)

    npm = find_npm()

    print_step("Starting backend and frontend")
    backend, _backend_thread = launch_process(
        "backend",
        [str(venv_python), "-m", "trireason"],
        cwd=ROOT,
        env=runtime_env,
    )
    frontend, _frontend_thread = launch_process(
        "frontend",
        [npm, "run", "dev"],
        cwd=FRONTEND_DIR,
        env=runtime_env,
    )

    processes = {"backend": backend, "frontend": frontend}
    exit_code = monitor_processes(processes)

    for name, process in processes.items():
        terminate_process(name, process)

    if exit_code != 0:
        raise SystemExit(exit_code)

    print_step("TriReason stopped")
    print("PostgreSQL and Redis may still be running if they were started with Docker Compose.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        fail(f"Command failed with exit code {exc.returncode}")
