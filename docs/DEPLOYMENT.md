# Raspberry Pi systemd deployment

The tracked edge unit exposes the bridge on `0.0.0.0:8834` for authenticated Watcher notification, synthetic text and stock PTT transport. The M2 text adapter calls the pinned Teacher Core over localhost; the M3.0 PTT endpoint returns a deterministic test response and does not yet send audio through Teacher STT or conversation. See [STATUS](STATUS.md) for the current milestone boundary and [INTEGRATION_CONTRACT](INTEGRATION_CONTRACT.md) for endpoint contracts.

## Teacher Core baseline (pinned upstream)

Teacher Core is installed from `Lilian0414/teacher` at exactly
`c1b6a03c1894df2d2b8994cf3b9a124ea8b381e5`. At that revision it requires
Python 3.12+, provides `companion-core`, uses `requirements.lock`, reads
`COMPANION_HOST`/`COMPANION_PORT`, and exposes `GET /health`. Its default
database path is not suitable for Linux, so this deployment always supplies
`COMPANION_DATABASE_URL`.

Clone and pin Teacher in a permanent location as the runtime user, then install
it (the installer rejects any other commit):

Install `git`, Python 3.12 or newer, and that interpreter's `venv` support. On
a Raspberry Pi OS/Debian release whose default `python3` is new enough:

```bash
sudo apt-get install -y python3 python3-venv git
python3 -c 'import sys; assert sys.version_info >= (3, 12)'
git clone https://github.com/Lilian0414/teacher.git "$HOME/teacher"
git -C "$HOME/teacher" checkout --detach c1b6a03c1894df2d2b8994cf3b9a124ea8b381e5
sudo ./deploy/raspberry-pi/install-teacher-core.sh "$HOME/teacher"
sudoedit /etc/teacher/teacher.env
sudo chmod 600 /etc/teacher/teacher.env
sudo systemctl enable --now teacher-core
curl --fail --silent http://127.0.0.1:8000/health
```

The installer uses `python3` by default and validates its version. If a newer
interpreter is installed under a versioned or custom name, select it explicitly
while preserving the setting through `sudo`, for example:

```bash
sudo env TEACHER_PYTHON=python3.13 \
  ./deploy/raspberry-pi/install-teacher-core.sh "$HOME/teacher"
```

The dependency lock is installed first and the checkout is then installed
editable with `--no-deps`. The checkout `.venv` is created as the invoking sudo
user. `/var/lib/teacher` is persistent and runtime-user-owned;
`/etc/teacher/teacher.env` is external, root-owned, mode `0600`, preserved by
reinstall, and never printed. The template keeps embeddings disabled and uses
`sqlite:////var/lib/teacher/companion.sqlite3`.

The unit runs `alembic upgrade head` with the configured environment before
every start, making initial migration and upgrades repeatable, then starts
`companion-core`. It binds to `127.0.0.1:8000`, restarts on failure, and starts
at boot when enabled. Do not expose Core to the LAN; the implemented M2 text bridge client calls it over localhost.

### Operate, update, and remove Teacher Core

```bash
systemctl status teacher-core --no-pager
journalctl -u teacher-core -n 100 --no-pager
curl --fail --silent http://127.0.0.1:8000/health
sudo systemctl restart teacher-core

git -C "$HOME/teacher" fetch origin
git -C "$HOME/teacher" checkout --detach c1b6a03c1894df2d2b8994cf3b9a124ea8b381e5
sudo ./deploy/raspberry-pi/install-teacher-core.sh "$HOME/teacher"
sudo systemctl restart teacher-core

sudo systemctl disable --now teacher-core
sudo rm -f /etc/systemd/system/teacher-core.service
sudo systemctl daemon-reload
```

The removal commands retain database and secrets for recovery. For destructive
uninstall, separately remove `/etc/teacher`, `/var/lib/teacher`, and the Teacher
checkout only after backing up or explicitly discarding SQLite state.

### Teacher Core reboot and provider UAT (hardware passed; reusable procedure)

1. Record Pi model/RAM, Pi OS, `${TEACHER_PYTHON:-python3} --version`, Teacher SHA from
   `git -C "$HOME/teacher" rev-parse HEAD`, and teacher-edge SHA.
2. Record a known conversation ID (not private content), run `sudo reboot`, and
   do not manually start either service.
3. Verify `systemctl is-enabled teacher-core` is `enabled`,
   `systemctl is-active teacher-core` is `active`, `ss -ltnp` shows port 8000
   only on `127.0.0.1`, and the localhost health request succeeds.
4. Confirm the recorded conversation remains available after the reboot.
5. On the Pi, inspect `http://127.0.0.1:8000/openapi.json` and use its pinned
   schemas to make one real `POST /v1/conversations`, followed by one
   `POST /v1/conversations/{conversation_id}/messages`. Record sanitized HTTP
   statuses, IDs, and assistant success to prove Groq and persistence. This is
   direct Core UAT, **not** an edge TeacherClient.
6. Run `sudo systemctl kill -s SIGKILL teacher-core`, wait five seconds, and
   confirm the service returns to active and health succeeds.

