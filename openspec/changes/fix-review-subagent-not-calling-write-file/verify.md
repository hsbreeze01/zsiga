Verdict: PASS
Completeness: ✓ All spec requirements implemented: prompt hardening with mandatory write_file instruction in prominent position, and defensive fallback that checks file existence and writes if Verdict line found.
Correctness: ✓ Prompt uses imperative "You MUST" language at the top of user_prompt; fallback uses `os.path.isfile()` check + `re.search(r"^Verdict:", ..., re.MULTILINE)` to correctly match verdict lines; no overwrite when file already exists; logs warning on fallback trigger.
Coherence: ✓ Follows existing code patterns; `parse_review_verdict` and metrics logic untouched; `roles.py` not modified; imports limited to `logging` and `os`; all existing tests pass.
Issues: none
