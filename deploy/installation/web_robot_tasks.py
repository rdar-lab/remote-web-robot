from fabric.api import *

from web_robot_insatall import WebRobot


def install_web_robot():
    web_robot = WebRobot()
    web_robot.initiate_new_web_robot_server()


def deploy_app():
    web_robot = WebRobot()
    web_robot.stop_app_service()
    web_robot.deploy_app()
    web_robot.install_virtualenv_and_requirements()
    web_robot.restart_app_service()


def install_gui():
    web_robot = WebRobot()
    web_robot.install_gui_pagckages()


def restart_services():
    web_robot = WebRobot()
    web_robot.restart_app_service()
    web_robot.restart_vncserver_service()


def stop_services():
    web_robot = WebRobot()
    web_robot.stop_app_service()
    web_robot.stop_vncserver_service()


def restart_nginx():
    web_robot = WebRobot()
    web_robot.restart_nginx()
