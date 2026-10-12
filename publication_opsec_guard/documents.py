"""Bounded DOCX/PPTX XML-text inspection; images and embedded payloads remain untested."""
import argparse
import io
import json
import os
import re
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import zlib
from .guard import VERSION, read_policy, scan

LIMITS = {'archive_bytes': 8_000_000, 'parts': 1000, 'part_bytes': 2_000_000,
          'total_xml_bytes': 16_000_000, 'compression_ratio': 100,
          'xml_depth': 64, 'xml_elements': 100000, 'findings': 10000}
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
MAIN_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
PPT_TYPE = 'application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml'
PROFILES = {'.docx': ('word/document.xml', '{'+W+'}document', MAIN_TYPE),
            '.pptx': ('ppt/presentation.xml', '{'+P+'}presentation', PPT_TYPE)}


def parse_xml(raw):
    text = raw.decode('utf-8-sig')
    if '\x00' in text or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        raise ValueError('Unsupported XML')
    parser = ET.XMLPullParser(events=('start', 'end'))
    depth = count = 0
    root = None
    for offset in range(0, len(text), 4096):
        parser.feed(text[offset:offset+4096])
        for event, element in parser.read_events():
            if event == 'start':
                if root is None: root = element
                depth += 1; count += 1
                if depth > LIMITS['xml_depth'] or count > LIMITS['xml_elements']:
                    raise ValueError('XML limit')
            else:
                depth -= 1
    parser.close()
    if root is None:
        raise ValueError('Empty XML')
    return root


def extracted_lines(root):
    lines = []
    consumed = set()
    for paragraph in root.iter():
        if paragraph.tag not in {'{'+W+'}p', '{'+A+'}p'}:
            continue
        children = list(paragraph.iter()); consumed.update(children)
        value = ''.join(e.text or '' for e in children if e.tag in {
            '{'+W+'}t', '{'+W+'}delText', '{'+W+'}instrText', '{'+A+'}t'})
        if value: lines.append(value)
    for element in root.iter():
        if element not in consumed and element.text and element.text.strip():
            lines.append(element.text)
        lines.extend(value for value in element.attrib.values() if value.strip())
    return lines


