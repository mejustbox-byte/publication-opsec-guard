import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
import zipfile
from publication_opsec_guard.documents import inspect, exit_code, P, A, CT, PPT_TYPE


def presentation(path, text='safe', extras=None, runs=None, content_type=PPT_TYPE):
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',f'<Types xmlns="{CT}"><Override PartName="/ppt/presentation.xml" ContentType="{content_type}"/></Types>')
        z.writestr('_rels/.rels','<Relationships><Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>')
        z.writestr('ppt/presentation.xml',f'<p:presentation xmlns:p="{P}"/>')
        run_text = ''.join(f'<a:r><a:t>{v}</a:t></a:r>' for v in (runs or [text]))
        z.writestr('ppt/slides/slide1.xml',f'<p:sld xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree><a:p>{run_text}</a:p></p:spTree></p:cSld></p:sld>')
        for name, value in (extras or {}).items(): z.writestr(name,value)


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'sample.pptx'

    def test_clean_profile_and_schema(self):
        from jsonschema import Draft202012Validator
        presentation(self.path)
        result=inspect(self.path)
        self.assertEqual(exit_code(result),0)
        self.assertEqual(result['format'],'pptx')
        schema=json.loads((Path(__file__).parent/'schemas/documents-0.2.schema.json').read_text())
        self.assertTrue(Draft202012Validator(schema).is_valid(result))

    def test_split_drawingml_runs(self):
        presentation(self.path,runs=['10.1.','2.3'])
        result=inspect(self.path)
        self.assertEqual(exit_code(result),1)
        self.assertEqual(result['findings'][0]['check_id'],'PUB-001')
        self.assertEqual(result['findings'][0]['part_id'],'ppt/slides/slide1.xml')

    def test_notes_hidden_slides_and_author_metadata(self):
        presentation(self.path,extras={
            'ppt/notesSlides/notesSlide1.xml': f'<p:notes xmlns:p="{P}" xmlns:a="{A}"><a:p><a:r><a:t>demo.internal</a:t></a:r></a:p></p:notes>',
            'ppt/slides/slide2.xml': f'<p:sld xmlns:p="{P}" xmlns:a="{A}" show="0"><a:p><a:r><a:t>10.4.5.6</a:t></a:r></a:p></p:sld>',
            'ppt/commentAuthors.xml': f'<p:cmAuthorLst xmlns:p="{P}"><p:cmAuthor name="IDENTITY_SENTINEL" initials="IS"/></p:cmAuthorLst>'})
        result=inspect(self.path)
        self.assertEqual({f['check_id'] for f in result['findings']},{'DOC-001','PUB-001','PUB-002'})
        self.assertNotIn('IDENTITY_SENTINEL',json.dumps(result))

    def test_media_embeddings_and_external_links_remain_gaps(self):
        for name, value in [('ppt/media/image.png',b'image'),('ppt/embeddings/object.bin',b'object'),
            ('ppt/slides/_rels/slide1.xml.rels','<Relationships><Relationship TargetMode="External" Target="https://example.invalid/"/></Relationships>')]:
            presentation(self.path,extras={name:value})
            self.assertEqual(exit_code(inspect(self.path)),2)

    def test_macro_wrong_type_and_extension_rejected(self):
        presentation(self.path,content_type='application/vnd.ms-powerpoint.presentation.macroEnabled.main+xml')
        self.assertEqual(exit_code(inspect(self.path)),2)
        other=self.path.with_suffix('.pptm');presentation(other)
        self.assertEqual(exit_code(inspect(other)),2)
        self.assertEqual(inspect(other)['format'],'unsupported')

    def test_existing_docx_profile_survives(self):
        from test_documents import package
        docx=self.path.with_suffix('.docx');package(docx,text='safe')
        result=inspect(docx)
        self.assertEqual(exit_code(result),0)
        self.assertEqual(result['format'],'docx')
        self.assertEqual(result['schema_version'],'documents-0.2')

    def test_cli_pptx_codes(self):
        for text, extras, expected in [('safe',{},0),('10.1.2.3',{},1),('safe',{'ppt/media/a.png':b'image'},2)]:
            presentation(self.path,text=text,extras=extras)
            result=subprocess.run([sys.executable,'-m','publication_opsec_guard.documents',str(self.path)],
                                  capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,expected,result.stderr)
            self.assertEqual(json.loads(result.stdout)['format'],'pptx')

if __name__ == '__main__':unittest.main()
