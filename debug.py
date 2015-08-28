
# Debugging
TEST = 0

TEMP_TEST = 0
RELAY_TEST = 0
DIST_TEST = 0

try:
    # noinspection PyUnresolvedReferences
    import mydebug

    TEMP_TEST = mydebug.TEMP_TEST
    RELAY_TEST = mydebug.RELAY_TEST
    DIST_TEST = mydebug.DIST_TEST
except ImportError:
    pass
except AttributeError:
    pass
