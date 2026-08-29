# Port Checker

- The Python command-line tool is the main product.
- Use `make test`, `make lint`, and `make run ARGS="scan"` for normal checks.
- If working on the Swift app, edit only the newer source under `swift/`.
- Do not edit the older duplicate under `PortCheckerMenuBar/`.
- Scan and confirm the target before stopping any running service.
- Do not commit secrets, local settings, or generated app bundles.
