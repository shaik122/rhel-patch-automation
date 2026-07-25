# Variable Reference

## `patch_management` role

| Variable | Default | Description |
|---|---|---|
| `patch_security_only` | `true` | Patch only security errata vs all available updates |
| `patch_reboot_allowed` | `false` | Whether the role may reboot the host if a reboot is required |
| `patch_reboot_timeout` | `600` | Seconds to wait for the host to come back after a reboot |
| `patch_lvm_snapshot_enabled` | `false` | Take an LVM snapshot before patching |
| `patch_lvm_vg` | `rhel` | Volume group to snapshot |
| `patch_lvm_lv` | `root` | Logical volume to snapshot |
| `patch_lvm_snapshot_size` | `5G` | Snapshot size |
| `patch_excluded_packages` | `[]` | dnf-style globs to exclude from patching (e.g. `kernel*`) |
| `patch_critical_services` | `[]` | Services checked/restarted after patching |
| `patch_report_dir` | `{{ playbook_dir }}/../reports` | Where reports and state files are written |
| `patch_state_dir` | `{{ patch_report_dir }}/state` | Where per-host pre/post-patch state files live |
| `patch_environment` | *(set per inventory)* | Label shown in reports (e.g. `production`, `staging`) |

## `compliance_reporting` role

| Variable | Default | Description |
|---|---|---|
| `patch_report_dir` | `{{ playbook_dir }}/../reports` | Output directory for rendered reports |
| `compliance_report_formats` | `[markdown, html]` | Which report formats to render |

## Facts produced (consumed by the report, not meant to be set manually)

| Fact | Set by | Description |
|---|---|---|
| `patch_summary` | `patch_management/tasks/post_checks.yml` | Per-host summary of a patch run: updates applied, rebooted, service health, status |
| `compliance_record` | `compliance_reporting/tasks/gather_compliance.yml` | Per-host compliance snapshot: pending updates, parsed security advisories, subscription/Insights status |
