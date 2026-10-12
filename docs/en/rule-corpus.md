# Synthetic rule corpus and measured behavior

## Purpose and scope

The corpus makes the five current text-rule claims reviewable. It contains 54 independently labeled inputs in `examples/rules/corpus.json`. Each case is scanned alone in a temporary UTF-8 file, preventing one input from affecting another. All values are synthetic; private-key cases contain headers only, never functioning key material.

## Reading a case

`id` is a stable case identifier; `rule` identifies the rule being assessed; `category` describes positive, negative or boundary intent; `text` is the exact input; `markers` supplies a synthetic policy; `expected_count` is the expected count for that rule only. Zero does not mean publication safety. Other rules are not suppressed.

## Current observations

| Rule | Cases expecting findings | Cases expecting none |
|---|---|---|
| PUB-001 | 7 | 12 |
| PUB-002 | 4 | 4 |
| PUB-003 | 5 | 5 |
| PUB-004 | 6 | 4 |
| PUB-005 | 5 | 2 |

All 54 case counts match their labels locally. These counts are regression evidence on this finite corpus, not precision/recall measurements on production data. The full suite has 38 test methods; corpus cases run as subtests, not 54 additional methods. CI must pass independently on each supported runner before merge.

## Representations and boundaries

IPv4 covers both ends of every selected private network, adjacent outside addresses, invalid octets, leading zeroes, word adjacency, CIDR text and an IPv6 negative. Domain cases cover uppercase suffixes, URLs, Unicode labels and suffix continuation. Path cases cover Unix/macOS prefixes, Windows drive letters, prefix case, missing usernames and the incidental `/Users/` match in a forward-slash Windows path. Key cases cover all six accepted headers and four nonmatching variants. Marker cases verify escaped punctuation, substring matching, multiple occurrences, Unicode case and overlapping configured markers.

## Run and interpret

Run from the repository root in the validator environment:

```bash
python3 -m unittest test_rule_corpus -v
python3 -m unittest discover -v
python3 check_docs.py
```

A case failure identifies its stable ID and expected/actual count. Inspect the implementation and documented behavior before changing a label. Do not update expected values merely to silence a failure. If behavior changes deliberately, update both languages and add migration notes where needed. A report is also passed through the standalone validator, and the multiline case checks exact one-based evidence lines.

## Limits and extension

The corpus does not test PDF/Office/images, secret validity, organizational ownership or arbitrary encodings. It does not establish performance or resistance to every regex input. Add a minimal synthetic regression case for each confirmed bug. Keep real filenames, credentials, employer names and production exports outside this corpus. Coverage limits and unreadable inputs remain in the scanner hardening tests.

---

[Documentation index](index.md) · [Русский](../ru/rule-corpus.md)
