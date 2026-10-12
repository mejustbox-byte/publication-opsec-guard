# Rule catalog PUB-001–PUB-005

## Common model

A rule locates a text indicator, emits `status: fail` and a one-based line number. Each match creates a record; multiple rules can match a single line. Severity is static, not calculated from impact on a particular organization.

“Does not match” below means no match for that rule only. It does not establish overall safety.

## PUB-001 — private IPv4

**Purpose:** identify possible internal addressing disclosure. **Severity:** high.

The algorithm first finds four decimal octets using regex, then validates the address with `ipaddress.ip_address`. It must belong to `10.0.0.0/8`, `172.16.0.0/12` or `192.168.0.0/16`. It uses these explicit networks rather than the broader `is_private` property.

| Text | Result | Reason |
|---|---|---|
| `10.20.30.40` | Matches | Within 10/8 |
| `172.31.255.255` | Matches | Upper boundary of 172.16/12 |
| `172.32.0.1` | No match | Outside the listed networks |
| `192.0.2.10` | No match | Documentation address outside this set |
| `999.1.1.1` | No match | Invalid IPv4 |

**False positives:** synthetic examples and generic instructions using RFC1918 addresses. **Misses:** IPv6, obfuscated addresses, image content, other ranges and addresses directly embedded in words. `10.1.2.3/24` may produce an address finding without CIDR-mask validation.

**Response:** review context and replace actual addresses with synthetic ones. The tool does not establish network ownership or connect to the address.

## PUB-002 — internal domain

**Purpose:** identify `.local` and `.internal` names. **Severity:** medium.

The regex searches letters/digits, `_`, dots and hyphens preceding the suffix, case-insensitively. It performs no DNS lookup or internal-ownership verification.

`demo.internal` and `host.LOCAL` match; `example.invalid` does not. Quoted names and URL content may match when their text fits the pattern. Other internal zones and organizational public domains are outside the rule; policy markers can cover them.

**False positives:** educational names. **Misses:** alternate zones, representations and unsupported formats. **Response:** replace identifying names with neutral examples and inspect adjacent text.

## PUB-003 — home directory path

**Purpose:** detect a username disclosed in an absolute path. **Severity:** medium.

Recognizes text prefixes `/Users/`, `/home/` and `C:\Users\` with any drive letter. The component after the prefix extends until whitespace or a separator. Prefix case matters: `C:\users\` does not match the current expression.

`/home/alice/file.txt`, `/Users/alice/report.md` and `C:\Users\alice\report.txt` match. Relative paths, `~`, UNC, Windows forward-slash paths and other directory forms are outside scope. JSON escaping may alter backslash representation; it is not parsed semantically.

**False positives:** synthetic usernames in examples. **Response:** replace identifying paths and review filenames and adjacent lines.

## PUB-004 — private-key header

**Purpose:** find an explicit private-key material indicator. **Severity:** critical.

Recognizes `PRIVATE KEY`, `RSA PRIVATE KEY`, `EC PRIVATE KEY`, `OPENSSH PRIVATE KEY`, `DSA PRIVATE KEY` and `ENCRYPTED PRIVATE KEY` headers with exact PEM-like delimiters. Matching is case-sensitive.

Example indicator: `-----BEGIN PRIVATE KEY-----`. A header alone is enough for a finding. The body, validity, algorithm, service availability and prior disclosure are not checked. A `PUBLIC KEY` header does not match.

**False positives:** an educational quote of the header. **Misses:** headerless keys and unsupported variants. **Response:** determine whether the key is real and remove it from publication. Arrange revocation/replacement separately if already disclosed.

## PUB-005 — organization marker

**Purpose:** locate sensitive names, code names or internal identifiers known to the policy author. **Severity:** high.

Each `markers` string is escaped and matched as a case-insensitive literal substring. `a.b` matches `a.b`, not `axb`. Empty markers are rejected by CLI. The policy does not disable PUB-001–PUB-004.

**False positives:** short common words, matches inside other words and duplicate markers. **Misses:** inflections, transliterations and alternate names absent from policy. There is no semantic classifier or automatic company-name discovery.

**Response:** use specific markers, inspect context and edit only the prepared copy. Do not publish the policy if it contains actual internal values.

---

[Documentation index](index.md) · [Русский](../ru/rule-catalog.md)


## Verified representation caveat

`C:/Users/synthetic` matches the Unix-style `/Users/` substring. This is incidental text matching, not Windows path parsing. The earlier statement excluding all Windows forward-slash paths was too broad. See [rule corpus](rule-corpus.md).
