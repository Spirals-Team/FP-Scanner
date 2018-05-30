import numpy as np
import json
from scipy import ndimage
from fingerprint import Fingerprint


def filter_isolated_cells(array, struct):
    """ Return array with completely isolated single cells removed
    :param array: Array with completely isolated single cells
    :param struct: Structure array for generating unique regions
    :return: Array with minimum region size > 1
    """

    filtered_array = np.copy(array)
    id_regions, num_ids = ndimage.label(filtered_array, structure=struct)
    id_sizes = np.array(ndimage.sum(array, id_regions, range(num_ids + 1)))
    area_mask = (id_sizes == 1)
    filtered_array[area_mask[id_regions]] = 0
    return filtered_array


class Scanner:
    SAME_UAS = "SAME_UAS"
    PLATFORM_OS_REF = "PLATFORM_OS_REF"
    MQ_OS = "MQ_OS"
    PLUGINS_OS = "PLUGINS_OS"
    FONTS_OS = "FONTS_OS"
    MULTIMEDIA_DEVICES_BLOCKED = "MULTIMEDIA_DEVICES_OS"
    WEBGL_OS = "WEBGL_OS"
    ERRORS_BROWSER = "ERRORS_BROWSER"
    FEATURES_BROWSER = "FEATURES_BROWSER"
    NAVIGATOR_OVERWRITTEN = "NAVIGATOR_OVERWRITTEN"
    CANVAS_OVERWRITTEN = "CANVAS_OVERWRITTEN"
    SCREEN_OVERWRITTEN = "SCREEN_OVERWRITTEN"
    TIMEZONE_OVERWRITTEN = "TIMEZONE_OVERWRITTEN"
    CANVAS_PIXELS = "CANVAS_PIXELS"
    ACCELEROMETER = "ACCELEROMETER"
    SCREEN_SIZE = "SCREEN_SIZE"
    ETSL = "ETSL"
    PRODUCT_SUB = "PRODUCT_SUB"
    TOUCH_SUPPORT = "TOUCH_SUPPORT"
    EMOJI = "EMOJI"

    ANALYSES = [
        SAME_UAS, PLATFORM_OS_REF, MQ_OS, PLUGINS_OS, FONTS_OS, WEBGL_OS,
        ERRORS_BROWSER, FEATURES_BROWSER, NAVIGATOR_OVERWRITTEN,
        CANVAS_OVERWRITTEN, SCREEN_OVERWRITTEN, TIMEZONE_OVERWRITTEN,
        CANVAS_PIXELS, ACCELEROMETER, ETSL, PRODUCT_SUB,
        TOUCH_SUPPORT, EMOJI
    ]

    OS_ANALYSES = {
        SAME_UAS, PLATFORM_OS_REF, MQ_OS, PLUGINS_OS, FONTS_OS, MULTIMEDIA_DEVICES_BLOCKED, WEBGL_OS,
        ACCELEROMETER, TOUCH_SUPPORT, EMOJI
    }

    BROWSER_ANALYSES = {
        ERRORS_BROWSER, FEATURES_BROWSER, ETSL, PRODUCT_SUB
    }

    def __init__(self, number_wrong_fonts, number_wrong_features, number_transparent_pixels):
        self.font_to_os = dict()
        with open("./experiments/fonts_linked.csv", "r") as f:
            for line in f:
                l_split = line.split(",")
                self.font_to_os[l_split[0]] = l_split[1]

        self.number_wrong_fonts = number_wrong_fonts
        self.number_wrong_features = number_wrong_features
        self.number_transparent_pixels = number_transparent_pixels

        self.caniuse_features = self.__read_caniusefeatures()

    def should_be_consistent(self, fingerprint: Fingerprint):
        """
            Used only for testing purpose
            Given a fingerprint with classical attributes +
            ground truth attributes (os, browser, version)
            returns True if the fingerprint should be considered
            as having an inconsistency, else False
        """

        return fingerprint.countermeasure == "no"

    def check_fingerprint(self, fingerprint: Fingerprint, run_all=True, only_pixels=False):
        """
            Analyze if a fingerprint fp has an inconsistency
            Returns a list of AnalysisResult objects containing
            the details of each analysis
        """
        analyses_results = []
        if not only_pixels:
            analyses_results.append(self.__are_uas_identical(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__is_platform_os_ref_consistent(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__are_mq_os_consistent(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__are_plugins_consistent_os(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__is_webgl_consistent_os(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__are_font_consistent_os(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__are_devices_blocked(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__is_etsl_consistent_browser(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__is_product_sub_consistent_browser(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__are_errors_consistent_browser(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__are_features_consistent_browser(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__is_navigator_overwritten(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__is_canvas_overwritten(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__is_timezone_overwritten(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__is_screen_overwritten(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__is_accelerometer_consistent(fingerprint))
            if analyses_results[-1].is_consistent or run_all:
                analyses_results.append(self.__is_touch_support_consistent(fingerprint))

        if run_all or only_pixels or analyses_results[-1].is_consistent:
            analyses_results.append(self.__are_canvas_pixels_consistent(fingerprint, all_tests=False))

        return analyses_results

    def guess_real_info(self, fingerprint: Fingerprint, analyses_results):
        """
            If fingerprint has an inconsistency, tries to guess real information
            such as browser family, browser version and OS
        """

        failed_os_analyses = set()
        failed_browser_analyses = set()

        mq_weight = 1
        platform_weight = 1
        fonts_weight = 1
        plugins_weight = 1
        webgl_weight = 1

        for analysis in analyses_results:
            if analysis.name in Scanner.OS_ANALYSES and \
                    not analysis.is_consistent:
                failed_os_analyses.add(analysis)
            elif analysis.name in Scanner.BROWSER_ANALYSES and \
                    not analysis.is_consistent:
                failed_browser_analyses.add(analysis)

        # We try to guess the real OS value
        # we define a list of possible real OSes
        # at the end we make a sort of vote
        real_os = []
        if len(failed_os_analyses) == 0 and len(failed_browser_analyses) == 0:
            # We detected no OS inconsistencies
            # We take the value from the UA
            real_os.append((fingerprint.os_ref_js, 1000))
        else:
            # Schade, the user lied
            # We try to guess its real OS
            # Except by voting, we don't try to mix different tests to infer information

            # we start with media queries, since it is the hardest to spoof
            # In theory, if we are sure from the fact that a browser is firefox
            # we could also learn from non matching media queries
            # in our case we only consider matching media queries
            if fingerprint.mq_os[0]:
                real_os.append(("Mac OS X", mq_weight))
            elif fingerprint.mq_os[1]:
                real_os.append(("Windows XP", mq_weight))
            elif fingerprint.mq_os[2]:
                real_os.append(("Windows Vista", mq_weight))
            elif fingerprint.mq_os[3]:
                real_os.append(("Windows 7", mq_weight))
            elif fingerprint.mq_os[4]:
                real_os.append(("Windows 8", mq_weight))
            elif fingerprint.mq_os[5]:
                real_os.append(("Windows 10", mq_weight))

            # we continue with the plugins
            extensions = {".so", ".dll", ".plugin"}
            str_plugins = "-".join(fingerprint.plugins)
            found_extension = None
            for extension in extensions:
                if extension in str_plugins:
                    found_extension = extension

            # if a plugin filename extension has been found, we make the hypothesis
            #  it is linked to the real OS
            # .dll doesn't enable to have exact version of Windows
            extension_to_os = {
                ".so": "Linux",
                ".dll": "Windows",
                ".plugin": "Mac OS X"
            }
            if found_extension is not None:
                real_os.append((extension_to_os[found_extension], plugins_weight))

            # if incons between ua and platform, trust platform since it is probably a user agent spoofer
            is_platform_incons = len(
                [(not x.is_consistent and x.name == Scanner.PLATFORM_OS_REF) for x in failed_browser_analyses]) == 1
            if is_platform_incons:
                platforms_to_os = {
                    "Linux i686": "Linux",
                    "Linux x86_64": "Linux",
                    "FreeBSD amd64": "FreeBSD",
                    "FreeBSD i386": "FreeBSD",
                    "OpenBSD amd64": "OpenBSD",
                    "OpenBSD i386": "OpenBSD",
                    "NetBSD amd64": "NetBSD",
                    "Win32": "Windows",
                    "Win64": "Windows",
                    "MacIntel": "Mac OS",
                    "iPhone": "iOS",
                    "iPad": "iOS",
                    "Linux armv7l": "Android",
                    "Linux i686": "Android",
                    "Linux armv8l": "Android"
                }
                try:
                    real_os.append((platforms_to_os[fingerprint.platform], platform_weight))
                except KeyError:
                    real_os.append(("Other", platform_weight))

            # We continue with fonts
            os_family_to_count = dict()
            for font in fingerprint.fonts_js:
                if fingerprint.fonts_js[font]:
                    try:
                        if self.font_to_os[font] not in os_family_to_count:
                            os_family_to_count[self.font_to_os[font]] = 1
                        else:
                            os_family_to_count[self.font_to_os[font]] += 1
                    except KeyError:
                        # We pass, it just means the font has not been collected
                        pass

            os_most_likely = None
            for os_family in os_family_to_count:
                # we set a minimum number of fonts at 8
                if os_family_to_count[os_family] > 8 and \
                        (os_most_likely is None or
                         os_family_to_count[os_most_likely] < os_family_to_count[os_family]):
                    os_most_likely = os_family

            # Once again for Windows we don't have the detail of the version
            if os_most_likely is not None:
                real_os.append((os_most_likely, fonts_weight))

            # Go on with webGL
            renderer_subtr_to_os_family = {
                "ANGLE": "Windows",
                "OpenGL": "Mac OS X",
                "Mesa": "Linux",
                "Gallium": "Linux"
            }

            for renderer_substr in renderer_subtr_to_os_family:
                if renderer_substr in fingerprint.web_gl_info[0] or \
                        renderer_substr in fingerprint.web_gl_info[1]:
                    real_os.append(
                        (renderer_subtr_to_os_family[renderer_substr],
                         webgl_weight
                         )
                    )
                    break

        # We continue with the browser
        # We try to guess the real browser family and version
        # we first determine the real browser family
        # once we have the browser family we use the detected features
        # to infer the version
        real_browser_family = None
        real_browser_version = []
        if len(failed_browser_analyses) == 0 and len(failed_os_analyses) == 0:
            real_browser_family = fingerprint.browser_ref_js
            real_browser_version = [fingerprint.browser_version_ref_js]
        else:
            # we start with etsl
            if fingerprint.etsl == 39:
                real_browser_family = "Internet Explorer"
            elif fingerprint.etsl == 33:
                # we ignore Opera for the moment
                # onopera... event to detect it
                # otherwise we could use feature detection
                real_browser_family = "Chrome"
            elif fingerprint.etsl == 37:
                # need to distinguish safari and firefox
                # we use productSub for this
                if fingerprint.product_sub == "20030107":
                    real_browser_family = "Safari"
                else:
                    real_browser_family = "Firefox"

            # now we try to detect real version
            # There may be problem since we don't detect mobile version
            #  of browsers such as Chrome mobile
            # if it is chrome we may also try for Opera
            browser_version_to_count_features = dict()
            for feature in fingerprint.modernizr:
                if feature in self.caniuse_features:
                    if real_browser_family in self.caniuse_features[feature]:
                        for browser_version in self.caniuse_features[feature][real_browser_family]:
                            if browser_version not in browser_version_to_count_features:
                                browser_version_to_count_features[browser_version] = 1
                            else:
                                browser_version_to_count_features[browser_version] += 1

            version_most_likely = None
            for browser_version in browser_version_to_count_features:
                if version_most_likely is None:
                    version_most_likely = browser_version
                elif browser_version_to_count_features[browser_version] > \
                        browser_version_to_count_features[version_most_likely]:
                    version_most_likely = browser_version

            for browser_version in browser_version_to_count_features:
                if browser_version_to_count_features[browser_version] == \
                        browser_version_to_count_features[version_most_likely]:
                    real_browser_version.append(browser_version)

        # we compute the winner of the vote for real os
        # special case if only windows and one of them is windows + version
        os_to_count_votes = dict()
        max_vote = None
        for vote in real_os:
            os_vote = vote[0]
            if "Windows" in os_vote:
                os_vote = "Windows"

            if vote[0] not in os_to_count_votes:
                os_to_count_votes[os_vote] = vote[1]
            else:
                os_to_count_votes[os_vote] += vote[1]

            if max_vote is None or \
                    os_to_count_votes[os_vote] > os_to_count_votes[max_vote]:
                max_vote = os_vote

        if max_vote is None:
            max_vote = fingerprint.os_ref_js

        if max_vote == "Windows":
            for vote in real_os:
                # don't remove whitespace after "Windows"
                if "Windows " in vote[0]:
                    max_vote = vote[0]

                # edge case for Windows 8.1
                if "Windows 8" in max_vote:
                    max_vote = "Windows 8"

        real_os = max_vote

        # Special cases for Brave
        for prop in fingerprint.navigator_prototype:
            if "return handler" in fingerprint.navigator_prototype[prop]:
                real_browser_family = "Brave"
                break

        if real_os == "Android" and fingerprint.canvas_img is None:
            real_browser_family = "Brave"
        elif real_os == "Android" and real_browser_family == "Chrome":
            real_browser_family = "Chrome Mobile"

        return real_os, real_browser_family, real_browser_version

    def __are_uas_identical(self, fingerprint: Fingerprint):
        """
            Analysis name: SAME_UAS
            Checks if ua http and ua navigator are the same
        """
        # if browser is IE we don't check for equality of UA
        # we only check that both UAs reflect the same browser and OS
        if fingerprint.browser_ref_js == 'IE':
            is_consistent = (fingerprint.browser_ref_js == fingerprint.browser_ref_http) and \
                            (fingerprint.os_ref_js == fingerprint.os_ref_http)
        else:
            is_consistent = fingerprint.user_agent_js == fingerprint.user_agent_http
        return AnalysisResult(Scanner.SAME_UAS, is_consistent, data={})

    def __is_platform_os_ref_consistent(self, fingerprint: Fingerprint):
        """
            Analysis name: PLATFORM_OS_REF
            Checks if navigator platform attribute is consistent with OS
            using user agent
        """
        os_to_platforms = {
            "Linux": ["Linux i686", "Linux x86_64"],
            "Ubuntu": ["Linux x86_64", "Linux i686"],
            "Fedora": ["Linux i686", "Linux x86_64"],
            "FreeBSD": ["FreeBSD amd64", "FreeBSD i386", "OpenBSD amd64"],
            "OpenBSD": ["OpenBSD amd64", "OpenBSD i386"],
            "NetBSD": ["NetBSD amd64"],
            "Windows 7": ["Win32", "Win64"],
            "Windows 8": ["Win32", "Win64"],
            "Windows 8.1": ["Win32", "Win64"],
            "Windows 10": ["Win32", "Win64"],
            "Windows Vista": ["Win32", "Win64"],
            "Mac OS": ["MacIntel"],
            "Other": ["Other", "PlayStation 4", "PlayStation 3", "Nintendo Wii"],
            "Windows Phone OS": ["ARM", "Win32"],
            "Windows Phone": ["ARM", "Win32"],
            "Windows RT": ["ARM"],
            "iOS": ["iPhone", "iPad"],
            "Android": ["Linux armv7l", "Linux i686", "Linux armv8l"],
            "Firefox OS": ['unknown'],
            'PLAYSTATION': ['PlayStation 3']
        }

        is_consistent = fingerprint.platform in os_to_platforms[fingerprint.os_ref_js]
        data = {"os": fingerprint.os_ref_js, "platform": fingerprint.platform}
        return AnalysisResult(Scanner.PLATFORM_OS_REF, is_consistent, data)

    def __are_mq_os_consistent(self, fingerprint: Fingerprint):
        """
            Analysis name: MQ_OS
            Check if media queries about OS are consistent
            with the OS displayed in the user agent
            It also detects inconsistency with the browser (Firefox)
        """
        inconsistent = False
        data = dict()
        # we test if one one the media query is true and the browser
        #  is not firefox
        found = False
        for mq in fingerprint.mq_os:
            if mq:
                found = True
                break

        if found and (fingerprint.browser_ref_js != "Firefox" or (fingerprint.browser_ref_js == "Firefox" and \
                                                                  fingerprint.browser_version_ref_js > 57)):
            # starting at version 58, these media queries don't exist anymore either in normal mode or when
            # fingerprinting protection is activated
            # When fingerprinting protection is activated the UA change the version to 52 which triggers a true positive
            data["not_firefox"] = True
            inconsistent = True

        # mq_os[0] tests mac OS X special theme
        if fingerprint.mq_os[0] and fingerprint.os_ref_js != "Mac OS X":
            data["mq_failed"] = "Mac OS X"
            inconsistent = True

        if fingerprint.browser_ref_js == 'Firefox' and fingerprint.browser_version_ref_js < 58:
            # mq_os[1] tests Windows XP
            if not inconsistent and \
                    (fingerprint.mq_os[1] and fingerprint.os_ref_js != "Windows XP") or \
                    (not fingerprint.mq_os[1] and fingerprint.os_ref_js == "Windows XP" and \
                     (fingerprint.browser_ref_js == "Firefox" or found)):
                data["mq_failed"] = "Windows XP"
                inconsistent = True

            # mq_os[2] tests Windows Vista
            if not inconsistent and \
                    (fingerprint.mq_os[2] and fingerprint.os_ref_js != "Windows Vista") or \
                    (not fingerprint.mq_os[2] and fingerprint.os_ref_js == "Windows Vista" and \
                     (fingerprint.browser_ref_js == "Firefox" or found)):
                data["mq_failed"] = "Windows Vista"
                inconsistent = True

            # mq_os[3] tests Windows 7
            if not inconsistent and \
                    (fingerprint.mq_os[3] and fingerprint.os_ref_js != "Windows 7") or \
                    (not fingerprint.mq_os[3] and fingerprint.os_ref_js == "Windows 7" and \
                     (fingerprint.browser_ref_js == "Firefox" or found)):
                data["mq_failed"] = "Windows 7"
                inconsistent = True

            # mq_os[4] tests Windows 8
            # Warning, may fail if Windows 8.1?
            if not inconsistent and \
                    (fingerprint.mq_os[4] and "Windows 8" not in fingerprint.os_ref_js) or \
                    (not fingerprint.mq_os[4] and "Windows 8" in fingerprint.os_ref_js and \
                     (fingerprint.browser_ref_js == "Firefox" or found)):
                data["mq_failed"] = "Windows 8"
                inconsistent = True

            # Duplicate for Windows 8.1
            # May be removed later
            if not inconsistent and \
                    (fingerprint.mq_os[4] and fingerprint.os_ref_js != "Windows 8.1") or \
                    (not fingerprint.mq_os[4] and fingerprint.os_ref_js == "Windows 8.1" and \
                     (fingerprint.browser_ref_js == "Firefox" or found)):
                data["mq_failed"] = "Windows 8.1"
                inconsistent = True

            # mq_os[5] tests Windows 10
            if not inconsistent and \
                    (fingerprint.mq_os[5] and fingerprint.os_ref_js != "Windows 10") or \
                    (not fingerprint.mq_os[5] and fingerprint.os_ref_js == "Windows 10" and \
                     (fingerprint.browser_ref_js == "Firefox" or found)):
                data["mq_failed"] = "Windows 10"
                inconsistent = True

        return AnalysisResult(Scanner.MQ_OS, not inconsistent, data)

    def __are_plugins_consistent_os(self, fingerprint: Fingerprint):
        """
            Analysis name: PLUGIN_OS
            Checks if plugins filename extension is consistent with the OS
            On Linux it should be .so
            On Mac .plugin
            On Windows .dll
            Some OSes shouldn't have plugins such as Android or iOS
        """
        # Default case, everything is forbidden
        forbidden_extensions = [".so", ".dll", ".plugin"]
        if "arm" in fingerprint.platform.lower():
            forbidden_extensions = [".so", ".dll", ".plugin"]
        elif fingerprint.os_ref_js != "Windows Phone" and "Windows" in fingerprint.os_ref_js:
            forbidden_extensions = [".so", ".plugin"]
        elif "Mac OS X" in fingerprint.os_ref_js:
            forbidden_extensions = [".so", ".dll"]
        elif "Linux" in fingerprint.os_ref_js or "Ubuntu" in fingerprint.os_ref_js:
            forbidden_extensions = [".dll", ".plugin"]

        forbidden_extension_found = False
        data = dict()
        str_plugins = "-".join(fingerprint.plugins)
        for extension in forbidden_extensions:
            if extension in str_plugins:
                forbidden_extension_found = True
                data["forbidden_extension"] = extension
                break

        consistent = not forbidden_extension_found
        return AnalysisResult(Scanner.PLUGINS_OS, consistent, data)

    def __is_webgl_consistent_os(self, fingerprint: Fingerprint):
        """
            Analysis name: WEBGL_OS
            Checks if webgl vendor is consistent with the OS claimed
        """
        inconsistent = False
        data = dict()

        # iPad/iPhone: vendor : Apple Inc. Apple A8 GPU
        # Apple Inc. / Apple A9X GPU
        # Apple Inc. /Apple A8X GPU, A7...
        # For ipad : Imagination Technologies / PowerVR SGX 543 , seems to be also available for other brands
        # Adreno, MaliXXX, Tegra X for android or windows phone
        # see http://www.anandtech.com/show/6426/ipad-4-gpu-performance-analyzed-powervr-sgx-554mp4-under-the-hood

        if fingerprint.os_ref_js != "Windows Phone" and \
                "Windows" in fingerprint.os_ref_js or \
                fingerprint.os_ref_js == "Mac OS X" or \
                fingerprint.os_ref_js == "Linux" or \
                fingerprint.os_ref_js == "Ubuntu":
            forbidden_extensions = ["ANGLE", "OpenGL", "Mesa", "Gallium", "Qualcomm"]
            # False negative with Windows Phone, change this later
            if "Windows" in fingerprint.os_ref_js:
                forbidden_extensions = ["OpenGL", "Mesa", "Gallium", "Qualcomm"]
            elif "Mac OS X" in fingerprint.os_ref_js:
                forbidden_extensions = ["ANGLE", "Mesa", "Gallium", "Qualcomm"]
            elif "Linux" in fingerprint.os_ref_js or "Ubuntu" in fingerprint.os_ref_js:
                forbidden_extensions = ["ANGLE", "OpenGL", "Qualcomm"]

            for extension in forbidden_extensions:
                if extension in fingerprint.web_gl_info[1] or \
                        extension in fingerprint.web_gl_info[0]:
                    inconsistent = True
                    data["forbidden_extension"] = extension
                    break

        return AnalysisResult(Scanner.WEBGL_OS, not inconsistent, data)

    def __are_font_consistent_os(self, fingerprint: Fingerprint):
        """
            Analysis name: FONTS_OS
            Checks if fonts that should be present only on certain
            OS are present on the claimed OS
        """
        # Default case is "other"
        # For the moment we do it only for desktop devices
        os_family = "Other"
        if fingerprint.os_ref_js != "Windows Phone" and "Windows" in fingerprint.os_ref_js:
            os_family = "Windows"
        elif "Ubuntu" in fingerprint.os_ref_js or "Linux" in fingerprint.os_ref_js or "Fedora" \
                in fingerprint.os_ref_js:
            os_family = "Linux"
        elif "Mac OS X" in fingerprint.os_ref_js:
            os_family = "Mac OS X"

        nb_wrong_fonts = 0
        nb_right_fonts = 0
        data = dict()
        data["wrong_fonts"] = []
        for font in fingerprint.fonts_js:
            if fingerprint.fonts_js[font]:
                try:
                    if self.font_to_os[font] != os_family:
                        nb_wrong_fonts += 1
                        data["wrong_fonts"].append(font)
                    else:
                        nb_right_fonts += 1
                except KeyError:
                    # We pass, it just means the font has not been collected
                    pass

        data["nb_wrong_fonts"] = len(data["wrong_fonts"])
        data["nb_right_fonts"] = nb_right_fonts
        consistent = nb_wrong_fonts < self.number_wrong_fonts
        return AnalysisResult(Scanner.FONTS_OS, consistent, data)

    def __are_devices_blocked(self, fingerprint: Fingerprint):
        """
            Checks if multimedia devices have been blocked by Brave desktop
        """
        return AnalysisResult(Scanner.MULTIMEDIA_DEVICES_BLOCKED, not fingerprint.devices_blocked, {})

    def __are_errors_consistent_browser(self, fingerprint: Fingerprint):
        """
            Checks if the errors are consistent with the browser claimed
        """
        inconsistent = False
        errors_failed = []
        # errors_generated[3] = error.description
        # errors_generated[4] = error.number
        # it is only available on IE browsers
        if not inconsistent and \
                (fingerprint.errors_generated[3] != None and \
                 (fingerprint.browser_ref_js != "IE" and \
                  fingerprint.browser_ref_js != "Edge")) or \
                (fingerprint.errors_generated[3] == None and \
                 (fingerprint.browser_ref_js == "IE" or \
                  fingerprint.browser_ref_js == "Edge")):
            inconsistent = True
            errors_failed.append("IE Edge exception signature")

        # errors_generated[1] = error.filename
        # its is only available on Firefox based browsers
        # works also for firefox mobile
        if (fingerprint.errors_generated[1] != None and "Firefox" not in fingerprint.browser_ref_js) or \
                (fingerprint.errors_generated[1] == None and "Firefox" in fingerprint.browser_ref_js):
            inconsistent = True
            errors_failed.append("Firefox filename")

        # errors_generated[7] = websocket error.toString()
        if ("An invalid or illegal" in fingerprint.errors_generated[7] and \
            "Firefox" not in fingerprint.browser_ref_js) or \
                ("An invalid or illegal" not in fingerprint.errors_generated[7] and \
                 "Firefox" in fingerprint.browser_ref_js):
            inconsistent = True
            errors_failed.append("Firefox websocket constructor")

        if ("Failed to construct 'WebSocket'" in fingerprint.errors_generated[7] and \
            "Chrome" not in fingerprint.browser_ref_js and \
            fingerprint.browser_ref_js != "Opera") or \
                ("Failed to construct 'WebSocket'" not in fingerprint.errors_generated[7] and \
                 ("Chrome" in fingerprint.browser_ref_js or fingerprint.browser_ref_js == "Opera")):
            inconsistent = True
            errors_failed.append("Chrome websocket constructor")

        if (fingerprint.res_overflow[1] == "InternalError" and \
            "Firefox" not in fingerprint.browser_ref_js) or \
                (fingerprint.res_overflow[1] != "InternalError" and \
                 "Firefox" in fingerprint.browser_ref_js):
            inconsistent = True
            errors_failed.append("Firefox stack overflow")

        if (fingerprint.res_overflow[1] == "RangeError" and \
            "Chrome" not in fingerprint.browser_ref_js and \
            fingerprint.browser_ref_js != "Opera" and \
            "Safari" not in fingerprint.browser_ref_js) or \
                (fingerprint.res_overflow[1] != "RangeError" and \
                 ("Chrome" in fingerprint.browser_ref_js or \
                  fingerprint.browser_ref_js == "Opera" or \
                  "Safari" in fingerprint.browser_ref_js)):
            inconsistent = True
            errors_failed.append("Chrome stack overflow")

        # check message depending on the browser
        # errors_generated[0] = error.message
        # it depends on the browser

        data = {"errors_failed": ";".join(errors_failed)} if errors_failed else {}
        return AnalysisResult(Scanner.ERRORS_BROWSER, not inconsistent, data)

    def __read_caniusefeatures(self):
        """
            Parse json file provided by caniuse.com
            to translate it to a more usable structure
        """
        with open("./ressources/data_caniuse_v2.json", "r") as f:
            caniuse_data = json.load(f)

        caniuse_browser_to_ua_parser = {
            "chrome": "Chrome",
            "opera": "Opera",
            "firefox": "Firefox",
            "safari": "Safari",
            "edge": "Edge",
            "ie": "IE",
            "and_chr": "Chrome mobile",
            "android": "Android",
            "ie_mob": "IE Mobile",
            "ios_saf": "Mobile Safari"
        }
        features = dict()

        for feature in caniuse_data["data"]:
            features[feature] = dict()
            for browser in caniuse_data["data"][feature]["stats"]:
                if browser in caniuse_browser_to_ua_parser:
                    features[feature][caniuse_browser_to_ua_parser[browser]] = set()
                    for version in caniuse_data["data"][feature]["stats"][browser]:
                        versions_split = version.split("-")
                        if len(versions_split) > 1:
                            version_key = versions_split[0].split(".")[0]
                        else:
                            version_key = version.split(".")[0]

                        if self.__is_feature_supported(
                                caniuse_data["data"][feature]["stats"][browser][version]
                        ):
                            features[feature][caniuse_browser_to_ua_parser[browser]].add(version_key)

        return features

    def __is_feature_supported(self, feature_data):
        return "y" in feature_data or "a" in feature_data

    def __are_features_consistent_browser(self, fingerprint: Fingerprint):
        """
            Analysis name: FEATURES_BROWSER
            Test if modernizr features are consistent with features
            that browser claimed in user agent should have
            Data are extracted from caniuse.com website
        """
        #  https://raw.githubusercontent.com/Fyrd/caniuse/master/data.json
        # Only 48 features have exactly the same name between Modernizr
        # And caniuse. Maybe remove the others.
        nb_errors = 0
        errors_features = []
        for feature in fingerprint.modernizr:
            if feature in self.caniuse_features:
                if fingerprint.browser_ref_js in self.caniuse_features[feature]:
                    should_feature_be_available = (
                            str(fingerprint.browser_version_ref_js) in \
                            self.caniuse_features[feature][fingerprint.browser_ref_js]
                    )
                    if fingerprint.modernizr[feature] != should_feature_be_available:
                        errors_features.append(feature)
                        nb_errors += 1

        # 0 might be a bit too strict, maybe allow one error?
        # consistent = nb_errors <= 4
        consistent = nb_errors <= self.number_wrong_features
        data = {"errors_features": ";".join(errors_features)} if errors_features else {}
        return AnalysisResult(Scanner.FEATURES_BROWSER, consistent, data)

    def __is_navigator_overwritten(self, fingerprint: Fingerprint):
        """
            Analysis name: NAVIGATOR_OVERWRITTEN
            Checks if there exists at least 1 methods or attributes
            of navigator object that has been overwritten
        """
        consistent = True
        overwritten_properties = []
        for prop_name in fingerprint.navigator_prototype:
            if fingerprint.navigator_prototype[prop_name] != "" and \
                    "native" not in fingerprint.navigator_prototype[prop_name]:

                if prop_name == "constructor" and fingerprint.browser_ref_http == 'IE':
                    continue  # special case for IE

                consistent = False
                overwritten_properties.append("%s;;;%s" %
                                              (
                                                  prop_name,
                                                  fingerprint.navigator_prototype[prop_name]
                                              )
                                              )

        data = {"properties_overwritten": "~~".join(overwritten_properties)} if \
            overwritten_properties else {}
        return AnalysisResult(Scanner.NAVIGATOR_OVERWRITTEN, consistent, data)

    def __is_canvas_overwritten(self, fingerprint: Fingerprint):
        """
            Analysis name: CANVAS_OVERWRITTEN
            Checks if a property/method used to generate a
            canvas has been overwritten
        """
        consistent = "native code" in fingerprint.canvas_desc
        return AnalysisResult(Scanner.CANVAS_OVERWRITTEN, consistent, data={})

    def __is_screen_overwritten(self, fingerprint: Fingerprint):
        """
            Analysis name: SCREEN_OVERWRITTEN
            Returns True if screen object has been overwritten,
            else False
        """
        consistent = fingerprint.screen_desc != "error"
        return AnalysisResult(Scanner.SCREEN_OVERWRITTEN, consistent, data={})

    def __is_timezone_overwritten(self, fingerprint: Fingerprint):
        """
            Analysis name: TIMEZONE_OVERWRITTEN
            Returns True if Date.getTimezoneOffset method has been
            overwritten, else False
        """
        consistent = fingerprint.timezone_desc != "error"
        return AnalysisResult(Scanner.TIMEZONE_OVERWRITTEN, consistent, data={})

    def __is_accelerometer_consistent(self, fingerprint: Fingerprint):
        """
            Analysis name: ACCELEROMETER
            Returns True if accelerometer is consistent with the
            class of device, i.e mobile device and accelerometer is True,
            or computer device and accelerometer is False
        """
        is_mobile_device = fingerprint.os_ref_js == "Android" or \
                           fingerprint.os_ref_js == "iOS" or \
                           fingerprint.os_ref_js == "Windows Phone"

        consistent = True
        if is_mobile_device and not fingerprint.accelerometer:
            consistent = False
        elif not is_mobile_device and fingerprint.accelerometer:
            consistent = False

        return AnalysisResult(Scanner.ACCELEROMETER, consistent, data={})

    def __is_product_sub_consistent_browser(self, fingerprint: Fingerprint):
        """
            Analysis name: PRODUCT_SUB
            Returns True if productSub is "20030107" on
            Chrome, Safari and Opera
        """
        consistent = True
        data = {}
        if (fingerprint.browser_ref_js == "Chrome" or \
            fingerprint.browser_ref_js == "Chrome Mobile" or \
            fingerprint.browser_ref_js == "Safari" or \
            fingerprint.browser_ref_js == "Opera") and \
                fingerprint.product_sub != "20030107":
            consistent = False
        elif fingerprint.browser_ref_js != "Other" and \
                fingerprint.browser_ref_js != "Chrome" and \
                fingerprint.browser_ref_js != "Chrome Mobile" and \
                fingerprint.browser_ref_js != "Safari" and \
                fingerprint.browser_ref_js != "Opera" and \
                fingerprint.product_sub == "20030107":
            consistent = False

        if not consistent:
            data["product_sub"] = fingerprint.product_sub

        return AnalysisResult(Scanner.PRODUCT_SUB, consistent, data)

    def __is_etsl_consistent_browser(self, fingerprint: Fingerprint):
        """
            Analysis name: ETSL
            Checks if eval.toString().length is equals to:
            - 37 for Safari and Firefox
            - 39 for IE and Edge
            - 33 for Chrome, Opera
        """
        browser_to_length = {
            "Safari": 37,
            "Firefox": 37,
            "Internet Explorer": 39,
            "Edge": 39,
            "Chrome": 33,
            "Opera": 33
        }

        consistent = True
        data = {}
        if fingerprint.browser_ref_js in browser_to_length and \
                browser_to_length[fingerprint.browser_ref_js] != fingerprint.etsl:
            consistent = False
            data["etsl"] = fingerprint.etsl

        return AnalysisResult(Scanner.ETSL, consistent, data)

    def __is_touch_support_consistent(self, fingerprint: Fingerprint):
        """
            Analysis name: TOUCH_SUPPORT
            Checks if touch support is active only on Android, iOS, or
            Windows Phone devices
        """
        consistent = True
        data = {}
        if (fingerprint.os_ref_js == "Android" or \
            fingerprint.os_ref_js == "iOS" or \
            fingerprint.os_ref_js == "Windows Phone") and \
                fingerprint.touch_support == "0;false;false":
            consistent = False
            data["touch_support"] = fingerprint.touch_support

        return AnalysisResult(Scanner.TOUCH_SUPPORT, consistent, data)

    def __are_canvas_pixels_consistent(self, fingerprint: Fingerprint, all_tests=True):
        """
            Analysis name: CANVAS_PIXELS
            Checks if pixels of a canvas have been modified by an extension
        """
        inconsistent = False
        data = {}
        # new version from raw image

        if fingerprint.canvas_img is None:
            data["canvas_blocked"] = True
            inconsistent = True
        else:
            img = fingerprint.canvas_img
            img.setflags(write=1)

            if not inconsistent or all_tests:
                # We look for specific colors as defined in the canvas definition
                colors_to_detect = [[255, 102, 0, 100]]
                MAX_NORM = 4
                failed_one_color = False
                for color in colors_to_detect:
                    nb_equals = 0
                    nb_close = 0
                    for v1 in fingerprint.canvas_img:
                        for v2 in v1:
                            norm = np.linalg.norm(v2[:3] - color[:3])
                            if norm < MAX_NORM and norm > 0:
                                nb_close += 1
                            if np.array_equal(v2[:3] - color[:3], [0, 0, 0]):
                                nb_equals += 1
                    if nb_equals == 0 or \
                            7 * nb_equals < nb_close:
                        failed_one_color = True
                        if not "color_failed" in data:
                            data["color_failed"] = []
                        data["color_failed"].append(str(color))

                if failed_one_color:
                    inconsistent = True

            if not inconsistent or all_tests:
                # We count the number of transparent pixels
                id_t = img[:, :, 3] > 0
                id_f = img[:, :, 3] == 0
                img[id_t, 3] = 1
                img[id_f, 3] = 0
                img = img[:, :, 3]
                nb_zeros = 24000 - np.count_nonzero(img)

                # if nb_zeros < 4000 or nb_zeros == 24000:
                if nb_zeros < self.number_transparent_pixels or nb_zeros == 24000:
                    inconsistent = True
                    data["zeros_pixels"] = nb_zeros

            if not inconsistent or all_tests:
                # We count the number of isolated cells
                filtered_array = filter_isolated_cells(img, struct=np.ones((3, 3)))
                diff_mat = img != filtered_array
                isolated_pixels = np.nonzero(diff_mat == True)
                if len(isolated_pixels[0]) > 8:
                    inconsistent = True
                    data["isolated_pixels"] = len(isolated_pixels[0])

        return AnalysisResult(Scanner.CANVAS_PIXELS, not inconsistent, data)


class AnalysisResult:

    def __init__(self, name, is_consistent, data):
        """
            name is a string representing the point being analysed
            is_consistent is True if the analysis checked no inconsistency, else False
            data is a dict containing data relative to the analysis
        """
        self.name = name
        self.is_consistent = is_consistent
        self.data = data

    def __str__(self):
        str_repr = "Analysis: %s\nResult: %s\n" % (self.name, self.is_consistent)
        data_repr = "\n".join([("%s: %s" % (x, self.data[x])) for x in self.data])
        return str_repr + data_repr
