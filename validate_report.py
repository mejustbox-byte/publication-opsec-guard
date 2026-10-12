"""Compatibility launcher for source-checkout users."""
import sys
from publication_opsec_guard import validate_report as implementation
if __name__ == '__main__':
    sys.exit(implementation.main())
else:
    sys.modules[__name__] = implementation
