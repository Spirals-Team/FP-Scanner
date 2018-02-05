import io
import base64
import matplotlib.image as mpimg
from ua_parser import user_agent_parser
import numpy as np

UNKNOWN = "unknown"

class Fingerprint():
    def __init__(self, dict_values):
        self._id = dict_values['_id']
        self.user_agent_js = dict_values["browser"]["userAgent"]
        self.os_ref_js = dict_values["os"]["name"]
        self.browser_ref_js = dict_values["browser"]["name"]

        if self.browser_ref_js == 'Chromium':
            self.browser_ref_js = 'Chrome'

        try:
            self.browser_version_ref_js = dict_values["browser"]["version"]
        except:
            parsed_ua = user_agent_parser.Parse(dict_values["browser"]["userAgent"])
            self.browser_version_ref_js = int(parsed_ua["user_agent"]["major"])

        if "." in self.browser_version_ref_js:
            self.browser_version_ref_js = int(self.browser_version_ref_js.split(".")[0])

        self.platform = dict_values["os"]["platform"]

        self.languages = dict_values["os"]["languages"]
        try:
            tmp_languages = self.languages.split("~~")
            self.languages = []
            for language in tmp_languages:
                self.languages.append(language)
        except Exception:
            self.languages = []

        # TODO add it to fpscanner script (or not)
        if "unknownImageError" in dict_values:
            self.unknown_image = [int(x) for x in dict_values["unknownImageError"].split(";")]

        self.mq_os = dict_values["scanner"]["mediaQueries"]

        self_tmp_resolution = dict_values["os"]["resolution"].split(",")
        self.screen_resolution = self_tmp_resolution[0]+","+self_tmp_resolution[1]
        self.available_screen_resolution = self_tmp_resolution[2]+","+self_tmp_resolution[3]
        self.color_depth = dict_values["os"]["colorDepth"]
        self.hardware_concurrency = dict_values["os"]["hardwareConcurrency"]
        self.timezone = dict_values["geolocation"]["timezone"]
        self.local_storage = dict_values["browser"]["localStorage"]
        self.cpu_class = dict_values["os"]["processors"]
        self.do_not_track = dict_values["browser"]["dnt"]
        self.oscpu = dict_values["os"]["oscpu"]
        self.mime_types = dict_values["browser"]["mimeTypes"].split(";;")

        if "devicesBlockedByBrave" in dict_values["os"]:
            self.devices_blocked = True
        else:
            self.devices_blocked = False


        fonts_js_split = dict_values["browser"]["fonts"].split(";;")
        self.fonts_js = dict()
        for font in fonts_js_split:
            font_split = font.split("--")
            self.fonts_js[font_split[0]] = True if font_split[1] == "true" else False

        self.plugins = dict_values["browser"]["plugins"]
        try:
            plugins_tmp = self.plugins.split(";;;")
            self.plugins = []
            for plugin in plugins_tmp:
                self.plugins.append(plugin)
        except Exception:
            self.plugins = []

        # Warning : base64 image, maybe use only the hash later
        try:
            self.canvas = dict_values["browser"]["canvas"]
            img_data = self.canvas.split("base64,")[1].encode()
            img = base64.b64decode(img_data)
            img = io.BytesIO(img)
            self.canvas_img = mpimg.imread(img, format='PNG')

        except:
            self.canvas = None
            self.canvas_img = None


        self.web_gl_info = dict_values["os"]["videoCard"].split(";;;")

        # TODO add modernizr
        tmp_modernizr = dict_values["scanner"]["modernizr"]
        self.modernizr = dict()
        for elt in tmp_modernizr:
            v = elt.split("-")
            self.modernizr[v[0]] = True if v[1] == "true" else False


        self.canvas_desc = dict_values["scanner"]["canvasDesc"]
        self.history_desc = dict_values["scanner"]["historyDesc"]
        self.screen_desc = dict_values["scanner"]["screenDesc"]
        self.bind_desc = dict_values["scanner"]["bindDesc"]
        self.timezone_desc = dict_values["scanner"]["timezoneOffsetDesc"]

        # TODO map with new attributes
        if "overwrittenObjects" in dict_values:
            self.overwritten_objects = dict_values["overwrittenObjects"]
            try:
                tmp_overwritten_objects = self.overwritten_objects.split("~~~")
                self.overwritten_objects = []
                for prop in tmp_overwritten_objects:
                    self.overwritten_objects.append(prop)
            except Exception:
                self.overwritten_objects = []

        self.accelerometer = dict_values["scanner"]["accelerometerUsed"]
        try:
            self.product_sub = dict_values["scanner"]["productSub"]
        except KeyError:
            self.product_sub = ''

        self.res_overflow = dict_values["scanner"]["resOverflow"]
        self.etsl = dict_values["scanner"]["etsl"]
        self.touch_support = dict_values["os"]["touchScreen"]

        self.navigator_prototype = dict_values["scanner"]["navigatorPrototype"]
        try:
            navigator_prototype_tmp = self.navigator_prototype.split(";;;")
            self.navigator_prototype = dict()
            for prop in navigator_prototype_tmp:
                elt_tmp = prop.split("~~~")
                self.navigator_prototype[elt_tmp[0]] = elt_tmp[1]
        except Exception:
            self.navigator_prototype = dict()

        self.errors_generated = dict_values["scanner"]["errorsGenerated"]




        self.languages_http = dict_values["browser"]["languageHttp"]
        self.user_agent_http = dict_values["browser"]["userAgentHttp"]
        parsed_ua_http = user_agent_parser.Parse(self.user_agent_http)
        # TODO check if both OS are identical (one is extracted in JS and the other in python)
        self.os_ref_http = parsed_ua_http["os"]["family"]
        self.browser_ref_http = parsed_ua_http["user_agent"]["family"]

        if self.browser_ref_http == 'Chromium':
            self.browser_ref_http = 'Chrome'
        
        if self.os_ref_http == "Fedora":
            self.os_ref_http = "Linux"
            self.os_ref_js = "Linux"

        if 'fpjs2' in dict_values:
            self.fpjs2_consistent = True
            try:
                if dict_values['fpjs2']['has_lied_resolution'] or\
                   dict_values['fpjs2']['has_lied_os'] or\
                   dict_values['fpjs2']['has_lied_browser']:
                    self.fpjs2_consistent = False
            except:
                pass

        if 'augurIncons' in dict_values:
            self.augur_consistent = not dict_values['augurIncons']
        else:
            self.augur_consistent = True


        # Case were we have the ground truth
        if "realBrowser" in dict_values:
            OS_MAPPING = {
                'w7': 'Windows 7',
                'w8': 'Windows 8',
                'linux': 'Linux',
                'andr': 'Android'
            }

            BROWSER_MAPPING = {
                'ie': 'IE',
                'ff': 'Firefox',
                'chr': 'Chrome'
            }

            self.real_browser = BROWSER_MAPPING[dict_values["realBrowser"]]

            if self.browser_ref_http == 'Chrome Mobile' and self.real_browser == 'Chrome':
                self.real_browser = 'Chrome Mobile'
                self.browser_ref_js = self.browser_ref_http

            self.real_os = OS_MAPPING[dict_values["realOS"]]
            self.real_version = dict_values["realVersion"]
            self.countermeasure = dict_values["countermeasure"]

    def __str__(self):
        return 'ID: {}' \
               'Real browser: {}, browser claimed: {}\n' \
               'Real os: {}, os claimed: {}\n' \
               'Real version: {}, version claimed: {}\n' \
               'Countermeasure: {}'.format(
            self._id,
            self.real_browser, self.browser_ref_http,
            self.real_os, self.os_ref_http,
            self.real_version, self.browser_version_ref_js,
            self.countermeasure
        )