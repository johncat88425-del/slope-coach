"""The fixed catalog of next checks. The model may choose among these; it may not invent new ones."""

CATALOG: dict[str, dict[str, list[str] | str]] = {
    "dimension_check": {
        "title": "Re-measure the slope",
        "steps": [
            "Measure the vertical height h of the slope again with a ruler.",
            "Measure the length L along the slope surface again.",
            "Enter the new values; a new calibration version and a new prediction are saved before the next trial.",
        ],
        "keep_same": ["slider", "surface", "start position", "camera position"],
        "expected_observation": "If the measured dimensions were off, the new prediction should sit closer to the next trial.",
    },
    "release_check": {
        "title": "Repeat with a gate release",
        "steps": [
            "Hold the slider with a flat card at the same start position.",
            "Lift the card straight up without pushing the slider forward.",
            "Film the release section clearly.",
        ],
        "keep_same": ["slope angle", "surface", "start position", "camera position"],
        "expected_observation": "If the earlier trial had a starting push, the fitted initial speed should drop toward zero.",
    },
}
