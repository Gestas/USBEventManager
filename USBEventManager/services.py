# Creates a service to start USBEventManager automatically.
import logging
from pathlib import Path

from actions import Actions
from helpers import Helpers

logger = logging.getLogger(__name__)

helpers = Helpers()
app_config = helpers.config
platform = helpers.platform
config_path = helpers.config_path
actions = Actions(app_config=app_config, ignore_custom_command_failure=False)


class SystemD(object):
	def __init__(self):
		self.service_mode = 644
		self.service_name = "USBEventManager.service"
		self.service_path = Path("/etc/systemd/system/")
		self.executable_path = Path("/usr/local/bin/USBEventManager")
		self.service_path = self.service_path.joinpath(self.service_name)

		reset_failed = "systemctl reset-failed"
		reload_daemon = "systemctl daemon-reload"
		stop = "systemctl stop " + self.service_name
		start = "systemctl start " + self.service_name
		enable = "systemctl enable " + self.service_name
		disable = "systemctl disable " + self.service_name
		chmod = "chmod " + str(self.service_mode) + " " + str(self.service_path)
		service_exists = "systemctl list-unit-files | grep " + self.service_name

		# Delete the service if it exists
		service = actions.run_subprocess([service_exists])
		if service:
			logger.debug("Removing existing %s service.", self.service_name)
			actions.run_subprocess([stop, disable])
			self.service_path.unlink(missing_ok=True)
			lib_systemd = Path("/usr/lib/systemd/system/")
			lib_systemd = lib_systemd.joinpath(self.service_name)
			lib_systemd.unlink(missing_ok=True)
			actions.run_subprocess([reload_daemon, reset_failed])

		# Create the service file
		self._make_systemd_service_file()
		# Activate the service
		actions.run_subprocess([chmod, reload_daemon, enable, start])

		# Check to make sure the service is started.
		if not self._is_active():
			actions.run_subprocess([start])
			if not self._is_active():
				logger.error(
					"Service failed to start. Check `systemctl status %s` for details.",
					self.service_name,
				)
				helpers.exiter(1)
		if self._is_active():
			logger.info("%s is running.", self.service_name)
			helpers.exiter(0)

	def _is_active(self):
		""" Return true if the service is active """
		is_active = "systemctl is-active " + self.service_name
		status = actions.run_subprocess([is_active])
		if status == "active":
			return True
		else:
			return False

	def _make_systemd_service_file(self):
		service = (
			f"[Unit]\n"
			f"Description=USBEventManager\n"
			f"Documentation=https://github.com/gestas/USBEventManager\n"
			f"StartLimitIntervalSec=0\n"
			f"\n"
			f"[Service]\n"
			f"Type=simple\n"
			f"Restart=always\n"
			f"RestartSec=2\n"
			f"User=root\n"
			f"ExecStart={self.executable_path} monitor\n"
			f"\n"
			f"[Install]\n"
			f"WantedBy=multi-user.target"
		)
		logger.debug("Creating service file %s", self.service_path)
		with open(self.service_path, "w") as f:
			f.write(service)


class LaunchD(object):
	""" Create a MacOS service """

	def __init__(self):
		self.service_name = "org.gestas.USBEventManager"
		self.service_path = Path("/System/Library/LaunchDaemons")
		self.executable_path = Path("/usr/local/bin/USBEventManager")
		self.service_path = Path(self.service_path.joinpath(self.service_name))
		self.service_path = Path(self.service_path.joinpath(".plist"))

		load = "launchctl load " + self.service_path
		start = "launchctl start " + self.service_name
		unload = "launchctl load " + self.service_path
		remove = "launchctl remove" + self.service_name

		# Delete the service if it exists
		if self.service_path.is_file():
			actions.run_subprocess([unload, remove])

		# Create the plist file
		self._make_plist_file()
		# Load and start the service
		actions.run_subprocess([load, start])

		# Check to make sure it's running
		if self._is_active():
			logger.info("%s is running.", self.service_name)
		else:
			logger.error("%s is not running.", self.service_name)

	def _is_active(self):
		""" Return true if the service is active """
		is_active = "launchctl list | grep " + self.service_name
		status = actions.run_subprocess([is_active])
		if status:
			return True
		else:
			return False

	def _make_plist_file(self):
		plist = (
			f'<?xml version="1.0" encoding="UTF-8"?>\n'
			f'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
			f'<plist version="1.0">\n'
			f"  <dict>\n"
			f"    <key>EnvironmentVariables</key>\n"
			f"    <dict>\n"
			f"      <key>PATH</key>\n"
			f"<string>/usr/local/opt/icu4c/sbin:/usr/local/opt/icu4c/bin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin"
			f":/usr/sbin:/sbin:/Users/admin/go/bin\n "
			f"      </string>\n"
			f"    </dict>\n"
			f"    <key>Label</key>\n"
			f"      <string>{self.service_name}</string>\n"
			f"    <key>Program</key>\n"
			f"      <string>{self.executable_path}</string>\n"
			f"    <key>ProgramArguments</key>\n"
			f"      <string>monitor</string>\n"
			f"    <key>RunAtLoad</key>\n"
			f"      <true/>\n"
			f"    <key>KeepAlive</key>\n"
			f"      <false/>\n"
			f"    <key>LaunchOnlyOnce</key>\n"
			f"      <true/>\n"
			f"  </dict>\n"
			f"</plist>"
		)

		logger.debug("Creating plist file %s", self.service_path)
		with open(self.service_path, "w") as f:
			f.write(plist)


class WindowsService(object):

	def __init__(self):
		self.service_name = "USBEventManager"
		self.description = "USB Device Event Manager"
		self.service_path = Path("/etc/systemd/system/")
		self.executable_path = Path("/usr/local/bin/USBEventManager")
		self.service_path = self.service_path.joinpath(self.service_name)

	def _new_service(self):
		service = (
			f"$credentials = new-object -typename System.Management.Automation.PSCredential "
			f"-argumentlist \"NT AUTHORITY\\LOCAL SYSTEM\"\n"
			f"New-Service -Name \"{self.service_name}\" -BinaryPathName \"{self.executable_path} monitor\" "
			f"-DisplayName \"{self.service_name}\" -Description \"{self.description}\" "
			f"-Credential $credentials -StartupType \"Automatic\"")

		# Create the service
		actions.run_subprocess([service])

