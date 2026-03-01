# Contributing

1. Fork → feature branch.
2. Keep PRs focused (ideally < 500 LOC).
3. If you tweak schemas or outputs, update README examples.
4. Dev loop:
   ```bash
   make bootstrap
   make demo
   make api
   ```
5. Add/adjust keywords in `app/classifier.py` (`BUCKETS`) with comments.
6. Open PR with screenshots / sample JSON.

Style/lint: optional (black/ruff). Tests TBD.
