# Semantic Resolution Laws

These laws are optional reasoning tools, not a conflict taxonomy. Select one only when repository evidence exposes the matching invariant. Use `custom` when a different invariant is required and `none` for a purely mechanical conflict.

## L1. Collapse Evolution Before Transplanting

Reduce an introduce/fix/rename/revert chain to its final observable behavior, then migrate that behavior once.

Prevents superseded implementations from being revived or combined.

## L2. Preserve the Active Owner

Keep the target implementation reached by current construction, registration, and call paths. Add source behavior at that owner or its narrow extension point.

Prevents a stale but textually convenient implementation from replacing the live architecture.

If the scoped source introduces a subsystem with no target equivalent, preserve the source owner or create and connect a target-native owner. “No target owner” means new ownership must be established, not that the source behavior is optional.

## L3. Adapt at One Boundary

When parents use different representations, convert once at the narrowest stable boundary. Keep each side internally consistent.

Prevents dual representations and caller-specific conversion from spreading through the system.

## L4. Preserve a Contract End to End

Trace each required value or event from producer through validation, defaults, transformations, transport, consumers, copies, retries, and terminal paths.

Prevents declarations that survive syntactically but no longer influence observable behavior.

## L5. Compose State Machines Explicitly

List states and transitions from both parents. Construct one coherent transition table before combining implementation, with defined retry, cancellation, failure, and terminal outcomes.

Prevents impossible states, duplicated completion, lost cancellation, and fail-open fallthrough.

## L6. Make Ownership and Lifetime Explicit

Name the owner at creation, transfer, retention, release, failure, cancellation, and shutdown. Repeated terminal events must be harmless or guarded.

Prevents leaks, double release, use-after-release, and late work recreating terminal state.

## L7. Preserve Invariants Across Alternate Paths

Primary, fallback, optimized, retried, empty, and exceptional paths must preserve the same public shape, ownership duties, and accounting rules unless scoped intent says otherwise.

Prevents one branch from silently dropping metadata, cleanup, bounds, or completion behavior.

## L8. Keep Accounting Symmetric and Identity Stable

Every reservation, increment, or admission needs correction, rollback, and completion behavior. Internal identity must not accidentally alias distinct operations.

Prevents drift, capacity leaks, double counting, and cross-operation interference.

## L9. Prove Absorption Through Active Use

Claim target absorption only when a final owner, active caller or registration path, complete mapping of every source-final behavior, and paired target/final contract evidence are all identified.

Prevents real feature loss from being waived because similar-looking code exists.

## L10. Preserve the Stronger Compatible Contract

When parents differ in validation, bounds, ordering, schema, or error behavior, retain the contract required by current target callers and dependencies while adding source intent.

Prevents compatibility regressions hidden by a locally compiling resolution.

## L11. Fail Closed on Evidence

Keep failure, timeout, skipped work, missing prerequisites, and untested behavior distinct from success. Do not mutate the environment merely to produce a green result.

Prevents false confidence and non-reproducible acceptance.

Failing to obtain runtime evidence defers only that evidence. It does not authorize an implementation omission or a preservation claim.

## L12. Re-Derive Callsites From the Merged Signature

When both parents touch the same callable, factory, or error contract, first fix its single merged form, then rewrite every callsite from that form instead of keeping either parent's callsite text. Parameter order, arity, keyword names, accepted argument shapes, and raised types are one contract, and tests are callsites too. Convert a positional callsite to keyword form whenever either parent inserted, removed, or reordered a parameter, and filter forwarded arguments by the resolved signature wherever a factory dispatches through a variable.

Prevents a callsite that merges without conflict, silently keeps the wrong parent's argument order or keyword set, and fails only when its request shape first executes.

## Caller/Callee Re-Pairing Shapes

L12 fails silently. None of these shapes produces a merge conflict, so enumerate
callsites from the merged tree rather than from the diff:

1. a parameter list replaced by an aggregate, or the call absorbed into the callee's own setup, so the old callsite becomes redundant rather than wrong;
2. a new parameter inserted ahead of an existing one, shifting every positional slot;
3. the same parameters ordered differently by each parent, so arity still matches and only a type-dependent operation fails;
4. one parent's caller forwarding arguments that the other parent's implementations do not declare, especially through a factory that dispatches on a variable;
5. one parent adding a raised type that the other parent's handler does not catch;
6. both parents guarding or mutating the same state, so the merged path does it twice and leaves it wrong on the failure branch;
7. one parent narrowing an accepted argument shape that the other parent's callers still produce.

Static signature retrieval reaches shapes 1, 2, and 5 only where the callsite is
syntactically resolvable, and cannot see 3, 4, 6, or 7. Cover the rest by running
the merged tree's own tests for every subsystem that had a conflict and comparing
the failing set against both parents; a test that fails on the merged tree while
passing on a parent is a merge defect, not inherited debt. Tests are callsites too,
so a stale test call is the same defect class rather than a test-only problem.

Known limit: this covers only contracts a test or a request reaches. A callable with
no test and no exercised path stays unverified and must be recorded as deferred; a
clean merge is not evidence.

## Selecting Evidence

Test the failure mode of the chosen law:

- evolution or absorption: compare final behavior and locate active callers;
- boundary or propagation: inspect or execute producer-to-consumer flow;
- state or lifetime: exercise success, failure, retry, cancellation, and repeated terminal events;
- alternate paths or accounting: compare equivalent paths and boundary cases;
- compatibility: exercise current callers, malformed inputs, and error outputs;
- evidence integrity: demonstrate that a negative control fails before accepting a positive result.
