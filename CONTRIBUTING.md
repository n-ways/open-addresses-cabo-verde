# Contributing

Proposals are welcome from municipalities, Correios, INGT, couriers, developers, researchers and residents. This file says what can change and how to propose it; [GOVERNANCE.md](GOVERNANCE.md) says who decides.

## What can change, and what cannot

- **Issued codes never change.** No pull request may move, reuse, renumber or lengthen an issued code, or change how one decodes (engine/SPEC.md §9).
- **The registry is not edited by hand.** `registry/` is exported from the issuer. A wrong entrance, a misclassified building, a demolished house or a missing building is corrected in the N-Ways app ("this is wrong", "Add my home"), where the agreement of independent people settles it, and reaches the registry with the next export.
- **Zone names and plate names** change with the Câmara Municipal's agreement (the Comissão Nacional de Toponímia's for national names). A municipality that wants to rename a zone or choose a flagged plate name writes to hello@nways.ng or opens an issue; the old name stays as an alias and every number stays.
- **The engine, the specification and the server** change by pull request.

## One issuer

Codes are issued by one issuer for the country, so that no number is ever given twice (GOVERNANCE.md, server/README.md). Do not run the registry server with `ISSUE_KEYS` unless the State of Cabo Verde or N-WAYS LIMITED has designated your deployment as the issuer; to issue codes from your own system, use the issuer's API with a key of your own.

## Pull requests

1. Open an issue first for anything larger than a fix, so the change can be discussed.
2. Keep the code standard-library Python 3.9 or later; the engine and the server must run with nothing to install.
3. Run the tests and self-checks, and make sure they pass:

   ```sh
   python3 engine/reference/test_cv.py
   python3 -m unittest server.test_server
   python3 tools/test_tools.py
   python3 tools/build_names.py
   python3 tools/registry_vectors.py --check
   ```

4. A change to the engine updates `engine/test-vectors.json` (`python3 engine/reference/cv_engine.py > engine/test-vectors.json`, then review the difference), raises the specification version in `engine/SPEC.md`, and explains in the pull request why the change is right for Cabo Verde.
5. A change to the API updates `server/openapi.yaml` and `docs/api.md` with real responses.
6. Write comments and documents for a reader who knows addressing but not this code: say what a rule is and why it holds.

By contributing you agree that your contribution is licensed as the part of the repository it changes: Apache-2.0 for code, ODbL 1.0 for data, CC BY 4.0 for documents (LICENSING.md).

## Reporting problems

- A wrong code or place: the N-Ways app, or an issue.
- A security problem: privately to hello@nways.ng ([SECURITY.md](SECURITY.md)).
- Anything else: an issue, or hello@nways.ng.
