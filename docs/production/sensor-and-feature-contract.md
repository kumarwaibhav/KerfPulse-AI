# Sensor and feature contract

The implemented schema is exposed at GET /api/fresh/schema. It names 72 current features and six context fields. Values are publisher ADC-domain completed-cut statistics; physical amps or controller load percentages are not equivalent without a validated conversion and extraction study. Schema haas-cut-summary-v1 and sensor profile piecuch-haas-vf1-summary-v1 describe this release.

Each event carries event_id, asset_id, tool_life_id, sequence_number, cut_completed_at with timezone, source_mode, clock_basis, data_origin, feature_schema_version, sensor_profile_version, context, features and inspection_breaks. Unknown top-level fields and unknown sensor fields are rejected, including future outcome labels. NumberOfCycle must equal sequence_number. Missing channels produce insufficient_evidence. Future timestamps beyond 60 seconds fail validation; evidence older than 300 seconds is stale. Forecast bounds permit slots only when the entire slot-relative horizon lies within eight further cuts.

Source raw cut-boundary/filtering, skewness and kurtosis equivalence require further study before qualifying physical extraction. User-measured input is stored as unsupported_domain pending commissioning. Publisher example input uses measured features, explicit demonstration clock and a source tool excluded from training. The exact reference feature schema is machine-readable via the API.

## Acquisition profile and signal meaning

The reference paper describes 12 current channels sampled at 500 Hz and eight vibration channels at 25 kHz. This application consumes the publisher's completed-cut summaries, not those high-rate raw streams. Current model consumes six statistics per current channel, 72 values in total, with six numeric context fields. Publisher sensor values are in the released acquisition domain; a controller spindle-load percentage is not an interchangeable substitute. [Publisher study](https://doi.org/10.1038/s41597-025-04923-y) and [versioned dataset](https://doi.org/10.6084/m9.figshare.28589216.v1).

| Context | Contract |
|---|---|
| NumberOfCycle | Positive cut ordinal; must equal sequence_number. Tool-life reset requires a new tool_life_id. |
| HardnessMean | Publisher workpiece hardness context; preserve source definition and units. |
| MillingToolType | Publisher category encoded numerically; arbitrary new category is not qualified. |
| ADOC / RDOC | Axial/radial cutting-depth context in the publisher definition. Together with tool and holder, used to check a known recipe. |
| ToolHolderLength | Publisher holder-length setting; preserve geometry and units. |

Every numeric value must be finite and have absolute magnitude at most 1e12. This transport bound is not a physical plausibility validator or an out-of-distribution detector. Missing current fields produce an abstention; extra fields are rejected. A known recipe/profile is an engineering compatibility check, not proof of plant transferability. Self-declared benchmark provenance is not cryptographically authenticated sensor provenance.

## Commissioning checklist before plant scoring

1. Record sensor model, channel mapping, gain, polarity, units, acquisition rate and clock synchronization.
2. Define tool installation/removal identity and authoritative completed-cut boundaries; specify treatment of interrupted and air cuts.
3. Reproduce filtering, clipping checks, missing-sample policy and each statistic's conventions, including standard deviation, skewness and kurtosis.
4. Replay paired reference captures through both extractors; compare values against predeclared tolerances and keep hashes of captures, extractor and configuration.
5. Verify freshness, sequence resets, missing channels and unsupported recipes on the actual source.
6. Collect independent shadow outcomes. Approval of numerical extraction does not approve predictive accuracy or action policy.

Raw extraction and physical commissioning are not implemented by this completed-cut upload slice. An uploaded event with data_origin=user-measured intentionally remains unsupported_domain. Historical example timestamps are substituted demonstration clocks, never fabricated acquisition times.
