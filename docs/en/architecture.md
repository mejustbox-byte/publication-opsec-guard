# Architecture

CLI → bounded loader → adapter → checks → normalized JSON → report presentation. Checks are pure functions; collection is separate from assessment. Contract fields: schema_version, tool_version, check_id, asset_id, status, severity, evidence, remediation. Statuses: pass/fail/not_tested/not_applicable. Collector errors are retained separately. Paths and identifiers are sensitive: public export requires separate sanitization.
