# XLSX XML profile

## Purpose and use

`publication-opsec-documents workbook.xlsx` inspects a bounded SpreadsheetML package using the same ZIP/XML limits as DOCX/PPTX. The main part is `xl/workbook.xml`, with transitional workbook namespace and a nonmacro XLSX content type. Legacy XLS, XLSM, XLSB, templates, Strict OOXML and unusual main-part locations are not supported. No Excel process is launched.

## Text representations

Shared-string `si` and inline-string `is` elements join rich-text `t` runs before the five text rules run. The shared-string table itself is scanned, including unused entries; it is not resolved to every referencing cell. XML in worksheets, comments, defined names, formulas, cached values, hidden sheets, connections and other readable parts receives generic text/attribute checks. Formulas are inspected as text and are never calculated. Cached values may be stale. Display formatting, sheet/cell address mapping and evaluated formulas are outside scope.

DOC-001 additionally flags nonempty legacy `xl/comments` author elements. Values are hidden; author identities in newer threaded/vendor formats are not semantically resolved. Source: [Microsoft SpreadsheetML structure](https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/structure-of-a-spreadsheetml-document).

## Coverage and output

The existing documents-0.2 envelope adds xlsx to its format enum. Consumers must reject unknown format values deliberately. Evidence is an extracted line in a ZIP part, not an Excel cell address. Images, embedded OLE/binaries, external relationships and uninspected ZIP/XML metadata remain gaps. Workbook relationships are not fully validated, and readable chart XML does not cover an embedded workbook/image. See [shared parser limits](docx-inspection.md).

## Verification

Synthetic tests cover plain/rich shared strings, inline strings/formula text, hidden workbook metadata, comment-author redaction, embeddings and macro type rejection. Regression tests retain DOCX/PPTX. These establish parser behavior, not Excel rendering or real-world formula correctness. The unified runner can dispatch XLSX together with other prepared files.

---

[Documentation index](index.md) · [Русский](../ru/xlsx-inspection.md)