Expected results are an active unit, successful health response, localhost-only
listener, durable database after reboot, and one persisted real conversation
turn. These results passed on real Pi hardware for M1.2; see
[`UAT.md`](UAT.md) for the sanitized evidence. Keep this procedure for
verification of later revisions. This procedure exercises Core directly; the M2 edge-to-Teacher round-trip is separately recorded in [UAT.md](UAT.md).

## Install

Prerequisites are a Raspberry Pi with Python 3.11+, `python3-venv`, and this
repository cloned to a permanent path. From the repository root, run:

```bash
sudo apt-get install -y python3-venv
sudo ./deploy/raspberry-pi/install.sh
sudoedit /etc/teacher-edge/teacher-edge.env
sudo chmod 600 /etc/teacher-edge/teacher-edge.env
sudo systemctl enable --now teacher-edge
```

The installer uses the invoking sudo user as the unprivileged runtime user. It
creates `.venv` and installs the checkout as that user, so runtime files in the
repository are not left owned by root. Root access is limited to repairing an
older `.venv` ownership, writing `/etc`, and managing the systemd unit. The
installer renders the unit with the absolute checkout path and creates the
external environment file only when absent. It never displays environment-file
contents and never overwrites existing values.
Run it as the intended runtime user via `sudo`; do not invoke it from a root
login unless the `pi` fallback user exists.

Replace both placeholder values in the environment file. Generate a token on
the Pi (for example, `openssl rand -hex 32`) and configure that exact token in
the Watcher. Use a comma-separated EUI list when allowing multiple devices.
The file is root-owned and mode `0600`; secrets do not belong in the checkout,
shell history, unit, status output, or logs.

## Operate and verify

```bash
systemctl status teacher-edge --no-pager
journalctl -u teacher-edge -n 100 --no-pager
curl --fail --silent http://127.0.0.1:8834/health
sudo systemctl restart teacher-edge
```

A healthy service is `active (running)`, enabled, and the health request returns
`{"status":"healthy"}`. `Restart=on-failure` restarts an unexpectedly failed
process after five seconds. Normal event logs contain normalized metadata, not
the Authorization header.

## Update

After reviewing and pulling a new revision into the same checkout:

```bash
git pull --ff-only
sudo ./deploy/raspberry-pi/install.sh
sudo systemctl restart teacher-edge
curl --fail --silent http://127.0.0.1:8834/health
```

The installer preserves the external environment file. If the checkout moves,
rerun it from the new path so the unit is rendered with that location.

## Recovery and uninstall

Inspect `systemctl status` and the journal first. Correct configuration with
`sudoedit /etc/teacher-edge/teacher-edge.env`, then restart. To remove the
service while deliberately retaining secrets for recovery:

```bash
sudo systemctl disable --now teacher-edge
sudo rm -f /etc/systemd/system/teacher-edge.service
sudo systemctl daemon-reload
```

To fully uninstall, also remove `/etc/teacher-edge` explicitly. Remove the
checkout separately only after deciding whether any local operational evidence
must be sanitized or retained.

## Edge reboot UAT (hardware passed; reusable procedure)

This procedure verifies **Pi reboot persistence only**. Before starting, the
Watcher must already be configured with the `http alarm` runtime taskflow and
must remain powered on throughout the test. Do not reboot or power-cycle the
Watcher as part of this procedure: current Watcher behavior resets its runtime
taskflow from `http alarm` to `sensecraft alarm` after a Watcher reboot.
Persisting or reprovisioning the Watcher taskflow is a known limitation and is
outside the M1.1 systemd deployment scope.

1. Record the Pi model/RAM, Pi OS, Python version, Watcher model/firmware,
   teacher-edge SHA, network topology, and test time without recording secrets.
2. Confirm that the powered-on Watcher is using the `http alarm` taskflow and
   that the service and localhost health check are healthy. Reboot **only the
   Pi** with `sudo reboot`, without manually starting Uvicorn afterward.
3. After the Pi returns, confirm `systemctl is-enabled teacher-edge` reports
   `enabled`, `systemctl is-active teacher-edge` reports `active`, and `/health`
   returns the healthy JSON.
4. Without rebooting the Watcher, trigger human detection and verify it sends
   its HTTP event to `http://PI_LAN_IP:8834`; confirm authenticated ingress
   returns `200 OK` and sanitized metadata appears in the Pi journal.
5. Stop the process with `sudo systemctl kill -s SIGKILL teacher-edge`, wait at
   least five seconds, and verify systemd returns it to `active` and `/health`
   succeeds. Record the observed result and revision in `docs/UAT.md`.

This procedure passed on a real Pi at teacher-edge main revision
`a5dc33140c15ced0a6e66ff3817f49a8fef7bbcc`: after reboot the unit was enabled,
active, and healthy, and a powered-on real Watcher retaining `http alarm` sent a
new authenticated human-detection event that returned `200 OK`. See
[`UAT.md`](UAT.md) for the sanitized evidence and its recorded limitations.
