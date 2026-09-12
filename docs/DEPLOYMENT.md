# Raspberry Pi systemd deployment

The tracked unit runs only the implemented Watcher ingress. It exposes the
bridge on `0.0.0.0:8834`; it does not expose or call Teacher Core. A future
Teacher adapter must continue to reach Teacher Core through a localhost URL.

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

The installer uses the invoking sudo user as the unprivileged runtime user,
creates `.venv`, installs this checkout, renders the unit with the absolute
checkout path, and creates the external environment file only when absent. It
never displays environment-file contents and never overwrites existing values.
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

## Reboot UAT (must run on the real Pi)

1. Record the Pi model/RAM, Pi OS, Python version, Watcher model/firmware,
   teacher-edge SHA, network topology, and test time without recording secrets.
2. Confirm the service and localhost health check are healthy, then reboot with
   `sudo reboot` without manually starting Uvicorn afterward.
3. After the Pi returns, confirm `systemctl is-enabled teacher-edge` reports
   `enabled`, `systemctl is-active teacher-edge` reports `active`, and `/health`
   returns the healthy JSON.
4. Power the Watcher independently, trigger human detection, and verify the
   Watcher sends its HTTP event to `http://PI_LAN_IP:8834`; confirm authenticated
   ingress returns `200 OK` and sanitized metadata appears in the Pi journal.
5. Stop the process with `sudo systemctl kill -s SIGKILL teacher-edge`, wait at
   least five seconds, and verify systemd returns it to `active` and `/health`
   succeeds. Record the observed result and revision in `docs/UAT.md`.

The deployment definition is locally verifiable, but reboot persistence and
Watcher connectivity are not proven until these steps pass on the target Pi.
