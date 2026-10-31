"""Plain-language explanation of an audit result (T99). Until Muse Spark writes it (T45), fixed templates
are used. Either way the text only holds slots; fill_numbers puts in the numbers from physics/, and the
same banned-phrase check applies. Never a judgement on whether a video is real or generated."""
from __future__ import annotations

from .output_check import fill_numbers

EARTH_G = 9.81
MODEL_NAMES = {"free_flight": "free flight", "bounce": "bouncing", "pendulum": "pendulum", "vehicle": "car driving"}

TEMPLATES = {
    "flight_consistent": "Assuming free flight, the object falls with an apparent gravity of {g:1} m/s², "
                         "close to Earth's {earth_g:1} m/s². The motion is consistent with that model.",
    "flight_inconsistent_g": "Assuming free flight, the object falls as if gravity were {g:2} m/s², "
                             "{ratio:2} times Earth's, closest to {body}. The motion is inconsistent with "
                             "real-time free flight on Earth. This does not say why.",
    "vehicle_consistent": "Assuming a car driving on a road, it moves at about {kmh:0} km/h and speeds up or "
                          "slows down at {ag:2} g, within what tyres can grip. The motion is consistent with that model.",
    "inconsistent": "The motion is inconsistent with the {model} model. Main reason: {reason}. This does not say why.",
    "consistent": "The motion is consistent with the {model} model.",
    "insufficient_data": "This clip cannot be judged against the {model} model: {reason}.",
}


def explain_audit(rec: dict) -> dict:
    n = rec.get("numbers", {})
    model = MODEL_NAMES.get(rec["assumed_model"], rec["assumed_model"])
    reason = (rec.get("reasons") or ["no reason recorded"])[0]
    slots: dict = {"model": model, "reason": reason, "earth_g": EARTH_G}
    key = rec["verdict"]
    g = n.get("g_apparent_m_s2")
    if rec["assumed_model"] == "free_flight" and g is not None:
        slots |= {"g": g, "ratio": g / EARTH_G, "body": rec.get("nearest_body") or "no listed body"}
        if key == "consistent":
            key = "flight_consistent"
        elif key == "inconsistent" and not 0.85 <= g / EARTH_G <= 1.15:
            key = "flight_inconsistent_g"
    if rec["assumed_model"] == "vehicle" and key == "consistent" and n.get("speed_km_h") is not None:
        slots |= {"kmh": abs(n["speed_km_h"]), "ag": n["accel_g"]}
        key = "vehicle_consistent"
    text, chk = fill_numbers(TEMPLATES[key], slots)
    if text is None:  # cannot happen with the fixed templates; keep the result honest if it does
        return {"source": "template", "text": f"Result: {rec['verdict']}."}
    return {"source": "template", "text": text}
