# Slope Coach E2E Synthetic Demo Verification (T14)

Automated E2E run of the 4 primary slope inquiry scenarios:

| Case | Scenario | Expected Verdict | Actual Verdict | Candidates | Remarks |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **pushed** | Accidental hand push during release ($v_0 > 0$) | discrepancy | `discrepancy` | `['release_check']` | Recommends barrier release intervention |
| **wrong_height** | Incline measured inaccurately ($h_{real} > h_{typed}$) | discrepancy | `discrepancy` | `['dimension_check']` | Recommends dimension re-measurement |
| **ok** | Clean release matching theoretical parameters | consistent | `consistent` | `[]` | Close alignment with theoretical model |
| **occluded** | Critical release frames obscured by hand | discrepancy | `discrepancy` | None (refused to guess $v_0$) | `the start of the slide is not visible enough to judge the release speed` |

All 4 scenario cases completed successfully with exact scientific guardrails.
