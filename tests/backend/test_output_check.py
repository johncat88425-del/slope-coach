from backend.output_check import check_choice, check_model_text, extract_numbers

TOOL = {"fit": {"v0_m_s": 0.6012, "a_m_s2": 1.42}, "arrival_error_rel": -0.183, "tolerance_rel": 0.15}


def test_grounded_text_passes():
    text = "The fitted initial speed is about 0.60 m/s and arrival was 18.3% early, beyond the 15% tolerance."
    assert check_model_text(text, [TOOL]).ok


def test_invented_number_rejected():
    r = check_model_text("Acceleration was 2.75 m/s².", [TOOL])
    assert not r.ok and "2.75" in r.problems[0]


def test_causal_overclaims_rejected_in_both_languages():
    assert not check_model_text("This proves the user pushed the block.", [TOOL]).ok
    assert not check_model_text("真因一定是摩擦力改變。", [TOOL]).ok
    assert check_model_text("結果與釋放時帶有初速度的假設一致，但仍無法區分時間偏移。", [TOOL]).ok


def test_small_counting_integers_ignored():
    assert check_model_text("There are 2 possible checks; try step 1 first.", [TOOL]).ok


def test_number_extraction_handles_percent_and_unicode_minus():
    vals = [(v, p) for _, v, p in extract_numbers("error −18.3% and 0.6")]
    assert vals == [(-18.3, True), (0.6, False)]


def test_choice_must_be_a_candidate():
    assert check_choice("release_check", ["release_check"]).ok
    assert not check_choice("change_surface", ["release_check"]).ok
    assert check_choice(None, []).ok


def test_authenticity_words_rejected():
    from backend.output_check import check_model_text
    assert not check_model_text("This looks like an AI-generated clip.", []).ok
    assert not check_model_text("這是假影片", []).ok
    assert check_model_text("The motion is not consistent with free flight.", []).ok


def test_fill_numbers_only_from_tool_output():
    from backend.output_check import fill_numbers
    nums = {"g_vs_earth": 0.2614, "nearest_body": "Moon", "implied_object_size_m": 2.4}
    text, chk = fill_numbers("Falls like on the {nearest_body}: {g_vs_earth} x Earth gravity", nums)
    assert chk.ok and text == "Falls like on the Moon: 0.26 x Earth gravity"
    assert fill_numbers("{implied_object_size_m:1} m wide", nums)[0] == "2.4 m wide"
    assert not fill_numbers("Gravity is 0.26 x Earth", nums)[1].ok
    assert not fill_numbers("{g_apparent} m/s2", nums)[1].ok
    assert not fill_numbers("Fake video: {g_vs_earth}", nums)[1].ok


def test_detector_and_any_video_claims_are_banned():
    from backend.output_check import find_banned_phrases

    for text in ("這是 AI 偵測工具", "Works as a lie detector for clips", "It can check any video.",
                 "物理測謊機", "This looks made by Sora"):
        assert find_banned_phrases(text), text
    assert not find_banned_phrases("The motion is inconsistent with free flight under Earth gravity.")
