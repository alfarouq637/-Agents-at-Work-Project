# Runtime SBOM

[sbom.cdx.json](sbom.cdx.json) is the reproducible CycloneDX 1.7 inventory of
the exact runtime packages in `requirements.lock`. It is generated from the
lockfile, not from a developer workstation environment, and contains no
configuration or customer data.

After an approved dependency update, regenerate it with Python 3.11 and the
pinned generator version:

```bash
python -m pip install cyclonedx-bom==7.5.0
python -m cyclonedx_py requirements --output-reproducible --spec-version 1.7 --output-format JSON --output-file docs/sbom.cdx.json requirements.lock
```

CI regenerates the file and rejects a stale committed inventory. This is a
software inventory and vulnerability-triage input, not a security certification
or a substitute for dependency auditing, provenance, or deployment review.
