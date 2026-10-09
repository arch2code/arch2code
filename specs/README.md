# Specs

A spec is the normative description of how a feature works, written from the code. It carries no status, history or plan.

- `spec-block-registration.md`: the instance factory key, how generated code registers and looks up blocks, the registrar files, and the static-archive link requirement.
- `spec-clock-reset-requirements.md`: clocks and resets in YAML, their binding, and the rules `make db` enforces.
- `spec-cpp-module-layout.md`: the C++20 artefact inventory, module identity, the region and slot map, and emission rules.
- `spec-eval-expressions.md`: the `eval:` expression language, its evaluation at `make db`, persistence, and per-language emission.
- `spec-memory-access-modes.md`: memory port access modes, firmware access, port clocks and the generated memory RTL.
- `spec-parameter-inheritance.md`: parameter declaration, variants, container-sourced values and their ownership.
- `spec-project-composition.md`: composing projects: provider selection, file ownership, identity across projects, which top is built, and build and migration order.
- `spec-register-bus-distribution.md`: how routers, routed leaves and address groups become the generated register-bus decode, handlers and firmware address enums.
- `spec-verilated-wrappers.md`: Verilated HDL wrapper files, their names and owners, boundary pin widths, and the build-manifest top records.
- `SIMULATOR_INTEGRATION.md`: building and running a project under VCS and Xcelium.

`plans/` holds only `backlog.md` and open plans.
