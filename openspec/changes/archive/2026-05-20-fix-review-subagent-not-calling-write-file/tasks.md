# Tasks: Fix Review Sub-Agent Not Calling write_file

## Group 1: Prompt & Fallback Fix

1.1 - [x] **Harden review prompt to enforce write_file tool call** (`zsiga/agent/reviewer.py`)
   - In `run_review()`, modify the user_prompt construction to include an explicit, mandatory instruction: the sub-agent MUST call `write_file` to write review output to `{change_dir}/review.md`
   - Use imperative language ("You MUST call write_file tool...") and place the instruction prominently in the prompt

1.2 - [x] **Add defensive fallback: auto-write review.md if sub-agent omits write_file** (`zsiga/agent/reviewer.py`)
   - After `sub_agent.run()` returns, check if `{change_dir}/review.md` exists on disk
   - If missing AND `SubAgentResult.content` contains a line with `Verdict:`, write the content to `{change_dir}/review.md` using a direct file write (not a sub-agent call)
   - If missing but no `Verdict:` in content, skip (nothing useful to persist)
   - Log a warning when the fallback triggers (indicates the prompt instruction was ignored)

## Group 2: Verification

2.1 - [x] **Verify existing reviewer tests pass** (`tests/test_reviewer.py`)
   - Run `pytest tests/test_reviewer.py -v` to confirm no regressions
   - Ensure mock-based tests still pass with the new prompt wording and fallback logic
