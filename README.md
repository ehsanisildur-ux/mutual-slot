# MutualSlot

A standalone GenLayer primitive for matching applicants to capacity-limited placements using source-grounded preferences on both sides.

The deployment fixes applicant identities, placement identities/capacities and the publisher repository. Any caller can submit a commit-pinned public preference record and its SHA-256 commitment. Leader and validators independently fetch the complete record and derive every profile's acceptable tiers, explicit rejections and unknown candidates. Exact normalized agreement determines whether allocation can proceed.

Resolved profiles feed applicant-proposing deferred acceptance. Each placement retains its most preferred applicants up to its seat capacity; displaced applicants continue proposing. The contract checks mutual acceptability, seat limits and the absence of blocking pairs before storing the result and proposal trace. It does not simply rank applicants globally or maximize a one-sided score.

## Source and consensus

Every candidate must appear exactly once in a profile's tiers, rejected list or unknown list. Omitted candidates are unknown unless the source explicitly rejects unlisted options. Undeclared comparisons are not silently converted into ties. Quotes must occur verbatim, and validators separately assess their material support for the entire profile. A quote containing names alone is insufficient.

Validators independently re-fetch bytes, verify hashes, extract profiles without leader decisions in their extraction prompt, compare every tier and acceptance/unknown partition, and judge every leader anchor against full source. Changed rankings, invented acceptance and unknown-to-rejection changes always reject the leader. There are no confidence tolerances.

Within a declared tie, constructor roster order breaks the tie. The output is stable under these refined strict preferences, and therefore weakly stable under the declared ties. It is not a claim of strong or super stability, random fairness, maximum-cardinality matching with ties, or optimal total welfare.

## Interface

| Method | Effect |
|---|---|
| `match(url, sha256)` | Fetches and interprets a new publisher record; stores MATCHED or REVIEW batch |
| `get_state()` | Returns policy and all batches, source commitments, profiles, results and traces |

If any candidate remains unknown, the entire batch becomes REVIEW with no assignment. Empty known acceptable lists can yield a valid empty matching. Records never overwrite previous results. There are no owners, proposal approvals, graph revisions, certificates or consumption rights.

Bounds: 1..5 applicants, 1..4 placements, 1..5 seats per placement, 8000 source bytes and 8 distinct batches. Only `records/*.md` at 40-character Git commits in the fixed publisher repository is accepted. Duplicate document hashes are rejected. The permissionless batch bound can be consumed by callers choosing distinct existing publisher records; deploy a new bounded batch ledger when exhausted. Source changes and network/model failures do not create successful business outcomes.

## Trust and use

Use cases include mentor placement, cohort assignment and shared programme seats where both sides' declared preferences matter. Results allocate logical seats in this ledger; they do not force external participation or reserve physical capacity. A downstream application can read the chosen batch's mapping.

The publisher is the authority for declarations. Git commit/SHA-256 checks bind publisher bytes, not personal signatures or independently proven consent. The contract does not verify identities or whether people will honor placements. Demonstration records are synthetic. Real deployments should use an appropriate trusted publisher and roster process.

## Checks

```sh
pip install -r requirements.txt
genvm-lint download --version v0.2.16
genvm-lint check contracts/mutual_slot.py --json
pytest tests/direct -q
node scripts/verify-proofs.cjs
```

20 tests include validator replay, unknown gating, mutual rejection, displacement, multi-seat capacities, tied-order normalization, forged anchors, byte changes and an independent exhaustive check of 625 small strict markets. That check enumerates all assignments and verifies stability and applicant optimality without calling the contract's blocking-pair checker. Direct web/LLM responses are mocked; live proofs test actual acquisition and model consensus.

[Contract](contracts/mutual_slot.py) · [Consensus design](docs/consensus.md) · [Onchain proofs](proofs/README.md).

The matching algorithm follows [Gale and Shapley's original 1962 paper](https://www.math.toronto.edu/mccann/assignments/477/GaleShapley62.pdf). The integration of source interpretation, complete two-sided partitions, exact validator equivalence, capacities, replayable traces and bounded batch storage is this contract's mechanism. No new mathematical algorithm is claimed. CLI transport scaffolding is adapted from our earlier contracts; matching source and tests are new.
