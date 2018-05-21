def pytest_addoption(parser):
    parser.addoption('--including-search', action='store_true', dest="searchtests",
                     default=False, help="enable search tests")


def pytest_configure(config):
    if not config.option.searchtests:
        # Include `not search` to parameters so that search test do not perform
        setattr(config.option, 'markexpr', 'not search')