def inspect(path, policy=None):
    path = Path(path)
    result = {'schema_version': 'documents-0.2', 'tool_version': VERSION,
              'scope': 'ooxml-utf8-xml-text-and-selected-identity-metadata',
              'format': path.suffix.lower().lstrip('.') if path.suffix.lower() in PROFILES else 'unsupported',
              'asset_id': path.name, 'coverage_complete': False, 'parts_inspected': 0,
              'xml_bytes_read': 0, 'limits': dict(LIMITS), 'findings': [], 'coverage_gaps': []}
    def gap(reason, part=None):
        item = {'status': 'not_tested', 'reason': reason}
        if part is not None: item['part_id'] = part
        result['coverage_gaps'].append(item)
    def finding(item):
        if len(result['findings']) >= LIMITS['findings']:
            raise ValueError('Finding limit')
        result['findings'].append(item)
    try:
        markers = read_policy(policy)
        if path.suffix.lower() not in PROFILES or path.is_symlink():
            raise ValueError('Input format')
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
        with os.fdopen(fd, 'rb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError('Not regular')
            archive = stream.read(LIMITS['archive_bytes']+1)
        if len(archive) > LIMITS['archive_bytes']:
            gap('archive_size_limit'); return result
        with zipfile.ZipFile(io.BytesIO(archive)) as package:
            if package.comment:
                gap('uninspected_zip_metadata')
            entries = package.infolist()
            if len(entries) > LIMITS['parts']:
                gap('part_count_limit'); return result
            names = set()
            for item in entries:
                name = item.filename
                if item.comment or item.extra:
                    gap('uninspected_zip_metadata', name)
                normalized = name.rstrip('/')
                parts = PurePosixPath(normalized).parts
                if (item.orig_filename != name or not normalized or '\\' in name or '\x00' in name or ':' in name
                        or name.startswith('/') or '..' in parts or '.' in name.split('/')
                        or '//' in name or normalized in names
                        or stat.S_ISLNK(item.external_attr >> 16)):
                    gap('unsafe_or_duplicate_part'); return result
                names.add(normalized)
                if item.flag_bits & 1:
                    gap('encrypted_part', name); return result
                if item.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                    gap('unsupported_compression', name); return result
                if (item.file_size > LIMITS['part_bytes'] or
                        item.file_size > max(1, item.compress_size) * LIMITS['compression_ratio']):
                    gap('part_size_or_ratio_limit', name); return result
            main_path, main_tag, content_type = PROFILES[path.suffix.lower()]
            required = {'[Content_Types].xml', '_rels/.rels', main_path}
            if not required <= names:
                gap('invalid_ooxml_package'); return result
            parsed = {}
            for item in entries:
                name = item.filename
                if item.is_dir(): continue
                if not name.endswith(('.xml', '.rels')):
                    gap('unsupported_part', name); continue
                if result['xml_bytes_read'] + item.file_size > LIMITS['total_xml_bytes']:
                    gap('total_xml_bytes_limit'); return result
                with package.open(item) as stream:
                    raw = stream.read(LIMITS['part_bytes']+1)
                if len(raw) != item.file_size or len(raw) > LIMITS['part_bytes']:
                    gap('part_read_limit', name); return result
                result['xml_bytes_read'] += len(raw)
                try:
                    xml_text = raw.decode('utf-8-sig')
                    if '<!--' in xml_text or re.search(r'<\?(?!xml(?:\s|\?))', xml_text):
                        gap('xml_comments_or_processing_instructions', name)
                    parsed[name] = parse_xml(raw)
                except (ValueError, UnicodeError, ET.ParseError):
                    gap('invalid_or_unsupported_xml', name)
            if not required <= parsed.keys():
                gap('invalid_ooxml_package'); return result
            types = parsed['[Content_Types].xml']
            main = parsed[main_path]
            rels = parsed['_rels/.rels']
            if (types.tag != '{'+CT+'}Types' or main.tag != main_tag
                    or not any(e.get('PartName') == '/'+main_path and e.get('ContentType') == content_type for e in types)
                    or not any(e.get('Target') == main_path and
                               (e.get('Type') or '').endswith('/officeDocument') and
                               e.get('TargetMode') != 'External' for e in rels)):
                gap('invalid_ooxml_package'); return result
            with tempfile.TemporaryDirectory(prefix='guard-ooxml-') as tmp:
                sample = Path(tmp) / 'part.txt'
                for name, root in parsed.items():
                    for element in root.iter():
                        if name.endswith('.rels') and element.get('TargetMode') == 'External':
                            gap('external_reference', name)
                        local = str(element.tag).split('}')[-1]
                        identity = (name.startswith('docProps/') and local in {'creator','lastModifiedBy','Company','Manager'} and (element.text or '').strip())
                        comment_identity = name.startswith('word/comments') and any(k.split('}')[-1] in {'author','initials'} and v.strip() for k,v in element.attrib.items())
                        presentation_identity = name.startswith('ppt/commentAuthors') and any(k.split('}')[-1] in {'name','initials'} and v.strip() for k,v in element.attrib.items())
                        if identity or comment_identity or presentation_identity:
                            finding({'check_id': 'DOC-001', 'asset_id': path.name, 'part_id': name,
                                     'status': 'fail', 'severity': 'medium',
                                     'evidence': {'kind': 'identity_metadata', 'redacted': True},
                                     'remediation': 'Review and remove identifying document metadata before publication.'})
                    lines = extracted_lines(root)
                    sample.write_text('\n'.join(lines), encoding='utf-8')
                    report = scan(tmp, markers=markers, max_bytes=4_000_000,
                                  max_findings=LIMITS['findings']-len(result['findings']) or 1)
                    for item in report['findings']:
                        converted = {**item, 'asset_id': path.name, 'part_id': name}
                        converted['evidence'] = {**item['evidence'], 'kind': 'extracted_line'}
                        finding(converted)
                    if not report['coverage_complete']:
                        gap('extracted_text_incomplete', name)
                    result['parts_inspected'] += 1
            result['coverage_complete'] = not result['coverage_gaps']
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, NotImplementedError, ET.ParseError, zlib.error, EOFError, RecursionError):
        gap('invalid_input_policy_or_package')
    return result


def exit_code(result):
    return 1 if result['findings'] else 0 if result['coverage_complete'] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('document'); parser.add_argument('--policy')
    args = parser.parse_args()
    result = inspect(args.document, args.policy)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return exit_code(result)


if __name__ == '__main__':
    sys.exit(main())
