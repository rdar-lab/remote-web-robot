from json import dumps
import requests

if __name__ == '__main__':

    robot_url = 'http://localhost:8088/run'

    robot_params = \
        {
            "actions": [
                {
                    "what": "open",
                    "url": "https://www.whatismybrowser.com/detect/what-is-my-user-agent/"
                },
                {
                    "what": "read",
                    "field_xpath": "//div[@id='detected_value']",
                    "param_name": "detected_agent"
                }
            ]
        }

    response: requests.Response = requests.post(robot_url, data=dumps(robot_params),
                                                headers={"Content-Type": "application/json"})

    print(response.json())
