# USB Interface Removal — 5-Pin UART Debug Header Instead

**Date:** 2026-03-12

## Context

The Rev-A-precursor schematic (Fionn Smith) carried a USB-C interface, primarily as a power-input path for the BQ25185 + TPS631000 charging stack that Rev-B later dropped (see [`power-architecture.md`](power-architecture.md): the Li-ion AA architecture has no on-PCB charging). With charging-via-USB no longer needed, USB's role in the Rev-B design reduces to debug and firmware-update transport — uses that are achievable with a simpler interface at lower cost and EMC burden.

## Decision

**Remove USB from Rev-B; replace with a 5-pin UART debug header** exposing TX, RX, GND, 3.3 V, and BOOT0. Firmware-update and bring-up workflows use a USB-UART bridge (FTDI, CP2102, or equivalent) plugged into this header; the BOOT0 pin enables the STM32 system bootloader for DFU-style firmware updates.

## Alternatives considered

- **Retain USB-C (Fionn's design).** Lost on cost and complexity: BOM additions (USB connector, ESD diodes, USB stack firmware maintenance), EMC certification burden, and PCB area for the connector and routing — all for marginal benefit once the charging-input rationale was gone.
- **Remove debug interface entirely (no header).** Would force SWD-only access for every firmware update or log retrieval. Cheaper still, but worse for bring-up and field-debuggability of the prototype batch. Rejected on workflow grounds.

## Consequences

- **Lower BOM cost and PCB complexity.** USB connector and supporting passives removed.
- **No EMC certification burden from USB.** Whatever EMC characterisation Rev-B needs is bounded by the optical front-end and boost-converter sections, not a high-speed serial line.
- **Firmware updates require a USB-UART bridge.** Acceptable at the prototype stage; clinicians do not update firmware in the field.
- **Field firmware update workflow is deferred.** Whether the production path uses UART, SWD, or eventual restored USB is a Rev-C / production decision; not blocking for Rev-B.

## Revisit triggers

- If a production deployment requires field-updateable firmware via a consumer-grade port, USB or a USB-UART bridge cable becomes part of the deployment kit and the interface decision reopens.
- If a future revision restores an on-PCB charging path that requires USB power input, USB returns to the architecture and this ADR is superseded.
