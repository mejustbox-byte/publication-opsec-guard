# PPTX inspection and documents-0.2 migration

## Purpose and boundary

The existing `publication-opsec-documents` command now accepts `.pptx` as well as `.docx`. It inspects a bounded OOXML XML-text profile locally without launching PowerPoint. The purpose is to find retained internal addressing, naming, paths, key headers, policy markers and selected author metadata in presentation packages. It does not render slides, OCR screenshots, decode media, run macros or retrieve linked content.

Install Guard 0.2.0a6 from a reviewed checkout. No additional runtime parser dependency is required. Use an immutable prepared copy; `--policy` is optional and uses the existing marker contract:

```bash
publication-opsec-documents prepared.pptx --policy policy.local.json > presentation-report.json
```

Exit codes remain 0/1/2 for clean declared scope, findings and incomplete/invalid scope. Findings can coexist with gaps. A zero result says nothing about unsupported visual representations that were outside the declared checks.

## Presentation package profile

The main part is `ppt/presentation.xml` with a transitional PresentationML `presentation` root and the nonmacro presentation main content type. `[Content_Types].xml` and `_rels/.rels` must declare the corresponding main content and relationship. `.pptm`, legacy `.ppt`, `.ppsx`, Strict OOXML, unusual main locations and macro main types are not accepted. This profile is conservative; it is not full OOXML or relationship-graph validation.

All readable XML parts are inspected, including slides, notes, slide/layout masters, comments and unreferenced XML parts. Hidden slides are not suppressed. DrawingML `a:t` runs are joined within `a:p` paragraphs before matching, so formatting boundaries do not necessarily hide an indicator. Generic text and attribute values are also checked. The existing WordprocessingML joining remains available for DOCX.

Sources: [Microsoft PresentationML structure](https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document), [comment authors](https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-comments).

## Selected identity metadata

DOC-001 continues to flag nonempty creator, lastModifiedBy, Company and Manager values in docProps. For the legacy `ppt/commentAuthors` parts it also flags nonempty `name` or `initials` attributes. Values are omitted from output. This is a review signal, not a claim that every author format or identity representation is recognized. Newer/vendor-specific author models are not semantically resolved; their readable text/attributes still receive the five generic checks.

A finding reports the presentation basename and `part_id` such as `ppt/notesSlides/notesSlide1.xml`. `extracted_line` is a one-based line in the temporary text representation, not the displayed slide number, slide order, shape position or original XML line. Metadata evidence has no line. Filenames and part names remain visible even though matched values are hidden.

## Media, links and parser limits

The [DOCX parser limits](docx-inspection.md) apply to the shared ZIP/XML implementation: 8 MB compressed input, 1,000 parts, 2 MB per uncompressed part, 16 MB XML total, compression ratio 100, XML depth 64 and 100,000 elements per part, 10,000 findings. Stored/deflated ZIP only; no archive path extraction. DTD/entities, unsupported XML encodings, unsafe/duplicate/symlink members and encrypted parts cannot become clean results.

Images, embedded workbooks/OLE, audio, video and other non-XML payloads produce `unsupported_part`; external relationships produce `external_reference`. ZIP comments/extra metadata and XML comments/processing instructions remain uninspected gaps. A chart may have readable XML and an embedded XLSX: inspecting the former does not cover the latter. The command does not inspect general archives or call Gitleaks automatically. No hard total RAM/CPU quota or PowerPoint rendering proof is provided.

## Contract migration: documents-0.1 → documents-0.2

| Field | 0.1 | 0.2 |
|---|---|---|
| schema_version | documents-0.1 | documents-0.2 |
| scope | docx-utf8-xml-text-and-selected-identity-metadata | ooxml-utf8-xml-text-and-selected-identity-metadata |
| format | Absent | Required: docx, pptx or unsupported |
| Invalid package reason | invalid_docx_package | invalid_ooxml_package |
| All other fields | Original DOCX envelope | Same meanings and shapes |

The new command emits 0.2 for both DOCX and PPTX. Keep consumers version-aware; do not silently accept an unknown scope. The old [schema](../../schemas/documents-0.1.schema.json) is retained for historic outputs; the [new schema](../../schemas/documents-0.2.schema.json) describes current outputs. The core response-0.2 and secret-adapter secrets-0.1 contracts are unchanged. The core validator now supports document envelopes; schema validation checks shape, not source authenticity or semantic coverage.

## Verification and use in publication workflows

Seven presentation test methods cover clean profile/schema, run-split indicators, notes and hidden slides, comment-author redaction, unsupported media/embeddings/external links, macro/type/extension rejection, DOCX regression and CLI codes. Together with existing checks the suite contains 71 test methods. CI uses the same tests on Linux, Windows and macOS and verifies installation from the wheel. Minimal fixtures do not establish compatibility with every PowerPoint producer or Office rendering.

Run this command as a separate gate for each prepared document. The existing Action/pre-commit hook remains a directory text check and does not dispatch Office files. Inspect findings and gaps together, then review the visual document and unsupported contents through an appropriate separate process before publication.

---

[Documentation index](index.md) · [Русский](../ru/pptx-inspection.md)

[All-report validation](all-report-validation.md) is supplied from 0.3.0a1.
