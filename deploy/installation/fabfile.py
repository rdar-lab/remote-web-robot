from fabric.api import *

import web_robot_tasks


@task
def initiate_new_web_robot_server():
    """
    Initiate Web_robot server
    """
    web_robot_tasks.install_web_robot()


@task
def restart():
    """
    Restarts server
    """
    web_robot_tasks.restart_services()
    web_robot_tasks.restart_nginx()


@task
def deploy_app():
    """
    Deploy new version
    """
    web_robot_tasks.deploy_app()

