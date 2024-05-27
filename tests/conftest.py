def pytest_addoption(parser):
    parser.addoption('--multiprocessing', action='store_true', dest="multiprocessing",
                 default=False, help="enable multiprocessing tests with filelock")