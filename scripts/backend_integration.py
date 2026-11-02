"""Verify a built backend image with offline probes and synthetic PostgreSQL.

Requires an explicit local Docker socket and preloaded images. Creates only
labelled temporary containers and an internal network, with no host mounts or
published ports. Uses no cloud credentials, external database, or existing data.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import sys
import time
import uuid

from check_dependency_audit import read_lock
from local_recovery import POSTGRES_IMAGE

SCRIPTS = Path(__file__).resolve().parent
LABEL = "org.story-filler.runtime-check"
UNCERTAIN_CREATE_ATTEMPTS = 5

SEED = """
import os
import subprocess
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'maori_story_project.settings'
subprocess.run(
    [sys.executable, 'manage.py', 'migrate', '--noinput'],
    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
import django
django.setup()
from core.models import AppConfig, BlankLink, Paragraph, Story, Word
story = Story.objects.create(title='Runtime verification')
word = Word.objects.create(maori_word='wai', english_translation='water')
story.word_bank.add(word)
paragraph = Paragraph.objects.create(
    story=story, order=1, text='Kia ora __BLANK_water__'
)
BlankLink.objects.create(paragraph=paragraph, placeholder='__BLANK_water__', word=word)
AppConfig.objects.create()
print('PASS: migrated and seeded a new synthetic PostgreSQL database')
"""

HTTP_CHECK = """
import hashlib
import os
from pathlib import Path
import urllib.error
import urllib.request
assert os.getuid() != 0
base = 'http://127.0.0.1:8000'
check_api(base, timeout=5, attempts=1)
for endpoint in ('/api/stories/', '/api/stories/1/', '/api/config/'):
    request = urllib.request.Request(base + endpoint, data=b'{}', method='POST')
    try:
        urllib.request.urlopen(request, timeout=5)
    except urllib.error.HTTPError as error:
        assert error.code == 405
        error.close()
    else:
        raise AssertionError('Public API unexpectedly allowed POST')
asset = Path('/app/staticfiles/admin/css/base.css')
with urllib.request.urlopen(base + '/static/admin/css/base.css', timeout=5) as response:
    assert response.status == 200
    assert response.headers.get_content_type() == 'text/css'
    expected = hashlib.sha256(asset.read_bytes()).digest()
    assert hashlib.sha256(response.read()).digest() == expected
try:
    urllib.request.urlopen(base + '/static/runtime-check-missing.css', timeout=5)
except urllib.error.HTTPError as error:
    assert error.code == 404
    error.close()
else:
    raise AssertionError('Missing static resource did not return 404')
"""


WORKER_CHECK = """
from pathlib import Path
assert b'gunicorn' in Path('/proc/1/cmdline').read_bytes()
children = Path('/proc/1/task/1/children').read_text().split()
assert len(children) == 3, 'Expected three Gunicorn workers'
for pid in children:
    assert b'gunicorn' in Path('/proc', pid, 'cmdline').read_bytes()
"""
APPLICATION_READY = WORKER_CHECK + """
import urllib.request
urllib.request.urlopen('http://127.0.0.1:8000/api/stories/', timeout=3).close()
"""
HTTP_CHECK += WORKER_CHECK + """
print('PASS: default Gunicorn command, three workers, read-only API and static assets')
"""


@contextmanager
def protect_cleanup():
    """Finish bounded cleanup after interruption; restore the caller's handlers."""
    signals = (signal.SIGTERM, signal.SIGINT)
    previous = {number: signal.getsignal(number) for number in signals}
    try:
        for number in signals:
            signal.signal(number, signal.SIG_IGN)
        yield
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class Verification:
    def __init__(self, host, image):
        require(
            host.startswith("unix:///") and not any(c in host for c in "\x00\n\r?#"),
            "Use an explicit local Docker Unix socket",
        )
        require(
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/@:-]*", image),
            "Use a local image name or digest",
        )
        self.prefix = ["docker", "--host", host]
        self.environment = {
            name: os.environ[name]
            for name in ("PATH", "HOME", "TMPDIR", "DOCKER_CONFIG")
            if name in os.environ
        }
        self.operation = uuid.uuid4().hex
        self.network = f"runtime-check-{self.operation}"
        self.containers = {}
        self.network_created = False
        self.network_id = None
        self.secret_values = []
        self.image = (
            self.command(
                ["image", "inspect", "--format", "{{.Id}}", image], "image availability"
            )
            .stdout.decode()
            .strip()
        )
        self.command(
            ["image", "inspect", "--format", "{{.Id}}", POSTGRES_IMAGE],
            "PostgreSQL image availability",
        )

    def diagnostics(self, result):
        # Only synthetic secrets are ever supplied to these containers. Replace
        # their complete values before truncation, so a tail cannot reveal part.
        text = result.stderr.decode("utf-8", errors="replace")
        for secret in self.secret_values:
            text = text.replace(secret, "[redacted]")
        return f"exit {result.returncode}: {text[-1024:].strip()}"

    def command(self, arguments, stage, *, data=None, timeout=120, check=True):
        try:
            # Fixed internal Docker commands; validated socket/image stay separate
            # argv values. No shell interprets them, so shell quoting is incorrect.
            # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
            result = subprocess.run(
                [*self.prefix, *arguments],
                input=data,
                capture_output=True,
                env=self.environment,
                timeout=timeout,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RuntimeError(f"{stage} did not complete") from error
        if check:
            require(
                result.returncode == 0, f"{stage} failed ({self.diagnostics(result)})"
            )
        return result

    def create(self, suffix, image, options, arguments=()):
        name = f"{self.network}-{suffix}"
        exists = self.command(
            ["container", "inspect", "--format", "{{.Id}}", name],
            "name availability",
            check=False,
        )
        require(exists.returncode != 0, "Temporary container name already exists")
        # Track before create: even a client timeout must not orphan a resource.
        self.containers[name] = None
        result = self.command(
            [
                "create",
                "--pull=never",
                "--name",
                name,
                "--label",
                f"{LABEL}={self.operation}",
                *options,
                image,
                *arguments,
            ],
            f"{suffix} container creation",
        )
        identifier = result.stdout.decode().strip()
        require(
            re.fullmatch(r"[a-f0-9]{64}", identifier),
            "Docker returned an invalid container ID",
        )
        self.containers[name] = identifier
        return identifier

    def run_python(self, suffix, source, options, arguments=()):
        container = self.create(
            suffix,
            self.image,
            ["--interactive", "--entrypoint", "python", *options],
            ["-", *arguments],
        )
        result = self.command(
            ["start", "--attach", "--interactive", container],
            f"{suffix} checks",
            data=source.encode(),
        )
        print(result.stdout.decode().strip(), flush=True)

    def wait_ready(self, container, arguments, stage):
        deadline = time.monotonic() + 60
        last_failure = "no readiness response"
        while time.monotonic() < deadline:
            running = self.command(
                ["inspect", "--format", "{{.State.Running}}", container], stage
            ).stdout.strip()
            require(running == b"true", f"{stage}: container exited; {last_failure}")
            result = self.command(
                ["exec", container, *arguments], stage, timeout=10, check=False
            )
            if result.returncode == 0:
                return
            last_failure = self.diagnostics(result)
            time.sleep(0.5)
        raise RuntimeError(f"{stage}: readiness deadline exceeded ({last_failure})")

    def verify(self):
        lock = SCRIPTS.parent / "backend" / "requirements.txt"
        arguments = [
            "--expected-packages-json",
            json.dumps(read_lock(lock)),
            "--lock-sha256",
            hashlib.sha256(lock.read_bytes()).hexdigest(),
        ]
        self.run_python(
            "offline",
            (SCRIPTS / "check_backend_runtime.py").read_text(),
            ["--network", "none"],
            arguments,
        )

        exists = self.command(
            ["network", "inspect", "--format", "{{.Id}}", self.network],
            "network name availability",
            check=False,
        )
        require(exists.returncode != 0, "Temporary network name already exists")
        self.network_created = True
        network = self.command(
            [
                "network",
                "create",
                "--internal",
                "--label",
                f"{LABEL}={self.operation}",
                self.network,
            ],
            "internal network creation",
        )
        self.network_id = network.stdout.decode().strip()
        require(re.fullmatch(r"[a-f0-9]{64}", self.network_id), "Invalid network ID")
        password = secrets.token_urlsafe(32)
        secret_key = secrets.token_urlsafe(48)
        self.secret_values.extend([password, secret_key])
        database = self.create(
            "database",
            POSTGRES_IMAGE,
            [
                "--network",
                self.network,
                "--network-alias",
                "database",
                "--tmpfs",
                "/var/lib/postgresql/data:rw",
                "--env",
                "POSTGRES_USER=runtime_test",
                "--env",
                "POSTGRES_DB=runtime_test",
                "--env",
                f"POSTGRES_PASSWORD={password}",
            ],
        )
        self.command(["start", database], "PostgreSQL startup")
        # The official entrypoint briefly runs a Unix-socket-only server during
        # initialization. TCP readiness selects the final server.
        self.wait_ready(
            database,
            [
                "pg_isready",
                "-h",
                "127.0.0.1",
                "-U",
                "runtime_test",
                "-d",
                "runtime_test",
            ],
            "PostgreSQL readiness",
        )
        options = [
            "--network",
            self.network,
            "--env",
            f"SECRET_KEY={secret_key}",
            "--env",
            (
                f"DATABASE_URL=postgres://runtime_test:{password}"
                "@database:5432/runtime_test"
            ),
            "--env",
            "USE_GCS=false",
            "--env",
            "DEBUG=false",
        ]
        self.run_python("seed", SEED, options)
        backend = self.create("application", self.image, options)
        started = time.monotonic()
        self.command(["start", backend], "default application startup")
        self.wait_ready(
            backend,
            [
                "python",
                "-c",
                APPLICATION_READY,
            ],
            "application readiness",
        )
        print(
            f"PASS: application ready after {time.monotonic() - started:.2f}s "
            "(local observation, not a performance target)"
        )
        smoke = (SCRIPTS / "smoke-check.py").read_text()
        source = (
            'namespace = {"__name__": "runtime_smoke"}\n'
            f"exec({smoke!r}, namespace)\n"
            'check_api = namespace["check_api"]\n' + HTTP_CHECK
        )
        result = self.command(
            ["exec", "--interactive", backend, "python", "-"],
            "HTTP checks",
            data=source.encode(),
        )
        print(result.stdout.decode().strip(), flush=True)
        self.command(
            ["stop", "--time", "15", backend],
            "graceful application shutdown",
            timeout=25,
        )
        result = self.command(
            ["inspect", "--format", "{{json .State}}", backend], "shutdown verification"
        )
        state = json.loads(result.stdout)
        require(
            not state["Running"] and state["ExitCode"] == 0 and not state["OOMKilled"],
            "Application did not stop gracefully",
        )
        print("PASS: Gunicorn handled SIGTERM and exited normally")

    def remove_owned(self, kind, name, identifier):
        label_field = ".Config.Labels" if kind == "container" else ".Labels"
        projection = '{"id":{{json .Id}},"labels":{{json ' + label_field + "}}}"
        attempts = UNCERTAIN_CREATE_ATTEMPTS if identifier is None else 1
        for attempt in range(attempts):
            result = self.command(
                [kind, "inspect", "--format", projection, name],
                "cleanup ownership check",
                timeout=10,
                check=False,
            )
            if result.returncode == 0:
                break
            listing = ["ps", "--all"] if kind == "container" else ["network", "ls"]
            if identifier is None:
                listing += ["--filter", f"label={LABEL}={self.operation}"]
            names = (
                self.command(
                    [
                        *listing,
                        "--format",
                        "{{.Names}}" if kind == "container" else "{{.Name}}",
                    ],
                    "cleanup inventory",
                    timeout=10,
                )
                .stdout.decode()
                .splitlines()
            )
            if identifier is not None:
                require(name not in names, "Could not inspect a tracked resource")
                return
            # A client timeout does not cancel a daemon create. Look again for a
            # late result; even repeated absence cannot prove that it finished.
            if attempt + 1 == attempts:
                raise RuntimeError(
                    f"Create outcome remains uncertain for {name}; "
                    f"check Docker resources labelled {LABEL}={self.operation}. "
                    "Cleanup is not confirmed."
                )
            time.sleep(1)
        metadata = json.loads(result.stdout)
        require(
            isinstance(metadata, dict)
            and isinstance(metadata.get("labels"), dict)
            and metadata["labels"].get(LABEL) == self.operation
            and isinstance(metadata.get("id"), str)
            and re.fullmatch(r"[a-f0-9]{64}", metadata["id"])
            and (identifier is None or metadata["id"] == identifier),
            "Resource ownership changed; cleanup refused",
        )
        arguments = (
            ["rm", "--force", "--volumes"] if kind == "container" else ["network", "rm"]
        )
        self.command([*arguments, metadata["id"]], "owned resource cleanup", timeout=30)

    def cleanup(self):
        resources = [
            ("container", name, identifier)
            for name, identifier in reversed(list(self.containers.items()))
        ]
        if self.network_created:
            resources.append(("network", self.network, self.network_id))
        with protect_cleanup():
            failures = []
            for resource in resources:
                try:
                    self.remove_owned(*resource)
                except (OSError, ValueError, RuntimeError) as error:
                    failures.append(str(error))
            require(not failures, "; ".join(failures))
            print("PASS: temporary containers and network removed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker-host", required=True)
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    verification = Verification(args.docker_host, args.image)
    # SIGTERM still runs finally, rather than leaving synthetic resources behind.
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        verification.verify()
    finally:
        verification.cleanup()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Backend image verification failed: {error}", file=sys.stderr)
        sys.exit(1)
