"""Real pinned-engine integration on synthetic material; no valid credentials."""
import hashlib
import os
from pathlib import Path
import tempfile
from publication_opsec_guard.secrets import inspect, exit_code

def main():
    binary = Path(os.environ['GITLEAKS_TEST_BINARY']).resolve()
    with binary.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sample = root/'sample.txt'; sample.write_text('ordinary documentation text')
        response = inspect(root, binary, digest)
        assert exit_code(response) == 0, response
        # Synthetic nonfunctional token matching the pinned rule's lexical shape.
        token = 'ghp_' + 'A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8'
        sample.write_text('token = "'+token+'" # gitleaks:allow\n')
        response = inspect(root, binary, digest)
        assert exit_code(response) == 1 and response['engine']['status'] == 'completed', response
        assert response['findings'], response
        assert token not in str(response), 'Raw synthetic token leaked'
        print('OK: real Gitleaks 8.24.2 clean/finding, inline allow bypass disabled, converted output redacted')

if __name__ == '__main__':
    main()
