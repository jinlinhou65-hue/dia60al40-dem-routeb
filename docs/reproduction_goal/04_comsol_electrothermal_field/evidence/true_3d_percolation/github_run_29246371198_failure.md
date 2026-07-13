# GitHub Run 29246371198 Failure

The first frozen-pilot dispatch failed before dynamics with LIGGGHTS error
`Unable to calculate region volume`. The center-safe insertion regions had already accounted for
particle radius, and `all_in yes` applied the same exclusion a second time.

Artifact digest:
`sha256:44ae16d0a52c3cfb1e098b7fb8444e63fdae648fb518e009a3d2fbc83ebc04f7`.

The failure is retained as change-control evidence. The follow-up changed only the three insertion
flags to `all_in no`; it did not change a scientific parameter or acceptance gate.

Run URL: https://github.com/jinlinhou65-hue/dia60al40-dem-routeb/actions/runs/29246371198
