from app.database import Database


def test_log_and_recent_newest_first():
    db = Database("sqlite://")
    db.log("person", 0.91)
    db.log("bottle", 0.55)

    rows = db.recent(10)

    assert [r["label"] for r in rows] == ["bottle", "person"]
    assert rows[1]["confidence"] == 0.91


def test_recent_respects_limit():
    db = Database("sqlite://")
    for _ in range(5):
        db.log("cup", 0.5)
    assert len(db.recent(3)) == 3
