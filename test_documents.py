import io
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
import warnings
import zipfile
from unittest.mock import patch
from publication_opsec_guard.documents import inspect, exit_code, parse_xml, LIMITS, W, CT, MAIN_TYPE

TYPES = f'<Types xmlns="{CT}"><Override PartName="/word/document.xml" ContentType="{MAIN_TYPE}"/></Types>'
RELS = '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'

def package(path, text='safe', extras=None, main=None, compression=zipfile.ZIP_DEFLATED):
    with zipfile.ZipFile(path, 'w', compression=compression) as archive:
        archive.writestr('[Content_Types].xml', TYPES)
        archive.writestr('_rels/.rels', RELS)
        archive.writestr('word/document.xml', main or f'<w:document xmlns:w="{W}"><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>')
        for name, value in (extras or {}).items():
            info = zipfile.ZipInfo(name)
            # Preserve malicious names literally: Windows ZipInfo normally normalizes separators.
            info.filename = info.orig_filename = name
            info.compress_type = compression
            archive.writestr(info, value)

class DocumentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'sample.docx'

    def test_minimal_clean_and_schema(self):
        package(self.path)
        result = inspect(self.path)
        self.assertEqual(exit_code(result), 0)
        self.assertEqual(result['parts_inspected'], 3)
        from jsonschema import Draft202012Validator
        schema = json.loads((Path(__file__).parent/'schemas/documents-0.1.schema.json').read_text())
        Draft202012Validator.check_schema(schema)
        self.assertTrue(Draft202012Validator(schema).is_valid(result))

    def test_run_split_indicators_and_marker_redaction(self):
        main = f'<w:document xmlns:w="{W}"><w:body><w:p><w:r><w:t>10.1.</w:t></w:r><w:r><w:t>2.3 SENTINEL_NAME</w:t></w:r></w:p></w:body></w:document>'
        package(self.path, main=main)
        policy = self.path.parent/'policy.json'; policy.write_text('{"markers":["SENTINEL_NAME"]}')
        result = inspect(self.path, policy)
        self.assertEqual(exit_code(result), 1)
        self.assertEqual({f['check_id'] for f in result['findings']}, {'PUB-001','PUB-005'})
        self.assertNotIn('SENTINEL_NAME', json.dumps(result))
        self.assertEqual(result['findings'][0]['evidence']['kind'], 'extracted_line')

    def test_metadata_and_comments(self):
        package(self.path, extras={'docProps/core.xml':'<properties><creator>IDENTITY_SENTINEL</creator></properties>',
            'word/comments.xml':f'<w:comments xmlns:w="{W}"><w:comment w:author="IDENTITY_SENTINEL"><w:p><w:r><w:t>safe</w:t></w:r></w:p></w:comment></w:comments>'})
        result = inspect(self.path)
        self.assertEqual(len([f for f in result['findings'] if f['check_id']=='DOC-001']), 2)
        self.assertNotIn('IDENTITY_SENTINEL', json.dumps(result))

    def test_header_footer_and_external_target(self):
        package(self.path, extras={'word/header1.xml': f'<w:hdr xmlns:w="{W}"><w:p><w:r><w:t>demo.internal</w:t></w:r></w:p></w:hdr>',
            'word/_rels/document.xml.rels':'<Relationships><Relationship TargetMode="External" Target="https://demo.internal/"/></Relationships>'})
        result = inspect(self.path)
        self.assertEqual(exit_code(result), 1)
        self.assertFalse(result['coverage_complete'])
        self.assertIn('external_reference', [g['reason'] for g in result['coverage_gaps']])

    def test_images_and_embedded_files_not_clean(self):
        for name in ('word/media/image.png','word/embeddings/file.bin','word/vbaProject.bin'):
            package(self.path, extras={name:b'not inspected'})
            result = inspect(self.path)
            self.assertEqual(exit_code(result), 2)
            self.assertIn('unsupported_part', [g['reason'] for g in result['coverage_gaps']])

    def test_traversal_duplicates_and_symlink_members(self):
        for name in ('../escape.xml','/absolute.xml','word\\escape.xml','word/../escape.xml','word//escape.xml'):
            package(self.path, extras={name:'<x/>'})
            self.assertEqual(exit_code(inspect(self.path)), 2)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore'); package(self.path)
            with zipfile.ZipFile(self.path,'a') as z: z.writestr('word/document.xml','<x/>')
        self.assertEqual(exit_code(inspect(self.path)), 2)
        package(self.path)
        info = zipfile.ZipInfo('word/link.xml'); info.create_system=3; info.external_attr=0o120777<<16
        with zipfile.ZipFile(self.path,'a') as z: z.writestr(info,'target')
        self.assertEqual(exit_code(inspect(self.path)), 2)

    def test_xml_dtd_entities_depth_and_encoding(self):
        for raw in (b'<!DOCTYPE x [<!ENTITY a "secret">]><x>&a;</x>', b'<x>',
                    '<x/>'.encode('utf-16'), b'<x>'*65+b'</x>'*65):
            with self.assertRaises((ValueError, UnicodeError, SyntaxError)):
                parse_xml(raw)
        package(self.path, extras={'word/comments.xml':b'<!DOCTYPE x><x/>'})
        self.assertEqual(exit_code(inspect(self.path)), 2)

    def test_byte_part_and_compression_limits(self):
        package(self.path, extras={'word/large.xml':'<x>'+'x'*20000+'</x>'})
        self.assertIn('part_size_or_ratio_limit', [g['reason'] for g in inspect(self.path)['coverage_gaps']])
        package(self.path)
        for key, value in [('archive_bytes',1),('parts',1),('part_bytes',1),('total_xml_bytes',1)]:
            with patch.dict(LIMITS, {key:value}): self.assertEqual(exit_code(inspect(self.path)), 2)
        package(self.path, compression=zipfile.ZIP_BZIP2)
        self.assertEqual(exit_code(inspect(self.path)), 2)

    def test_invalid_package_and_macro_type(self):
        for payload in (b'not a zip', b'PK'):
            self.path.write_bytes(payload); self.assertEqual(exit_code(inspect(self.path)),2)
        with zipfile.ZipFile(self.path,'w') as z: z.writestr('word/document.xml','<x/>')
        self.assertEqual(exit_code(inspect(self.path)),2)
        package(self.path, main='<document/>')
        self.assertEqual(exit_code(inspect(self.path)),2)

    def test_input_symlink_policy_and_source_unchanged(self):
        package(self.path); original=self.path.read_bytes()
        inspect(self.path); self.assertEqual(self.path.read_bytes(),original)
        self.assertEqual(exit_code(inspect(self.path, self.path.parent/'missing')),2)
        link=self.path.parent/'link.docx'; link.symlink_to(self.path)
        self.assertEqual(exit_code(inspect(link)),2)
        self.assertEqual(exit_code(inspect(self.path.parent/'missing.docx')),2)

    def test_finding_limit_and_no_network(self):
        package(self.path,text='10.1.2.3 10.1.2.4')
        with patch.dict(LIMITS, {'findings':1}):
            result=inspect(self.path); self.assertEqual(exit_code(result),1)
            self.assertFalse(result['coverage_complete'])
            self.assertLessEqual(len(result['findings']),1)
        with patch('socket.socket',side_effect=AssertionError('network')):
            self.assertEqual(exit_code(inspect(self.path)),1)

    def test_schema_for_result_states(self):
        from jsonschema import Draft202012Validator
        schema = json.loads((Path(__file__).parent/'schemas/documents-0.1.schema.json').read_text())
        validator = Draft202012Validator(schema)
        for text, extras in [('safe', {}), ('10.1.2.3', {}), ('safe', {'word/media/a.png': b'unknown'}),
                             ('safe', {'docProps/core.xml':'<x><creator>synthetic</creator></x>'})]:
            package(self.path, text=text, extras=extras)
            self.assertTrue(validator.is_valid(inspect(self.path)))
        self.path.write_bytes(b'broken')
        self.assertTrue(validator.is_valid(inspect(self.path)))

    def test_uninspected_xml_and_zip_metadata(self):
        for xml in ('<x><!-- synthetic hidden data --></x>', '<x><?custom hidden?></x>'):
            package(self.path, extras={'customXml/item1.xml': xml})
            result = inspect(self.path)
            self.assertEqual(exit_code(result), 2)
        package(self.path)
        with zipfile.ZipFile(self.path, 'a') as archive: archive.comment = b'synthetic metadata'
        self.assertEqual(exit_code(inspect(self.path)), 2)

    def test_cli_result_codes(self):
        for text, extras, code in [('safe', {}, 0), ('10.1.2.3', {}, 1),
                                 ('safe', {'word/media/a.png': b'unknown'}, 2)]:
            package(self.path, text=text, extras=extras)
            result = subprocess.run([sys.executable, '-m', 'publication_opsec_guard.documents', str(self.path)],
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, code, result.stderr)
            self.assertEqual(json.loads(result.stdout)['schema_version'], 'documents-0.1')

if __name__ == '__main__': unittest.main()
