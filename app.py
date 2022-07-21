import json
import logging
import os
from random import random
from time import sleep
from uuid import uuid4

from flask import Flask, request, Response
from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
import undetected_chromedriver as uc

app = Flask(__name__)

_logger = logging.getLogger(__name__)
_CAPTURE_SCREENSHOTS = False
_HEADLESS = False
_DEFAULT_BROWSER = "chrome"
_DEFAULT_DELAY = "random"
_DEFAULT_WAIT_FOR_ELEMENT_SEC = 30
_RANDOM_DELAY_MAX_SEC = 5


def create_app():
    logging.basicConfig(level=logging.INFO)
    if _CAPTURE_SCREENSHOTS:
        os.makedirs("screenshots", exist_ok=True)
    return app


def _run_action(driver, action, props):
    _logger.info("Running action - {} with props {}".format(action, props))
    try:
        what = action["what"]
        if what == "open":
            driver.get(action["url"])
        elif what == "send":
            obj = driver.find_element(By.XPATH, action["field_xpath"])
            param_name = action["param_name"]
            obj.send_keys(props[param_name])
        elif what == "read":
            obj = driver.find_element(By.XPATH, action["field_xpath"])
            param_name = action["param_name"]
            props[param_name] = obj.text
        elif what == "read_html":
            obj = driver.find_element(By.XPATH, action["field_xpath"])
            param_name = action["param_name"]
            props[param_name] = obj.get_attribute('innerHTML')
        elif what == "click":
            obj = driver.find_element(By.XPATH, action["field_xpath"])
            obj.click()
        elif what == "accept_alert":
            try:
                driver.switch_to.alert.accept()
            except NoAlertPresentException:
                pass
        elif what == "dismiss_alert":
            try:
                driver.switch_to.alert.dismiss()
            except NoAlertPresentException:
                pass
        else:
            raise Exception("Unknown 'what' {}".format(what))

        return props
    except Exception:
        _logger.exception("Error running action. Full PAGE HTML={}".format(driver.page_source))
        raise


def _run(config):
    _logger.info("Running with config - {}".format(config))
    driver = None
    try:
        props = config.get("props", {})
        browser = config.get("browser", _DEFAULT_BROWSER)

        step_delay = config.get("step_delay", _DEFAULT_DELAY)

        unique_run_id = str(uuid4())

        _logger.info("Browser init - {}".format(browser))
        if browser == "firefox":
            driver = _create_firefox()
        elif browser == "chrome":
            driver = _create_chrome()
        elif browser == "undetected_chrome":
            driver = _create_undetected_chrome()
        else:
            raise Exception("Unknown browser {}".format(browser))

        driver.implicitly_wait(_DEFAULT_WAIT_FOR_ELEMENT_SEC)
        driver.maximize_window()
        driver.delete_all_cookies()

        _inject_anti_detection_scripts(driver)

        step_num = 1
        for action in config["actions"]:
            _logger.info("Running step {}".format(step_num))
            if _CAPTURE_SCREENSHOTS:
                _capture_screenshot(driver, "screenshots/{}-{}-PRE.png".format(unique_run_id, step_num))
            props = _run_action(driver, action, props)
            if _CAPTURE_SCREENSHOTS:
                _capture_screenshot(driver, "screenshots/{}-{}-POST.png".format(unique_run_id, step_num))
            step_num = step_num + 1
            if step_delay == "random":
                step_delay_num = _RANDOM_DELAY_MAX_SEC * random()
            else:
                step_delay_num = float(step_delay)

            if step_delay_num > 0:
                _logger.info("Sleeping for {} seconds".format(step_delay_num))
                sleep(step_delay_num)

        _logger.info("Finished running, result - {}".format(props))
        return props
    finally:
        if driver is not None:
            driver.close()


# noinspection PyBroadException
def _capture_screenshot(driver, file_name):
    sleep(1)
    try:
        driver.save_screenshot(file_name)
    except Exception:
        _logger.exception("Error taking screenshot")


