# Patching Strategy

This doc explains the operational reasoning behind the defaults in this
repo — useful if you're adapting it for your own environment, or explaining
the design in an interview/portfolio context.

## Security-only vs full patching

Production defaults to `patch_security_only: true`. The reasoning:

- Security errata are pre-vetted by Red Hat as fixing a specific CVE — the
  risk of *not* applying them is well understood and often compliance-driven
  (PCI-DSS, SOC 2, internal audit).
- Full patching pulls in everything, including feature/bugfix updates that
  haven't been through the same change-control process. Those are lower
  urgency and higher blast-radius, so they're better scheduled deliberately
  (a maintenance window, tested in staging first) rather than applied on
  every automated run.

Staging flips this — `patch_security_only: false` — because staging exists
to catch exactly the kind of regression a full update might introduce,
before it reaches production.

## Batch sizing

`serial: "25%"` with `max_fail_percentage: 20` means:

- A run touches roughly a quarter of a group at a time.
- If more than 20% of a batch fails, the play stops before the next batch
  starts.
- For a 4-host group, that's realistically "one host at a time until you've
  proven the patch is safe" — which is intentional for small fleets.

For larger fleets, smaller percentages (e.g. `serial: "10%"`) give you more
canary batches before the majority of the fleet is touched. There's no
universal right number — it's a trade-off between total patch-run duration
and blast radius per batch.

## Reboot policy

Reboots are opt-in (`patch_reboot_allowed: false` by default) because a
reboot is the single highest-impact action in this whole workflow — it's
the point where a host actually goes down. Separating "patch applied" from
"host rebooted" means:

- You can patch during business hours and reboot during a maintenance
  window, as two separate playbook runs.
- A patch run that doesn't require a reboot (the common case) completes
  with zero downtime.
- Database hosts (`db_servers` group) keep `patch_reboot_allowed: false`
  even in production overrides — reboot there is always a manual, planned
  action.

## Rollback

Two rollback mechanisms exist at different levels:

1. **`dnf history undo`** (via `playbooks/rollback.yml`) — reverses the
   specific package transaction. Fast, always available, but doesn't help
   if the problem is a config file changed by a package post-install
   script.
2. **LVM snapshot** (`patch_lvm_snapshot_enabled: true`) — a block-level
   snapshot taken before patching. Reverting it undoes *everything* since
   the snapshot, including config drift, at the cost of losing any
   legitimate changes made since patching. This is the safety net for
   "the dnf-level rollback isn't enough."

Neither is a substitute for testing patches in staging first — they exist
to make a bad production patch recoverable, not to make testing optional.

## Compliance reporting cadence

`playbooks/compliance-report.yml` is read-only and safe to run on a
schedule independent of patching — e.g. nightly via cron or an AWX/Tower
job template — to track how compliance drifts between patch windows. The
patch run itself (`patch.yml`) also generates a report at the end, so every
patch run is self-documenting.
