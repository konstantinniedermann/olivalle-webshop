from app.services.rate_limit import RateLimiter


def test_allows_up_to_limit():
    rl = RateLimiter(max_requests=3, window_seconds=60)
    assert rl.check("1.1.1.1") is True
    assert rl.check("1.1.1.1") is True
    assert rl.check("1.1.1.1") is True


def test_blocks_over_limit():
    rl = RateLimiter(max_requests=3, window_seconds=60)
    for _ in range(3):
        rl.check("1.1.1.1")
    assert rl.check("1.1.1.1") is False


def test_separate_ips_independent():
    rl = RateLimiter(max_requests=2, window_seconds=60)
    assert rl.check("1.1.1.1") is True
    assert rl.check("2.2.2.2") is True
    assert rl.check("1.1.1.1") is True
    assert rl.check("2.2.2.2") is True
    assert rl.check("1.1.1.1") is False
    assert rl.check("2.2.2.2") is False


def test_window_expires(monkeypatch):
    current = [1000.0]
    monkeypatch.setattr("app.services.rate_limit.time.time", lambda: current[0])
    rl = RateLimiter(max_requests=2, window_seconds=60)
    assert rl.check("1.1.1.1") is True
    assert rl.check("1.1.1.1") is True
    assert rl.check("1.1.1.1") is False
    current[0] += 61
    assert rl.check("1.1.1.1") is True
