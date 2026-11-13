# Report outbox handoff
Muse: use a separate local copy. No change to current collection.
Save each sanitized report locally, then run:
```sh
python3 tools/report_outbox.py enqueue /path/to/report.md
python3 tools/report_outbox.py status
```
Continue independent work immediately. Do not invoke a blocking approval action during unattended work. When user is available, create a fresh batch directory:
```sh
python3 tools/report_outbox.py batch /path/to/new-batch
```
Inspect manifest, review content for secrets and customer data, then submit selected reports in one ordinary GitHub approval card to integration/grok-review. Preserve original intended docs paths; resolve conflicting versions before submission. Do not bypass approval. After confirming all manifest files match committed content, run:
```sh
python3 tools/report_outbox.py ack /path/to/new-batch/manifest.json VERIFIED_FULL_COMMIT_SHA
```
If denied or uncertain, leave pending. No automatic ack. Never mark task complete merely because report is queued. If a task requires GPT feedback, park it and continue independent tasks.
Acceptance: compile; enqueue same file twice gives one pending; batch preserves bytes; no ack until actual verified commit; pending survives restart. Test with temporary root and synthetic reports only. Report actual test result. This utility is not a background agent or an approval bypass.
