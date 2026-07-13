# Excluded Wrapper-Timeout Attempt

- Case: `fixed_current_multiplier_1`
- Applied voltage: `0.015498244703062427 V`
- COMSOL physical solve: completed in `52 s`
- Mesh: `3316` elements, minimum quality `0.6652`
- Wrapper decision: failed after its 210-second post-run wait

The COMSOL log contains a normal localized termination line and the summary was freshly written.
A diagnostic rerun reproduced the wait after removal of the transient process-count check, which
isolated the cause to Windows PowerShell 5.1 decoding the source file's literal Chinese log marker
inconsistently. This attempt is excluded from the accepted six-case evidence and retained as
workflow-debugging evidence.

The wrapper now requires a fresh summary timestamp and a language-neutral ASCII structure on the
last non-empty log line (`:<seconds> s.`). It still rejects launcher errors, Java/model exceptions,
non-finite summaries, and mismatched applied voltage. The accepted case is rerun from scratch;
these excluded files are not reused.
