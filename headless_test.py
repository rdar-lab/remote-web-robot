from json import dumps
import requests

if __name__ == '__main__':

    robot_url = 'http://localhost:8088/run'

    robot_params = \
        {
            "actions": [
                {
                    "what": "open",
                    "url": "https://infosimples.github.io/detect-headless/"
                },                {
                    "what": "accept_alert",
                },
                {
                    "what": "read_html",
                    "field_xpath": "//table",
                    "param_name": "result"
                }
            ]
        }

    response: requests.Response = requests.post(robot_url, data=dumps(robot_params),
                                                headers={"Content-Type": "application/json"})

    print(response.json())
