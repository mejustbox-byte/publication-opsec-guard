# Testing and lab

Each check: unsafe input → fail; safe input → pass; missing evidence → not_tested; established inapplicability → not_applicable. Measure TP/FP/FN/TN on a versioned corpus; do not invent accuracy percentages. Separately test malformed JSON, Unicode, limits, symlinks and permission failures. Live lab records OS, versions, configuration, date, SHA and sanitized evidence; fixtures do not replace live labs. No paid resources are created automatically.

## Locally executed

8 tests: five rules and match redaction; documentation addresses; RFC1918 boundaries; symlink and unsupported format; size/encoding/binary text; file count; literal marker; clean text. No Windows/macOS lab or CI yet.
