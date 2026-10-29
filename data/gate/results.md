| clip | source | assumed_model | result | why | g_apparent | time_factor | implied_size_m | tilt_deg | rms_over_travel | tracked_fraction | size_trend | tracker | track_ok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| own_1_IMG_8426.mov | own | free_flight | consistent |  | 9.62 | 1.01 | 0.112 | -6.0 | 0.008 | 1.0 | 0.05 | color:orange | yes |
| own_2_IMG_8429.mov | own | free_flight | consistent |  | 9.82 | 1.0 | 0.11 | 1.1 | 0.004 | 1.0 | 0.23 | color:orange | yes |
| own_3_IMG_8434.mov | own | free_flight | inconsistent | apparent g 8.17 m/s^2 is outside 8.34-11.28 | 8.17 | 1.1 | 0.132 | 4.7 | 0.004 | 1.0 | -0.03 | color:orange | yes |
| meta_clip1.mp4 | meta_ai | free_flight | inconsistent | acceleration points 85 deg away from image-down; track does not follow a constant-acceleration path; apparent g 0.85 m/s^2 is outside 8.34-11.28 | 0.85 | 3.39 | 0.46 | 85.4 | 0.23 | 1.0 | -0.39 | color:orange | no |
| meta_clip2.mp4 | meta_ai | free_flight | inconsistent | acceleration points -39 deg away from image-down; track does not follow a constant-acceleration path; apparent g 1.71 m/s^2 is outside 8.34-11.28 | 1.71 | 2.39 | 1.374 | -39.2 | 0.024 | 1.0 | 0.04 | color:orange | yes |
| meta_clip3.mp4 | meta_ai | free_flight | inconsistent | acceleration points -17 deg away from image-down; track does not follow a constant-acceleration path; apparent g 0.26 m/s^2 is outside 8.34-11.28 | 0.26 | 6.12 | 8.977 | -17.0 | 0.099 | 1.0 | -0.28 | color:orange | yes |
| meta_clip4.mp4 | meta_ai | free_flight | inconsistent | acceleration points -27 deg away from image-down; track does not follow a constant-acceleration path; apparent g 0.34 m/s^2 is outside 8.34-11.28 | 0.34 | 5.37 | 6.929 | -27.2 | 0.043 | 1.0 | 0.79 | color:orange | no |
| meta_clip5.mp4 | meta_ai | free_flight | inconsistent | acceleration points -167 deg away from image-down; track does not follow a constant-acceleration path; apparent g 1.73 m/s^2 is outside 8.34-11.28 | 1.73 | 2.38 | 1.364 | -167.1 | 0.152 | 1.0 | -0.64 | color:orange | no |
| meta_clip6.mp4 | meta_ai | free_flight | inconsistent | apparent g 0.12 m/s^2 is outside 8.34-11.28 | 0.12 | 8.93 | 8.762 | -6.2 | 0.018 | 1.0 | -0.3 | color:orange | yes |
| manus_clip1.mp4 | manus | free_flight | refused | object tracked in only 55% of frames |  |  |  |  |  | 0.55 | 1.54 | color:orange |  |

Rules: {'diff_threshold': 30.0, 'min_tracked_fraction': 0.8, 'g_tolerance': 0.15, 'max_tilt_deg': 15.0, 'max_rms_fraction': 0.02, 'tracker': 'color_when_named'}.

## Summary

| source | consistent | inconsistent | insufficient_data | refused |
| --- | --- | --- | --- | --- |
| manus | 0 | 0 | 0 | 1 |
| meta_ai | 0 | 6 | 0 | 0 |
| own | 2 | 1 | 0 | 0 |

Q1 trustworthy tracks on own clips: pass
Q2 clear anomaly not explained by tracking or size error: pass (meta_clip1.mp4, meta_clip2.mp4, meta_clip3.mp4, meta_clip4.mp4, meta_clip5.mp4, meta_clip6.mp4)
Q3 one rule set, at most half refused: pass (1/10 refused)
False alarms on own clips (explain each): own_3_IMG_8434.mov
All clips in the manifest are listed; none are left out.
