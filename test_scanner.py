from fingerprint_data_manager import FingerprintDataManager
from inconsistency_scanner import Scanner

fp_manager = FingerprintDataManager()
scanner = Scanner()

# TODO warning I removed features

# def test_canvas_defender():
#     ALLOWED_TESTS_TO_FAIL = {Scanner.CANVAS_OVERWRITTEN, Scanner.CANVAS_PIXELS, Scanner.EMOJI}
#     # emoji is allowed to fail since when canvas is blank it has a bad prediction
#     fingerprints = fp_manager.get_fingerprints_countermeasure('cd') + fp_manager.get_fingerprints_countermeasure('cfpb')
#
#     print('Testing canvas defender: {:d} fingerprints'.format(len(fingerprints)))
#
#     for fingerprint in fingerprints:
#         tests_failed = []
#         scan_results = scanner.check_fingerprint(fingerprint, run_all=True)
#         results_failed = []
#         for scan_res in scan_results:
#             if not scan_res.is_consistent:
#                 tests_failed.append(scan_res.name)
#                 results_failed.append(scan_res)
#
#         if not set(tests_failed).issubset(ALLOWED_TESTS_TO_FAIL):
#             print('-------------')
#             print(fingerprint)
#             print(tests_failed)
#             for elt in results_failed:
#                 print(elt)
#             print()
#             assert False
#         else:
#             assert True

# def test_user_agent_spoofers():
#     ALLOWED_TESTS_TO_FAIL = {Scanner.PLATFORM_OS_REF, Scanner.PLUGINS_OS, Scanner.ETSL, Scanner.PRODUCT_SUB,
#                              Scanner.ERRORS_BROWSER, Scanner.ACCELEROMETER, Scanner.TOUCH_SUPPORT, Scanner.EMOJI,
#                              Scanner.FONTS_OS, Scanner.MQ_OS, Scanner.SCREEN_SIZE}
#
#     fingerprints = fp_manager.get_fingerprints_countermeasure('uas')
#     print('Testing user agent spoofers: {:d} fingerprints'.format(len(fingerprints)))
#
#     for fingerprint in fingerprints:
#         tests_failed = []
#         scan_results = scanner.check_fingerprint(fingerprint, run_all=True)
#         results_failed = []
#         for scan_res in scan_results:
#             if not scan_res.is_consistent:
#                 tests_failed.append(scan_res.name)
#                 results_failed.append(scan_res)
#
#         if not set(tests_failed).issubset(ALLOWED_TESTS_TO_FAIL):
#             print('-------------')
#             print(fingerprint)
#             print(tests_failed)
#             for elt in results_failed:
#                 print(elt)
#             print()
#             assert False
#         else:
#             assert True

# def test_no_countermeasures():
#     ALLOWED_TESTS_TO_FAIL = {Scanner.EMOJI, Scanner.SAME_UAS} # We allow emoji since it is non deterministic, but ideally it should not fail
#     # Same UAs may fail in case of ie 11
#
#     fingerprints = fp_manager.get_fingerprints_countermeasure('no')
#     print('Testing no countermeasure: {:d} fingerprints'.format(len(fingerprints)))
#
#     for fingerprint in fingerprints:
#         tests_failed = []
#         scan_results = scanner.check_fingerprint(fingerprint, run_all=True)
#         results_failed = []
#         for scan_res in scan_results:
#             if not scan_res.is_consistent:
#                 tests_failed.append(scan_res.name)
#                 results_failed.append(scan_res)
#
#         if not set(tests_failed).issubset(ALLOWED_TESTS_TO_FAIL):
#             print('-------------')
#             print(fingerprint)
#             print(tests_failed)
#             for elt in results_failed:
#                 print(elt)
#             print()
#             assert False
#         else:
#             assert True


# def test_ras_countermeasures():
#     ALLOWED_TESTS_TO_FAIL = {Scanner.MQ_OS, Scanner.ETSL, Scanner.PRODUCT_SUB, Scanner.ERRORS_BROWSER,
#                              Scanner.NAVIGATOR_OVERWRITTEN, Scanner.CANVAS_OVERWRITTEN, Scanner.EMOJI,
#                              Scanner.WEBGL_OS, Scanner.TOUCH_SUPPORT, Scanner.ACCELEROMETER, Scanner.SCREEN_SIZE,
#                              Scanner.FONTS_OS}
#
#     fingerprints = fp_manager.get_fingerprints_countermeasure('rasp') + \
#                    fp_manager.get_fingerprints_countermeasure('ras')
#
#     print('Testing RAS: {:d} fingerprints'.format(len(fingerprints)))
#
#     for fingerprint in fingerprints:
#         tests_failed = []
#         scan_results = scanner.check_fingerprint(fingerprint, run_all=True)
#         results_failed = []
#         for scan_res in scan_results:
#             if not scan_res.is_consistent:
#                 tests_failed.append(scan_res.name)
#                 results_failed.append(scan_res)
#
#         if not set(tests_failed).issubset(ALLOWED_TESTS_TO_FAIL):
#             print('-------------')
#             print(fingerprint)
#             print(tests_failed)
#             for elt in results_failed:
#                 print(elt)
#             print()
#             assert False
#         else:
#             assert True

