# Ready contribution

Category: Builder -> Intelligent Contracts

Title: MutualSlot: Consensus two-sided stable placement

## Notes / Description

MutualSlot is a GenLayer primitive for two-sided placement matching. Deployment fixes applicants, capacities and a publisher repository. Leader and validators independently fetch full commit-pinned records, verify hashes, and derive acceptable tiers, rejections and unknown candidates for both sides. Validators require exact agreement and independently check source anchors. Any unknown produces REVIEW without assignment. Resolved profiles feed applicant-proposing deferred acceptance; roster order refines declared ties. The contract checks mutual acceptance, seat limits and no blocking pairs, retaining proposal traces and unmatched applicants. StudioNet CLI proofs cover displacement, ties, nonreciprocal rejection and uncertainty. Five finalized MAJORITY_AGREE receipts match onchain reads. Includes pinned GenVM source, 20 tests and an exhaustive 625-market check. Synthetic records demonstrate logical allocation; publisher declarations and external participation remain trust boundaries.

## Evidence links

- Repository: https://github.com/ehsanisildur-ux/mutual-slot
- GenLayer contract source: https://github.com/ehsanisildur-ux/mutual-slot/blob/main/contracts/mutual_slot.py
- Onchain proofs: https://github.com/ehsanisildur-ux/mutual-slot/blob/main/proofs/README.md
- Deployment: https://explorer-studio.genlayer.com/tx/0xd9351f0f11ca4c72c51fc4e46d8e58a5ac9abac500bd2ff66378e8e75de92110

StudioNet contract: `0x5BC314c08111DF5768f4A25AF25E879d910F9acF`.

Notes length: 997 characters. Stability and applicant optimality refer to the refined strict preferences; no strong-stability or maximum-cardinality guarantee under original ties is claimed.
