| clip | source | assumed_model | result | why | g_apparent | time_factor | implied_size_m | tilt_deg | rms_over_travel | tracked_fraction | tracker | track_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| own_1_IMG_8426.mov | own | free_flight | consistent |  | 9.62 | 1.01 | 0.112 | -6.0 | 0.008 | 1.0 | color:orange |  |
| own_2_IMG_8429.mov | own | free_flight | consistent |  | 9.82 | 1.0 | 0.11 | 1.1 | 0.004 | 1.0 | color:orange |  |
| own_3_IMG_8434.mov | own | free_flight | inconsistent | apparent g 8.17 m/s^2 is outside 8.34-11.28 | 8.17 | 1.1 | 0.132 | 4.7 | 0.004 | 1.0 | color:orange |  |

Rules: {'diff_threshold': 30.0, 'min_tracked_fraction': 0.8, 'g_tolerance': 0.15, 'max_tilt_deg': 15.0, 'max_rms_fraction': 0.02, 'tracker': 'color_when_named'}.

## Summary

| source | consistent | inconsistent | insufficient_data | refused |
| --- | --- | --- | --- | --- |
| own | 2 | 1 | 0 | 0 |

Q1 trustworthy tracks on own clips: pending
Q2 clear anomaly not explained by tracking or size error: fail
Q3 one rule set, at most half refused: pass (0/3 refused)
False alarms on own clips (explain each): own_3_IMG_8434.mov
All clips in the manifest are listed; none are left out.