# def test_brave_countermeasures():
#     ALLOWED_TESTS_TO_FAIL = {Scanner.NAVIGATOR_OVERWRITTEN, Scanner.CANVAS_PIXELS, Scanner.EMOJI}
#     # emoji is allowed since blocking canvas engenders a wrongs prediction with the neural network
#
#     fingerprints = fp_manager.get_fingerprints_countermeasure('brave')
#
#     print('Testing Brave: {:d} fingerprints'.format(len(fingerprints)))
#
#     for fingerprint in fingerprints:
#         tests_failed = []
#         scan_results = scanner.check_fingerprint(fingerprint, run_all=True)
#         results_failed = []
#         for scan_res in scan_results:
#             if not scan_res.is_consistent:
#                 tests_failed.append(scan_res.name)
#                 results_failed.append(scan_res)
#
#         if not set(tests_failed).issubset(ALLOWED_TESTS_TO_FAIL):
#             print('-------------')
#             print(fingerprint)
#             print(tests_failed)
#             for elt in results_failed:
#                 print(elt)
#             print()
#             assert False
#         else:
#             assert True

# def test_firefox_protection_countermeasures():
#     ALLOWED_TESTS_TO_FAIL = {Scanner.MQ_OS, Scanner.EMOJI, Scanner.FONTS_OS, Scanner.WEBGL_OS}
#
#     fingerprints = fp_manager.get_fingerprints_countermeasure('ffp')
#
#     print('Testing Firefox protection: {:d} fingerprints'.format(len(fingerprints)))
#
#     for fingerprint in fingerprints:
#         tests_failed = []
#         scan_results = scanner.check_fingerprint(fingerprint, run_all=True)
#         results_failed = []
#         for scan_res in scan_results:
#             if not scan_res.is_consistent:
#                 tests_failed.append(scan_res.name)
#                 results_failed.append(scan_res)
#
#         if not set(tests_failed).issubset(ALLOWED_TESTS_TO_FAIL):
#             print('-------------')
#             print(fingerprint)
#             print(tests_failed)
#             for elt in results_failed:
#                 print(elt)
#             print()
#             assert False
#         else:
#             assert True

# def test_fp_random():
#     ALLOWED_TESTS_TO_FAIL = {Scanner.CANVAS_PIXELS}
#     fingerprints = fp_manager.get_fingerprints_countermeasure('fpr')
#
#     print('Testing FPRandom: {:d} fingerprints'.format(len(fingerprints)))
#
#     for fingerprint in fingerprints:
#         tests_failed = []
#         scan_results = scanner.check_fingerprint(fingerprint, run_all=True)
#         results_failed = []
#         for scan_res in scan_results:
#             if not scan_res.is_consistent:
#                 tests_failed.append(scan_res.name)
#                 results_failed.append(scan_res)
#
#         if not set(tests_failed).issubset(ALLOWED_TESTS_TO_FAIL):
#             print('-------------')
#             print(fingerprint)
#             print(tests_failed)
#             for elt in results_failed:
#                 print(elt)
#             print()
#             assert False
#         else:
#             assert True


def test_blink():
    ALLOWED_TESTS_TO_FAIL = {}
    fingerprints = fp_manager.get_fingerprints_countermeasure('blink')

    print('Testing Blink: {:d} fingerprints'.format(len(fingerprints)))

    for fingerprint in fingerprints:
        tests_failed = []
        scan_results = scanner.check_fingerprint(fingerprint, run_all=True)
        results_failed = []
        for scan_res in scan_results:
            if not scan_res.is_consistent:
                tests_failed.append(scan_res.name)
                results_failed.append(scan_res)

        if not set(tests_failed).issubset(ALLOWED_TESTS_TO_FAIL):
            print('-------------')
            print(fingerprint)
            print(tests_failed)
            for elt in results_failed:
                print(elt)
            print()
            assert False
        else:
            assert True

