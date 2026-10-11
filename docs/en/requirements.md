# Publication OPSEC Guard: Requirements

Offline inspection of material before publication.

Text CLI; JSON report without raw matches; limits; marker policy. ZIP/PDF/Office, OCR and Gitleaks adapters are deferred.

All operations are read-only. No automatic remediation. Inputs stay local. Examples are synthetic only. Acceptance: every matrix ID has positive, negative and invalid-input cases; unknown or unavailable data never count as a pass. Unsupported formats are reported. Resource limits are configurable with safe defaults.
