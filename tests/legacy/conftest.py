def pytest_ignore_collect(path, config):  # pragma: no cover
    # Disable collecting any tests under tests/legacy/*
    return True
