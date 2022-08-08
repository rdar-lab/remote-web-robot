import os

from fabric.api import *
from fabric.contrib import files

import helpers
from context import Context


class WebRobot:

    def __init__(self):
        self.context = Context()
        self.context.os = helpers.detect_os()
        self.local_app_dir = self.context.proj_dir.replace('deploy/installation', '')

    def initiate_new_web_robot_server(self):
        self.apt_update_and_upgrade()
        self.install_gui_pagckages()
        self.setup_tigervnc_server()
        self.set_display_param()
        self.install_google_chrome()
        self.deploy_app()
        self.install_virtualenv_and_requirements()
        self.start_app_process()
        self.install_and_initiate_nginx()

    def apt_update_and_upgrade(self):
        helpers.print_title("Update and upgrade to make sure the system running the latest packages")
        sudo("apt update")
        sudo("apt -y upgrade")

    def install_gui_pagckages(self):
        helpers.print_title("Install all the GUI packages")
        sudo("apt -y install ubuntu-desktop")
        sudo("apt -y install gnome-panel gnome-settings-daemon metacity nautilus gnome-terminal")

    def setup_tigervnc_server(self):
        helpers.print_title("Install tigervnc server")
        sudo("apt -y install tigervnc-standalone-server tigervnc-xorg-extension tigervnc-viewer")
        password = os.getenv("vnc_password")
        run("mkdir -m 700 ~/.vnc")
        run("echo {} | vncpasswd -f > /home/ubuntu/.vnc/passwd".format(password))
        run("chmod 0600 /home/ubuntu/.vnc/passwd")
        files.upload_template(filename="vnc_xstartup_conf", destination="/home/ubuntu/.vnc/xstartup", use_jinja=False,
                              template_dir=f"{self.context.templates_dir}",
                              context=vars(self.context),
                              use_sudo=False, backup=False, mode=0o755)
        run("vncserver :1")
        run("vncserver -kill :1")
        service_file = 'vncserver@:1.service'
        put(local_path=self.local_app_dir + service_file, remote_path="/etc/systemd/system/" + service_file,
            use_sudo=True)
        sudo("systemctl daemon-reload")
        sudo("systemctl start vncserver@:1.service")
        sudo("systemctl enable vncserver@:1.service")

    def set_display_param(self):
        run("echo export DISPLAY=:1 >> ~/.bashrc && source ~/.bashrc")
        run("echo export DISPLAY=:1 >> ~/.profile")

    def deploy_app(self):
        if files.exists('/home/ubuntu/web-robot-app'):
            helpers.print_title("Delete old app files")
            run('rm -rf /home/ubuntu/web-robot-app')

        helpers.print_title("Copy app files")
        run("mkdir web-robot-app")
        files_to_copy = ['app.py', 'requirements.txt']
        for file in files_to_copy:
            put(local_path=self.local_app_dir+file, remote_path="/home/ubuntu/web-robot-app/"+file)

    def install_virtualenv_and_requirements(self):
        run("sudo apt -y install python3-pip")
        run("pip install virtualenv")
        with cd("/home/ubuntu/web-robot-app"):
            run("python3 -m virtualenv venv")
            with prefix('source venv/bin/activate'):
                run('pip install -r requirements.txt')
                run('deactivate')

    def start_app_process(self):
        helpers.print_title("Copy nad start web-robot-app service file")
        service_file = 'web-robot-app.service'
        put(local_path=self.local_app_dir + service_file, remote_path="/etc/systemd/system/" + service_file,
            use_sudo=True)
        sudo("systemctl daemon-reload")
        sudo('systemctl start web-robot-app')
        sudo('systemctl enable web-robot-app')

    def stop_app_service(self):
        sudo('systemctl stop web-robot-app')

    def stop_vncserver_service(self):
        sudo('systemctl stop vncserver@:1.service')

    def restart_app_service(self):
        sudo('systemctl restart web-robot-app')

    def restart_vncserver_service(self):
        sudo('systemctl restart vncserver@:1.service')

    def install_and_initiate_nginx(self):
        sudo("apt -y install nginx")
        nginx_config_file = 'nginx_webrobotapp'
        conf_file_name = 'webrobotapp'
        put(local_path=self.local_app_dir + nginx_config_file, remote_path="/etc/nginx/sites-available/" + conf_file_name, use_sudo=True)
        sudo(f"ln -s /etc/nginx/sites-available/{conf_file_name} /etc/nginx/sites-enabled")
        sudo("rm /etc/nginx/sites-enabled/default")
        sudo("systemctl restart nginx")

    def restart_nginx(self):
        sudo("systemctl restart nginx")

    def install_google_chrome(self):
        helpers.print_title("Install google-chrome")
        run("wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb")
        sudo("dpkg -i google-chrome-stable_current_amd64.deb")
        run("rm google-chrome-stable_current_amd64.deb")
