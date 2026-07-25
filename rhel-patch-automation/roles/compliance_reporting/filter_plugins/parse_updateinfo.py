"""Custom Jinja2 filters for parsing `dnf updateinfo` output.

`dnf updateinfo list security` prints lines like:

    RHSA-2024:1234 Important/Sec.  bash-5.1.8-6.el9.x86_64
    RHSA-2024:5678 Moderate/Sec.   openssl-3.0.7-6.el9.x86_64

This module turns that free-text output into a list of dicts so it can be
looped over cleanly in Jinja2 templates instead of regex-matched inline.
"""

import re

ADVISORY_LINE_RE = re.compile(
    r"^(?P<advisory>[A-Za-z0-9_:.\-]+)\s+"
    r"(?P<severity>Critical|Important|Moderate|Low)"
    r"(?:/Sec\.?)?\s+"
    r"(?P<package>\S+)\s*$"
)


def parse_updateinfo(stdout_lines):
    """Parse `dnf updateinfo list security` stdout lines into structured records.

    Args:
        stdout_lines: list[str] — raw lines from `dnf updateinfo list security`.

    Returns:
        list[dict] with keys: advisory, severity, package.
        Lines that don't match the expected format (headers, blank lines,
        summary lines) are silently skipped rather than raising, since dnf's
        output format varies slightly across versions.
    """
    if not stdout_lines:
        return []

    records = []
    for line in stdout_lines:
        match = ADVISORY_LINE_RE.match(line.strip())
        if not match:
            continue
        records.append(
            {
                "advisory": match.group("advisory"),
                "severity": match.group("severity"),
                "package": match.group("package"),
            }
        )
    return records


def severity_count(records, severity):
    """Count parsed advisory records matching a given severity (case-insensitive)."""
    if not records:
        return 0
    return len([r for r in records if r.get("severity", "").lower() == severity.lower()])


class FilterModule(object):
    def filters(self):
        return {
            "parse_updateinfo": parse_updateinfo,
            "severity_count": severity_count,
        }
