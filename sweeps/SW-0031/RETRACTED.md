# SW-0031 — RETRACTED

The returns matrix for this sweep is identically zero. No variant was
actually evaluated; the scoring pipeline treated an empty matrix as a
valid null result and reported "best Sharpe 0.0, zero variants positive"
as a finding. It is not a finding. It is a failed run.

The same hypothesis was re-run correctly after the bug was fixed:

  SW-0029 -> SW-0032
  SW-0030 -> SW-0033
  SW-0031 -> SW-0034

Cite the replacement, not this record. The pre-registration and its
Bitcoin timestamp remain valid; only the execution failed.

Retracted: 2026-08-30T00:16:00Z
