# RHEL Patch Automation

Automated patching and compliance reporting for RHEL 8/9 fleets, built with Ansible.

Handles staged rollouts across environments, pre/post-patch validation, safe reboot
orchestration, rollback data capture, and consolidated HTML/Markdown compliance
reports — the kind of workflow a patching engineer runs every month, codified so
it's repeatable, auditable, and safe to run unattended.

[![CI](https://github.com/<your-username>/rhel-patch-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-username>/rhel-patch-automation/actions/workflows/ci.yml)
![Ansible](https://img.shields.io/badge/ansible-%3E%3D2.15-blue)
![Platform](https://img.shields.io/badge/platform-RHEL%208%20%2F%209-red)
![License](https://img.shields.io/badge/license-MIT-green)

## Why this exists

Patching a handful of servers by hand is easy. Patching a fleet safely — in
batches, with rollback data captured, reboots handled correctly, and a report
you can hand to an auditor — is a different problem. This project is my
solution to that problem, structured the way I'd run it in production.

## Features

- **Staged/canary rollouts** — patches roll out in batches (`serial`) with a
  configurable failure threshold, so a bad patch stops the run before it hits
  the whole fleet.
- **Security-only or full patching** — toggle between patching everything or
  only CVE-tagged security errata, per environment.
- **Pre-patch state capture** — records installed package versions and,
  optionally, takes an LVM snapshot before patching, so you have something to
  roll back to.
- **Reboot orchestration** — detects whether a reboot is actually required
  (`needs-restarting`) instead of blindly rebooting every host, waits for SSH
  to come back, and re-validates services afterward.
- **Post-patch validation** — checks that critical services are active and
  the host is reachable before marking a host "done."
- **Compliance reporting** — aggregates per-host results into a single
  Markdown + HTML report: patches applied, security errata remaining,
  subscription/Insights status, and failures, with a custom filter plugin for
  parsing `dnf updateinfo` output into structured data.
- **Rollback playbook** — uses `dnf history undo` against the captured
  transaction ID if a patch run needs to be reversed.
- **CI-tested** — Molecule scenario runs the role against a Rocky Linux 9
  container on every push (see [Note on RHEL vs Rocky/Alma](#note-on-rhel-vs-rockyalma-in-ci)).

## Architecture

```
                     ┌─────────────────────┐
                     │   Control Node       │
                     │  (Ansible + this repo)│
                     └──────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
        ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
        │  Batch 1    │     │  Batch 2   │     │  Batch N   │
        │ (25% hosts) │     │(25% hosts) │     │            │
        └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
              │                 │                 │
      pre-check → snapshot → patch → reboot? → post-check
              │                 │                 │
              └────────────────┬┴─────────────────┘
                                │
                     ┌──────────▼───────────┐
                     │ Compliance Report     │
                     │ (Markdown + HTML)     │
                     └───────────────────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the detailed flow and
[docs/PATCHING_STRATEGY.md](docs/PATCHING_STRATEGY.md) for the reasoning
behind batching, reboot handling, and rollback.

## Requirements

- Ansible-core >= 2.15 on the control node
- Target hosts: RHEL 8 or RHEL 9, registered with Red Hat Subscription
  Manager (or Simple Content Access), SSH access with a sudo-capable user
- `python3-dnf` and `yum-utils` (for `needs-restarting`) on target hosts —
  installed automatically as a pre-check if missing
- Collections listed in `requirements.yml`

## Quick start

```bash
git clone https://github.com/<your-username>/rhel-patch-automation.git
cd rhel-patch-automation

# Install required collections
ansible-galaxy collection install -r requirements.yml

# Point inventories/production/hosts.yml at your real hosts, then:

# 1. Dry run — see what would be patched, change nothing
ansible-playbook -i inventories/production playbooks/patch.yml --check --diff

# 2. Security-only patch run, staged rollout
ansible-playbook -i inventories/production playbooks/patch.yml \
  -e "patch_security_only=true"

# 3. Full patch run including reboots
ansible-playbook -i inventories/production playbooks/patch.yml \
  -e "patch_reboot_allowed=true"

# 4. Compliance report only (no changes made)
ansible-playbook -i inventories/production playbooks/compliance-report.yml
```

Reports are written to `reports/` by default —
`reports/compliance_report_<timestamp>.md` and the `.html` equivalent.

## Repository layout

```
.
├── ansible.cfg
├── requirements.yml
├── inventories/
│   ├── production/            # example inventory + group_vars
│   └── staging/
├── playbooks/
│   ├── site.yml                # patch + compliance report, end to end
│   ├── patch.yml                # patching only
│   ├── compliance-report.yml    # reporting only, read-only
│   └── rollback.yml             # dnf history undo using captured transaction id
├── roles/
│   ├── patch_management/        # pre-checks, snapshot, patch, reboot, post-checks
│   └── compliance_reporting/    # gather + aggregate + render reports
└── docs/
    ├── ARCHITECTURE.md
    ├── PATCHING_STRATEGY.md
    └── VARIABLES.md
```

Full variable reference: [docs/VARIABLES.md](docs/VARIABLES.md).

## Note on RHEL vs Rocky/Alma in CI

RHEL container images require a Red Hat subscription and aren't available for
public CI. The Molecule scenario tests against `rockylinux/rockylinux:9`,
which is binary-compatible with RHEL 9 and uses the same `dnf` package
manager, so the role logic is exercised faithfully. Anything RHEL-specific
(subscription-manager status, Insights) is checked with `when` guards that
skip gracefully on non-RHEL platforms during CI, and are documented as such
in the tasks.

## Safety notes

- Always run with `--check --diff` against a new environment before a real
  run.
- `patch_reboot_allowed` defaults to `false` — you opt in to reboots
  explicitly.
- The rollback playbook only undoes the specific `dnf` transaction captured
  during the patch run; it is not a full system restore.

## License

MIT — see [LICENSE](LICENSE).
