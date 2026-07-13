# GitHub Loading Verifier Failure 29243918541

- Run: https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/29243918541
- Commit: `1eda8c1859e50943cee523b24afd4b457203a9bd`
- Status: `failure`
- Started: `2026-07-13T10:46:29Z`
- Finished: `2026-07-13T10:47:21Z`

Steps through the six-case open replay, archived COMSOL comparison, and three-level FVM
refinement all passed. Only `Verify archived loading evidence hashes` failed. The manifest had
hashed raw Windows CRLF text bytes and file sizes, while the Ubuntu checkout contained LF text.
Fifty text records therefore differed even though the numerical content was unchanged.

Commit `7224eec` changed text evidence to LF-normalized canonical byte counts and SHA-256 while
retaining raw-byte hashing for binary `.mph` and image files. This run is a CI portability
failure, not a COMSOL or open-solver failure, and remains part of the evidence history.
