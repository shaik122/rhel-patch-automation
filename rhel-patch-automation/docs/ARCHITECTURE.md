# Architecture

## Flow (per host, per batch)

1. **Pre-checks** (`patch_management/tasks/pre_checks.yml`)
   Installs `yum-utils` if missing, checks subscription status, verifies
   free disk space on `/`, confirms the host is reachable.

2. **State capture / snapshot** (`patch_management/tasks/snapshot.yml`)
   Records the current `dnf` transaction id and full installed package
   manifest to the control node (`reports/state/<host>_pre_patch_state.yml`).
   Optionally takes an LVM snapshot of the root volume if
   `patch_lvm_snapshot_enabled` is true and there's free space in the VG.

3. **Check updates** (`patch_management/tasks/check_updates.yml`)
   Dry-run (`check_mode: true`) against `dnf` to see what's pending, plus a
   parsed list of security errata. No changes are made in this step.

4. **Apply patches** (`patch_management/tasks/apply_patches.yml`)
   Applies either security-only or full updates depending on
   `patch_security_only`. Records the post-patch transaction id (this is
   what `rollback.yml` targets). Determines whether a reboot is required via
   `needs-restarting -r` and conditionally notifies the reboot handler.

5. **Reboot** (`patch_management/tasks/reboot.yml`, only if
   `patch_reboot_allowed` and a reboot is required)
   Flushes the reboot handler immediately (rather than at end-of-play),
   waits for SSH to come back, re-gathers facts.

6. **Post-checks** (`patch_management/tasks/post_checks.yml`)
   Confirms the host is reachable, checks that `patch_critical_services` are
   active, restarts any that aren't, and builds a `patch_summary` fact
   consumed by the compliance report.

7. **Compliance report** (`compliance_reporting` role)
   Each host gathers its own compliance data (pending updates, parsed
   security advisories, subscription/Insights status) into a
   `compliance_record` fact. A single aggregation task
   (`delegate_to: localhost, run_once: true`) pulls every host's
   `compliance_record` (and `patch_summary`, if a patch run preceded it) out
   of `hostvars`, and renders both a Markdown and an HTML report.

## Why batching (`serial`) instead of patching everything at once

`playbooks/patch.yml` runs against `rhel8_batch1`, then `rhel8_batch2`, etc.
(inventory groups), using `serial: "25%"` and `max_fail_percentage: 20`. If a
patch breaks something on the first batch, Ansible stops before touching the
rest of the fleet. Database hosts run with `serial: 1` — one at a time, no
parallelism, because a failed DB host is a much bigger problem than a failed
web node.

## Why reboot detection instead of always rebooting

Not every patch requires a reboot (userspace package updates usually don't).
`needs-restarting -r` (from `yum-utils`) returns exit code 1 only when a
reboot is actually needed — kernel, glibc, systemd, etc. were updated.
Rebooting unconditionally would cause unnecessary downtime; skipping reboots
entirely would leave hosts running vulnerable code in memory even after
patching. This role does neither — it reboots only when necessary, and only
when the operator has explicitly opted in via `patch_reboot_allowed`.

## Why capture state before every run, even without LVM

`dnf history undo <id>` is the most common way to reverse a bad patch, but
it only works if you know which transaction to undo. Recording the
transaction id before and after every run means `rollback.yml` never has to
guess — it reads the exact id from the state file captured during that run.
