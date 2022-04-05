import json
import logging
from random import random
from time import sleep
from uuid import uuid4

from flask import Flask, request, Response
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import undetected_chromedriver as uc

app = Flask(__name__)

_logger = logging.getLogger(__name__)
_CAPTURE_SCREENSHOTS = False


def create_app():
    logging.basicConfig(level=logging.INFO)
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
        elif what == "click":
            obj = driver.find_element(By.XPATH, action["field_xpath"])
            obj.click()
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
        browser = config.get("browser", "firefox")
        step_delay = config.get("step_delay", "random")

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

        driver.implicitly_wait(30)
        step_num = 1
        for action in config["actions"]:
            _logger.info("Running step {}".format(step_num))
            if _CAPTURE_SCREENSHOTS:
                driver.save_screenshot("{}-{}-PRE.png".format(unique_run_id, step_num))
            props = _run_action(driver, action, props)
            if _CAPTURE_SCREENSHOTS:
                driver.save_screenshot("{}-{}-POST.png".format(unique_run_id, step_num))
            step_num = step_num + 1
            if step_delay == "random":
                step_delay_int = int(10 * random())
            else:
                step_delay_int = int(step_delay)

            if step_delay_int > 0:
                _logger.info("Sleeping for {} seconds".format(step_delay_int))
                sleep(step_delay_int)

        _logger.info("Finished running, result - {}".format(props))
        return props
    finally:
        if driver is not None:
            driver.close()


def _create_undetected_chrome():
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument('--headless')
    return uc.Chrome(options=options)


def _create_chrome():
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--user-agent="
                                "Mozilla/5.0 (X11; Linux x86_64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/98.0.4758.80 Safari/537.36")

    # For older ChromeDriver under version 79.0.3945.16
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # For ChromeDriver version 79.0.3945.16 or over
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    # chrome_options.headless = True # also works
    driver = webdriver.Chrome(options=chrome_options)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def _create_firefox():
    options = FirefoxOptions()
    options.headless = True

    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference('useAutomationExtension', False)
    options.set_preference('devtools.jsonview.enabled', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.set_preference("general.useragent.override",
                           "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:96.0) "
                           "Gecko/20100101 Firefox/96.0")

    cap = DesiredCapabilities.FIREFOX
    cap["marionette"] = False

    driver = webdriver.Firefox(options=options, desired_capabilities=cap)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
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
