| clip | source | assumed_model | result | why | g_apparent | time_factor | implied_size_m | tilt_deg | rms_over_travel | tracked_fraction | tracker | track_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| own_1_IMG_8426.mov | own | free_flight | inconsistent | acceleration points -70 deg away from image-down; track does not follow a constant-acceleration path; apparent g 11.83 m/s^2 is outside 8.34-11.28 | 11.83 | 0.91 | 0.091 | -70.5 | 0.413 | 1.0 | frame_diff | yes |
| own_2_IMG_8429.mov | own | free_flight | inconsistent | acceleration points -71 deg away from image-down; track does not follow a constant-acceleration path; apparent g 11.78 m/s^2 is outside 8.34-11.28 | 11.78 | 0.91 | 0.092 | -71.1 | 0.178 | 1.0 | frame_diff | yes |
| own_3_IMG_8434.mov | own | free_flight | insufficient_data | acceleration is not distinguishable from zero |  |  |  | -56.1 | 0.423 | 1.0 | frame_diff | yes |
| meta_clip1.mp4 | meta_ai | free_flight | inconsistent | acceleration points 132 deg away from image-down; track does not follow a constant-acceleration path; apparent g 0.03 m/s^2 is outside 8.34-11.28 | 0.03 | 17.42 | 12.132 | 132.4 | 0.247 | 1.0 | frame_diff | no |
| meta_clip2.mp4 | meta_ai | free_flight | inconsistent | acceleration points -37 deg away from image-down; apparent g 0.47 m/s^2 is outside 8.34-11.28 | 0.47 | 4.55 | 4.972 | -37.0 | 0.01 | 1.0 | frame_diff | yes |
| meta_clip3.mp4 | meta_ai | free_flight | inconsistent | track does not follow a constant-acceleration path; apparent g 0.17 m/s^2 is outside 8.34-11.28 | 0.17 | 7.62 | 13.948 | -2.4 | 0.081 | 1.0 | frame_diff | yes |
| meta_clip4.mp4 | meta_ai | free_flight | inconsistent | acceleration points -27 deg away from image-down; track does not follow a constant-acceleration path; apparent g 0.09 m/s^2 is outside 8.34-11.28 | 0.09 | 10.44 | 26.137 | -27.2 | 0.042 | 1.0 | frame_diff | no |
| meta_clip5.mp4 | meta_ai | free_flight | inconsistent | acceleration points -167 deg away from image-down; track does not follow a constant-acceleration path; apparent g 1.28 m/s^2 is outside 8.34-11.28 | 1.28 | 2.77 | 1.84 | -166.7 | 0.135 | 1.0 | frame_diff | no |
| meta_clip6.mp4 | meta_ai | free_flight | inconsistent | acceleration points -30 deg away from image-down; track does not follow a constant-acceleration path; apparent g 0.12 m/s^2 is outside 8.34-11.28 | 0.12 | 8.93 | 8.765 | -29.6 | 0.119 | 1.0 | frame_diff | yes |
| manus_clip1.mp4 | manus | free_flight | inconsistent | apparent g 2.55 m/s^2 is outside 8.34-11.28 | 2.55 | 1.96 | 0.924 | -11.2 | 0.004 | 1.0 | frame_diff |  |

Rules: {'diff_threshold': 30.0, 'min_tracked_fraction': 0.8, 'g_tolerance': 0.15, 'max_tilt_deg': 15.0, 'max_rms_fraction': 0.02, 'tracker': 'color_when_named'}.

## Summary

| source | consistent | inconsistent | insufficient_data | refused |
| --- | --- | --- | --- | --- |
| manus | 0 | 1 | 0 | 0 |
| meta_ai | 0 | 6 | 0 | 0 |
| own | 0 | 2 | 1 | 0 |

Q1 trustworthy tracks on own clips: fail
Q2 clear anomaly not explained by tracking or size error: pass (own_1_IMG_8426.mov, own_2_IMG_8429.mov, meta_clip1.mp4, meta_clip2.mp4, meta_clip3.mp4, meta_clip4.mp4, meta_clip5.mp4, meta_clip6.mp4, manus_clip1.mp4)
Q3 one rule set, at most half refused: pass (0/10 refused)
False alarms on own clips (explain each): own_1_IMG_8426.mov, own_2_IMG_8429.mov
All clips in the manifest are listed; none are left out.
