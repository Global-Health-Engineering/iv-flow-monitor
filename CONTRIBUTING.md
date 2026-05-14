# Contributing

Dripito Rev-B is the artefact of a submitted MSc semester project at ETH
Global Health Engineering (2026). Pull requests against this repository
are paused while submission and grading are in progress — issues, bug
reports, and questions are welcome at any time.

## Reporting issues

Open an issue at
[github.com/Gluflex/iv-flow-monitor-v2/issues](https://github.com/Gluflex/iv-flow-monitor-v2/issues).
For safety-relevant defects (drop-detection, alarm logic, firmware state
machine), email Leandro Catarci at `lcatarci@ethz.ch` rather than opening
a public issue — this repository is a research prototype, not a certified
medical device, but please don't broadcast safety findings before they're
fixed.

## Repository licence

- **Code, firmware, docs, data:** [CC BY 4.0](LICENSE-CC-BY-4.0.md)
- **Hardware (KiCad project, custom symbols, most footprints):**
  [CERN-OHL-P 2.0](LICENSE-CERN-OHL-2-PERMISSIVE.md)
- **Three custom KiCad footprints:** [CC BY-SA 4.0](LICENSE-CC-BY-SA-4.0.md) —
  see [`hardware/IV_Flow_Monitor_Footprints.pretty/README.md`](hardware/IV_Flow_Monitor_Footprints.pretty/README.md)
- **CubeMX/HAL files** retain `Copyright (c) STMicroelectronics` headers.

By opening a PR or contributing to an issue thread you agree that your
contribution is licensed under the same terms as the surrounding file(s).

## Branching strategy

- **`v2`** is the integration branch and the deployment source. The Pages
  site, badges, and CI all build from `v2`.
- Feature work happens on short-lived local branches off `v2` (e.g.
  `chore/...`, `feat/...`, `fix/...`).
- Feature branches are merged into `v2` by **fast-forward only** and then
  pushed. PR review is not used (sole maintainer).
- Feature branches stay local and are not pushed to `origin`; only `v2`
  is shared.

## Commit style

- Atomic commits — one concept per commit.
- Conventional-commit prefixes (`feat(scope):`, `fix(scope):`,
  `docs(scope):`, `chore(scope):`, `refactor(scope):`, `revert(scope):`).
- Imperative mood, present tense in the subject line.
- Bodies wrap at ~72 chars; describe the *why*, not the *what*.
- Never use `--no-verify`, `--force`, or `--amend` on already-pushed
  history without an explicit, durable reason.

## Code of Conduct

This project follows the [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct.html).
Be respectful — the project intersects with humanitarian healthcare, and
the contributor base includes clinicians, regulators, and engineering
students. Disagreements are welcome; personal attacks are not.

## Security-sensitive paths

The repository is a medical-device prototype. Three areas have heightened
review expectations:

- `firmware/STM32CubeIDE/InfusionBA2/Core/` — drop-detection state
  machine and alarm logic.
- `hardware/` — schematic, BOM, and PCB layout.
- `docs/decisions/` — Architecture Decision Records. New ADRs follow the
  template in [`docs/decisions/README.md`](docs/decisions/README.md).

## Author

Leandro Catarci · `lcatarci@ethz.ch`
