# Streaming-Regime Sample — 2026-05-13

Out-of-envelope capture taken when the first V_50_03 attempt was launched with the roller clamp open too far. The drip set transitioned into a streaming / threading flow regime; the run was aborted at ~141 s and the data was preserved as a separate sample rather than tabulated alongside V_50_01 and V_50_02. Renamed from the `_03_` slot to `_03_streaming_` so the regular `V_50_03` slot could be re-used at a controlled flow rate.

## Data files

```
data/raw/2026-05-13_macro20_50mlh_03_streaming_board1.csv        # firmware DROP rows (66)
data/raw/2026-05-13_macro20_50mlh_03_streaming_board1.log        # raw UART mirror
data/raw/2026-05-13_macro20_50mlh_03_streaming_board1_scale.csv  # scale SIR stream
```

## Bench observation

While the streams were running with the clamp wide open, the chamber outlet transitioned from discrete-drop formation to a near-continuous stream. The optical chain's response to a stream is qualitatively different from its response to discrete drops:

- A stream leaves liquid hanging on the photodiode surface for as long as the stream is intact, producing very long apparent `tau_TOP`.
- When the stream breaks momentarily, the device registers a single "drop" event with a chord time corresponding to the entire intact-stream duration.
- Between break points, the photodiode is continuously occluded, so subsequent drops are missed entirely.

## Numbers (66 drops captured before abort)

| Metric | Value |
|---|---:|
| Duration captured | ~141 s |
| Drops captured | 66 |
| tau_TOP min | 982 µs |
| tau_TOP median | 1313 µs |
| tau_TOP mean | 1737 µs |
| tau_TOP **max** | **9018 µs** (drop_N 727; 7-9× the typical chord) |
| Per-drop V (firmware) range | 0.2-144 µL/drop |
| Approximate flow rate at abort | 269 mL/hr (gravimetric) |

A 9 ms TOP-beam shadow implies the photodiode was occluded for 9 ms — the device's `v_TOP` → `chord` → `volume` chain then reports a "single drop" of ~144 µL, which is physically impossible at macro-20 spec (50 µL nominal). This is the artefact of the stream regime, not a true drop.

## Operating-envelope finding

The dual-beam time-of-flight architecture only works in the **discrete-drop regime**. Above approximately 200 mL/hr with this drip set, the flow transitions to streaming and the chord-time → volume mapping breaks down. The clinical operating envelope for drip-monitoring is below this transition (IV maintenance and bolus rates typically < 150 mL/hr for adult macro-set use), so the regime limit is a documented operating range rather than a defect.

A possible Rev-C software guard: detect implausible `tau_TOP` values (e.g. > 2× the median chord across the rolling drop window) and emit an `EVT,STREAM_DETECTED` event rather than a DROP row. This would prevent the streaming artefact from polluting `V_cal` calibration drops.

## Why we preserved this data

This is the only sample in the 2026-05-13 dataset that captures the *failure mode at the upper edge of the operating envelope*. Discarding it would have left only "everything works" data in the repository. Keeping it (as `_streaming_` to make the regime distinct from the validation runs) documents the boundary.
