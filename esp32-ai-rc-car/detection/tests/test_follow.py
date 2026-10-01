from app.follow import follow_command
from app.schemas import Detection

W, H = 640, 480


def box(label, x1, y1, x2, y2):
    return Detection(label, 0.9, x1, y1, x2, y2)


def test_stops_when_target_not_visible():
    assert follow_command([box("chair", 100, 100, 200, 200)], W, H, "person") == ("S", 0)
    assert follow_command([], W, H, "person") == ("S", 0)


def test_drives_forward_when_centred_and_far():
    assert follow_command([box("person", 280, 200, 360, 300)], W, H, "person", speed=170) == ("F", 170)


def test_stops_when_target_fills_frame():
    assert follow_command([box("person", 120, 40, 520, 440)], W, H, "person") == ("S", 0)


def test_turns_toward_target():
    left = follow_command([box("person", 10, 100, 110, 300)], W, H, "person", turn_speed=140)
    right = follow_command([box("person", 520, 100, 620, 300)], W, H, "person", turn_speed=140)
    assert left == ("L", 140)
    assert right == ("R", 140)


def test_follows_largest_matching_box():
    small_left = box("person", 10, 100, 60, 160)
    big_centre = box("person", 250, 150, 390, 330)
    assert follow_command([small_left, big_centre], W, H, "person")[0] == "F"
