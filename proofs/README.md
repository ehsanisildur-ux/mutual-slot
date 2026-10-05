# StudioNet proofs

MutualSlot was deployed through GenLayer CLI on gasless StudioNet (chain 61999).

Contract: `0x5BC314c08111DF5768f4A25AF25E879d910F9acF`.

[Deployment transaction](https://explorer-studio.genlayer.com/tx/0xd9351f0f11ca4c72c51fc4e46d8e58a5ac9abac500bd2ff66378e8e75de92110) · [Successful live run](https://github.com/ehsanisildur-ux/mutual-slot/actions/runs/37278969276) · [Manifest](deployment.json).

All five receipts are FINALIZED, MAJORITY_AGREE and execution-successful. The deployment has five agree votes; each matching transaction has three agree/two idle. Full votes are preserved in receipt JSON.

Source read back from the deployed contract exactly matches published bytes: SHA-256 `e6450f04eab1ef1e77f2e11ea4db024e55cd763b44cf5711aa9c037a50fefad0`.

| Scenario | Transaction | Verified result |
|---|---|---|
| Cascading displacement | [transaction](https://explorer-studio.genlayer.com/tx/0xeec2610f74b7cb6a70a0dbbf50525d667980c8a1bb82d4481d727177a614c812) | ada -> field; ben -> lab; cy unmatched. Five proposals include two displacements. |
| Declared ties | [transaction](https://explorer-studio.genlayer.com/tx/0x6824b507de27453de9531650cfa5bcf5b7889c54c0571c0edd06ac044d6d1f59) | ada -> lab; cy -> field; ben unmatched. Immutable roster order refines ties. |
| Nonreciprocal acceptance | [transaction](https://explorer-studio.genlayer.com/tx/0xffc3fce480585275035c1d0fc6813151756076de35516b2c61935880e1ab12c8) | ben -> lab; ada/cy unmatched; field stays vacant because acceptance is not reciprocal. |
| Undeclared preferences | [transaction](https://explorer-studio.genlayer.com/tx/0x2a8f53947e6d96365138c2a0ef0cefc97f1598f45c212bd42b598e1d1e0f4108) | REVIEW, no assignment or proposal trace. |

Each write was followed by an onchain `get_state` read. Stored results include full normalized profiles, verbatim source anchors, proposal traces, unmatched IDs and zero blocking pairs for resolved batches. REVIEW is unresolved, not a claim that an empty assignment is a stable solution.

Run `node scripts/verify-proofs.cjs`. The offline verifier checks finalized/execution outcomes, source hashes, receipt calldata binding, complete preference partitions and every quote substring. It independently enumerates all possible assignments to confirm stability and applicant optimality under refined strict preferences, then replays each proposal trace. This checks recorded evidence; the CLI run performed live acquisition and state reads, and semantic validators checked anchor relevance.

Fixtures are synthetic. Hashes bind publisher declarations, not personal signatures, physical participation or independently verified identity. Placements are logical allocations. Proof accounts are ephemeral and not retained; future batches are permissionless, within the eight-batch bound. These results do not reserve external programme seats.