def _inject_anti_detection_scripts(driver):
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'connection', {get: () => undefined});
        Object.defineProperty(navigator, 'language', {get: () => 'en-US'});
        Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
        Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
        Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'});
        Object.defineProperty(navigator, 'languages', {
          get: function() {
            return ['en-US', 'en'];
          },
        });        
        Object.defineProperty(navigator, 'plugins', {
          get: function() {
            // this just needs to have `length > 0`, but we could mock the plugins too
            return [1, 2, 3, 4, 5];
          },
        });
    
         var inject = function () {
            var overwrite = function (name) {
              const OLD = HTMLCanvasElement.prototype[name];
              Object.defineProperty(HTMLCanvasElement.prototype, name, {
                "value": function () {
                  var shift = {
                    'r': Math.floor(Math.random() * 10) - 5,
                    'g': Math.floor(Math.random() * 10) - 5,
                    'b': Math.floor(Math.random() * 10) - 5,
                    'a': Math.floor(Math.random() * 10) - 5
                  };
                  var width = this.width, height = this.height, context = this.getContext("2d");
                  var imageData = context.getImageData(0, 0, width, height);
                  for (var i = 0; i < height; i++) {
                    for (var j = 0; j < width; j++) {
                      var n = ((i * (width * 4)) + (j * 4));
                      imageData.data[n + 0] = imageData.data[n + 0] + shift.r;
                      imageData.data[n + 1] = imageData.data[n + 1] + shift.g;
                      imageData.data[n + 2] = imageData.data[n + 2] + shift.b;
                      imageData.data[n + 3] = imageData.data[n + 3] + shift.a;
                    }
                  }
                  context.putImageData(imageData, 0, 0);
                  return OLD.apply(this, arguments);
                }
              });
            };
            overwrite('toBlob');
            overwrite('toDataURL');
          };
          inject();   
          
        const getParameter = WebGLRenderingContext.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
          // UNMASKED_VENDOR_WEBGL
          if (parameter === 37445) {
            return 'Intel Open Source Technology Center';
          }
          // UNMASKED_RENDERER_WEBGL
          if (parameter === 37446) {
            return 'Mesa DRI Intel(R) Ivybridge Mobile ';
          }
        
          return getParameter(parameter);
        };

        ['height', 'width'].forEach(property => {
          // store the existing descriptor
          const imageDescriptor = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, property);
        
          // redefine the property with a patched descriptor
          Object.defineProperty(HTMLImageElement.prototype, property, {
            ...imageDescriptor,
            get: function() {
              // return an arbitrary non-zero dimension if the image failed to load
              if (this.complete && this.naturalHeight == 0) {
                return 20;
              }
              // otherwise, return the actual dimension
              return imageDescriptor.get.apply(this);
            },
          });
        });
               
            """)


def _create_undetected_chrome():
    options = uc.ChromeOptions()
    options.headless = True
    _set_chrome_options(options)
    return uc.Chrome(options=options)


def _create_chrome():
    options = ChromeOptions()
    _set_chrome_options(options)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return driver


def _set_chrome_options(options):
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_argument("--start-maximized")
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--incognito')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--user-agent="
                         "Mozilla/5.0 (X11; Linux x86_64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/98.0.4758.80 Safari/537.36")
    if _HEADLESS:
        options.add_argument('--headless')


def _create_firefox():
    options = FirefoxOptions()

    options.set_preference("browser.cache.disk.enable", False)
    options.set_preference("browser.cache.memory.enable", True)
    options.set_preference("browser.cache.offline.enable", False)
    options.set_preference("network.http.use-cache", False)
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference('useAutomationExtension', False)
    options.set_preference('devtools.jsonview.enabled', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.set_preference("general.useragent.override",
                           "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:96.0) "
                           "Gecko/20100101 Firefox/96.0")
    if _HEADLESS:
        options.headless = True

    cap = DesiredCapabilities.FIREFOX
    cap["marionette"] = False

    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options,
                               desired_capabilities=cap)
    return driver


@app.route('/run', methods=['POST'])
def run():
    try:
        config = request.json

        if config is None:
            raise Exception("JSON input is required")

        return {
            "result": _run(config)
        }

    except Exception as exp:
        _logger.exception(exp)
        return Response(json.dumps({"err": repr(exp)}), status=500, mimetype='application/json')


if __name__ == '__main__':
    create_app().run(host='0.0.0.0', port=8088)
