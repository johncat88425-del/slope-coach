| clip | source | assumed_model | result | why | g_apparent | time_factor | implied_size_m | tilt_deg | rms_over_travel | tracked_fraction | tracker | track_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| own_1_IMG_8426.mov | own | free_flight | inconsistent | acceleration points -70 deg away from image-down; track does not follow a constant-acceleration path; apparent g 11.83 m/s^2 is outside 8.34-11.28 | 11.83 | 0.91 | 0.091 | -70.5 | 0.413 | 1.0 | frame_diff |  |
| own_2_IMG_8429.mov | own | free_flight | inconsistent | acceleration points -71 deg away from image-down; track does not follow a constant-acceleration path; apparent g 11.78 m/s^2 is outside 8.34-11.28 | 11.78 | 0.91 | 0.092 | -71.1 | 0.178 | 1.0 | frame_diff |  |
| own_3_IMG_8434.mov | own | free_flight | insufficient_data | acceleration is not distinguishable from zero |  |  |  | -56.1 | 0.423 | 1.0 | frame_diff |  |

Rules: {'diff_threshold': 30.0, 'min_tracked_fraction': 0.8, 'g_tolerance': 0.15, 'max_tilt_deg': 15.0, 'max_rms_fraction': 0.02, 'tracker': 'color_when_named'}.

## Summary

| source | consistent | inconsistent | insufficient_data | refused |
| --- | --- | --- | --- | --- |
| own | 0 | 2 | 1 | 0 |

Q1 trustworthy tracks on own clips: fail
Q2 clear anomaly not explained by tracking or size error: pending (own_1_IMG_8426.mov, own_2_IMG_8429.mov)
Q3 one rule set, at most half refused: pass (0/3 refused)
False alarms on own clips (explain each): own_1_IMG_8426.mov, own_2_IMG_8429.mov
All clips in the manifest are listed; none are left out.
