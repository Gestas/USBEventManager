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
		self.reload_daemon = "systemctl daemon-reload"

	def disable(self):
		""" Disable the service if it exists """
		logger.debug("Disabling %s.", self.service_name)
		_disable = "systemctl disable " + self.service_name
		actions.run_subprocess([_disable])
		logger.info("%s disabled.", self.service_name)
		if self._check_service():
			logger.info("%s service is still running.", self.service_name)
		return True

	def remove(self):
		""" Delete the service if it exists """
		logger.debug("Removing existing %s service.", self.service_name)
		_reset_failed = "systemctl reset-failed"
		_stop = "systemctl stop " + self.service_name

		self.disable()
		actions.run_subprocess([_stop])
		self.service_path.unlink(missing_ok=True)
		lib_systemd = Path("/usr/lib/systemd/system/")
		lib_systemd = lib_systemd.joinpath(self.service_name)
		lib_systemd.unlink(missing_ok=True)
		actions.run_subprocess([self.reload_daemon, _reset_failed])
		logger.info("Automatic start disabled")

	def _check_service(self):
		""" Return true if the service is active """
		_is_active = "systemctl is-active " + self.service_name
		status = actions.run_subprocess([_is_active])
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

	def create(self) -> bool:
		""" Create a systemd service """
		_start = "systemctl start " + self.service_name
		_enable = "systemctl enable " + self.service_name
		_chmod = "chmod " + str(self.service_mode) + " " + str(self.service_path)
		_exists = "systemctl list-unit-files | grep " + self.service_name
		_service = actions.run_subprocess([_exists])
		if _service:
			self.remove()
		self._make_systemd_service_file()
		# Activate the service
		actions.run_subprocess([_chmod, self.reload_daemon, _enable, _start])
		if self._check_service():
			logger.info("Automatic start enabled, %s is running.", self.service_name)
			return True
		else:
			logger.error("Service failed to start. Check `systemctl status %s` for details.", self.service_name)
			return False


class LaunchD(object):
	""" Create a MacOS service """

	def __init__(self):
		self._service_name = "org.gestas.USBEventManager"
		self._service_path = Path("/System/Library/LaunchDaemons")
		self._executable_path = Path("/usr/local/bin/USBEventManager")
		self._service_path = Path(self._service_path.joinpath(self._service_name))
		self._service_path = Path(self._service_path.joinpath(".plist"))

	def _is_active(self):
		""" Return true if the service is active """
		_is_active = "launchctl list | grep " + self._service_name
		_status = actions.run_subprocess([_is_active])
		if _status:
			return True
		else:
			return False

	def _make_plist_file(self):
		_plist = (
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
			f"      <string>{self._service_name}</string>\n"
			f"    <key>Program</key>\n"
			f"      <string>{self._executable_path}</string>\n"
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

		logger.debug("Creating plist file %s", self._service_path)
		with open(self._service_path, "w") as f:
			f.write(_plist)

	def disable(self):
		""" Disable the service without changing its current state """
		if self._is_active():
			_disable = "launchctl load -w " + self._service_path
			actions.run_subprocess([_disable])
			logging.info("Automatic start disabled, %s is still running.", self._service_name)
		else:
			_disable = "launchctl unload -w " + self._service_path
			actions.run_subprocess([_disable])
			logging.info("Automatic start disabled, %s is not running.", self._service_name)

	def remove(self):
		if self._service_path.is_file():
			_unload = "launchctl unload " + self._service_path
			_remove = "launchctl remove" + self._service_name
			actions.run_subprocess([_unload, _remove])
			self._service_path.unlink(missing_ok=True)
			logger.info("%s removed.", self._service_name)
			return True

	def create(self):
		""" Create a LaunchD service"""
		_load = "launchctl load " + self._service_path
		_start = "launchctl start " + self._service_name
		# Delete the service if it exists
		if self._service_path.is_file():
			self.remove()
		self._make_plist_file()
		actions.run_subprocess([_load, _start])
		# Check to make sure it's running
		if self._is_active():
			logger.info("Automatic start enabled, %s is running.", self._service_name)
			return True
		else:
			logger.error("%s failed to start.", self._service_name)
			return False


class WindowsService(object):

	def __init__(self):
		self.service_name = "USBEventManager"
		self.description = "USB Device Event Manager"
		self.service_path = Path("/etc/systemd/system/")
		self.executable_path = Path("/usr/local/bin/USBEventManager")
		self.service_path = self.service_path.joinpath(self.service_name)

	def _make_service(self):
		""" Create a Windows service"""
		_service = (
			f"$credentials = new-object -typename System.Management.Automation.PSCredential "
			f"-argumentlist \"NT AUTHORITY\\LOCAL SYSTEM\"\n"
			f"New-Service -Name \"{self.service_name}\" -BinaryPathName \"{self.executable_path} monitor\" "
			f"-DisplayName \"{self.service_name}\" -Description \"{self.description}\" "
			f"-Credential $credentials -StartupType \"Automatic\"")
		actions.run_subprocess([_service])

	def _is_running(self):
		# TODO
		return True

	def remove(self):
		# TODO
		return True

	def create(self):
		self._make_service()
		if self._is_running():
			logger.info("Automatic start enabled, %s is running.", self.service_name)
			return True
		else:
			logger.error("%s failed to start.", self.service_name)
			return False




