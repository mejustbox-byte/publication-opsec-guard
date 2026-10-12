# DOCX inspection: XML text and identity metadata

## What this command does

`publication-opsec-documents` inspects one `.docx` file locally and read-only. It checks UTF-8 XML text and attributes with PUB-001–PUB-005 and emits DOC-001 for selected nonempty identity metadata. This is the first M6 format subcycle, not general Office/PDF/archive support. The existing text scanner, secret adapter and Action/hook do not automatically call it.

A DOCX package contains separate XML parts. The implementation requires `[Content_Types].xml`, `_rels/.rels` and `word/document.xml`, a main WordprocessingML root, a nonmacro DOCX main content type and a main relationship. It is a constrained package profile, not full ECMA/ISO conformance validation or Microsoft Word rendering. See [Microsoft structure reference](https://learn.microsoft.com/en-us/office/open-xml/word/structure-of-a-wordprocessingml-document).

## Installation and invocation

Install Guard 0.2.0a5 from a reviewed checkout using the [installation guide](installation.md). No additional parser library or Microsoft Office installation is required. Inspect an immutable prepared copy and store the report outside any later inspected directory:

```bash
publication-opsec-documents prepared.docx --policy policy.local.json > document-report.json
```

`--policy` is optional and uses the existing strict UTF-8 marker policy. Exit 1 means findings, possibly together with gaps; exit 2 means incomplete/invalid inspection without findings; exit 0 means no findings or recorded gaps in the declared XML scope. It does not prove the visual document or every embedded representation safe. A normal Word file can contain author metadata and therefore produce DOC-001.

## Extraction and evidence

Every readable `.xml`/`.rels` part is parsed. For transitional WordprocessingML paragraphs, text from `w:t`, `w:delText` and `w:instrText` runs is joined within a paragraph: an address split across formatting runs can still match. Other element text and attribute values are inspected separately. Headers, footers, notes and comments are covered when represented in readable XML parts. Attributes include hyperlink targets; no target is fetched.

A finding identifies the document basename and ZIP `part_id`. PUB findings have `evidence.kind: extracted_line` and a one-based line in the temporary extracted representation, **not a Word page or original XML line**. DOC-001 has `kind: identity_metadata` without a line. Its sources are nonempty creator, lastModifiedBy, Company and Manager elements under docProps, plus author/initials attributes in word/comments parts. It is a context-review indicator: synthetic author/tool names can be intentional false positives.

The output discards matched content and metadata values. Filenames and part names remain visible. No automatic metadata removal, key rotation or document editing is performed.

## Limits and rejection rules

| Limit | Default |
|---|---|
| ZIP input | 8,000,000 bytes |
| ZIP entries | 1,000 |
| Uncompressed part | 2,000,000 bytes |
| XML total | 16,000,000 bytes |
| Declared compression ratio | 100 |
| XML depth per part | 64 |
| XML elements per part | 100,000 |
| Findings | 10,000 |

Only stored/deflated ZIP parts are accepted. Encrypted members, ZIP symlink members, duplicate names, traversal/absolute paths, backslashes, colon-containing paths and ambiguous names are rejected. Parts are read by bounded streams; nothing is extracted to paths from the archive. DTD/ENTITY declarations, UTF-16/NUL XML, malformed XML and excess XML depth/elements remain untested. UTF-8 BOM is accepted.

The scanner reads the ZIP into bounded memory, keeps bounded XML trees and uses a private temporary text file for the existing rule engine. This is not a hard total memory or CPU quota. XML parsing and ZIP libraries still require a maintained Python runtime; the package metadata minimum is a compatibility floor, not a security-patch guarantee. See [Python XML security](https://docs.python.org/3/library/xml.html) and [ZIP security](https://docs.python.org/3/library/zipfile.html).

## Coverage gaps and decisions

| Reason | Interpretation |
|---|---|
| uninspected_zip_metadata / xml_comments_or_processing_instructions | ZIP comments/extra metadata or XML comments/processing instructions are present but uninspected |
| unsupported_part | Images, embedded binaries, VBA or other non-XML payloads were not inspected |
| external_reference | A relationship points outside the package; target was not retrieved |
| archive_size_limit / part_count_limit | ZIP container exceeds the declared scope |
| part_size_or_ratio_limit / total_xml_bytes_limit / part_read_limit | Bounded decompression/read policy prevented full inspection |
| encrypted_part / unsupported_compression | Content cannot be inspected in this profile |
| unsafe_or_duplicate_part | Package names or member type are unacceptable |
| invalid_or_unsupported_xml | XML is malformed, not supported UTF-8, DTD/entity-bearing or beyond parser limits |
| invalid_ooxml_package | Required parts/root/content type/main relation are missing or inconsistent |
| extracted_text_incomplete | The existing scanner could not fully inspect extracted text |
| invalid_input_policy_or_package | Input, policy, ZIP reading or finding cap failed |

Findings can coexist with gaps. Review both arrays. Images are never marked clean because their surrounding XML is readable. External hyperlinks can be legitimate, but external content coverage remains unavailable. DOCM, legacy DOC, PDF, XLSX/PPTX, image metadata/OCR and arbitrary ZIP files remain unsupported.

## Response schema

The independent `documents-0.2` envelope contains schema/tool version, explicit scope, document basename, coverage state, counters, effective limits, findings and coverage gaps. The bundled [JSON Schema](../../schemas/documents-0.2.schema.json) validates shape; it does not establish producer authenticity or publication safety. The core `publication-opsec-validate` CLI handles response-0.2 only and rejects this envelope.

`coverage_complete` describes successful processing of this constrained XML-text/selected-metadata scope. It does not validate relationships semantically, discover all hidden/custom XML meaning, establish visual content completeness or guarantee detection of every secret. Strict OOXML variants, unusual main-part locations and uncommon valid compression/encoding profiles may be rejected conservatively.

## Verification and next formats

Fourteen DOCX test methods generate synthetic ZIP packages at runtime: clean structure; formatting-run split indicators; marker redaction; identity/comment metadata; header and external target; images/embeddings; unsafe/duplicate/symlink members; DTD/depth/encoding; size/count/ratio/compression; invalid packages; unchanged source and invalid policy; finding cap/no-network; response-schema states; CLI 0/1/2. They run on all three CI platforms. Clean-environment installation also checks the new console command.

These fixtures do not prove Microsoft Word round-trip rendering or every real-world DOCX producer. The next format needs its own parser selection, threat model, limits, corpus and truthful coverage semantics. No automated PDF/Office completion is implied by this DOCX delivery.

---

[Documentation index](index.md) · [Русский](../ru/docx-inspection.md)


Current document envelope is 0.2 and includes format=docx; see [migration and PPTX](pptx-inspection.md). The 0.1 schema is retained for historical outputs.
