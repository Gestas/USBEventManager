import os
import ctypes
import logging
import subprocess

from helpers import Helpers
from usb_helpers import USBTools

usb = USBTools()
helpers = Helpers()

logger = logging.getLogger(__name__)


class Actions(object):
    def __init__(self, app_config, ignore_custom_command_failure=None):
        self.app_config = app_config

        self.device: str = ""
        self.event_type: str = ""
        self.queued_actions: dict = {}
        self.platform = helpers.platform
        self.no_action = self.app_config["no_action"]
        self.platform_specific_default_actions: dict = self.app_config[
            "platform_specific_default_actions"
        ]
        if not ignore_custom_command_failure:
            self.ignore_custom_command_failure = self.app_config["ignore_custom_command_failure"]
        else:
            self.ignore_custom_command_failure = ignore_custom_command_failure

    # Processors
    def trigger_actions(self, device: str, event_type=None):
        """ Trigger the appropriate actions for a given event """

        _actions: dict = {}
        _device_specific = self.app_config["device_specific"]
        self.device = device
        self.event_type = event_type

        d = helpers.usb_device_id_match(_device_specific, device)
        if d:
            actions = _device_specific.get(d, False)
        elif self.platform_specific_default_actions.get(self.platform, False):
            actions = self.platform_specific_default_actions.get(self.platform)
            logger.debug("Using actions for the %s platform.", self.platform)
        else:
            logger.debug("No specialized platform found, using default actions.")
            actions = self.app_config["default_actions"]

        # Filter the actions list for enabled actions.
        for action, state in actions.items():
            if state:
                self.queued_actions[action] = state
        logger.debug("Queued actions: %s", self.queued_actions)

        # Execute each action.
        for action, detail in self.queued_actions.items():
            action = "_" + str(action)
            getattr(Actions, action)(self)

    def run_subprocess(self, cmds, desc="") -> [bool, str]:
        """ Run custom commands """
        _cmds = cmds
        _desc = desc

        def _platform_switcher(cmds):
            """ Used to pick the right subprocess command for the current platform """
            _cmds = cmds
            if _cmd := _cmds.get(self.platform, False):
                return _cmd
            else:
                return False

        def _on_error(result):
            """ Manage an error result from subprocess """
            _result = result
            logger.error(
                "Command returned a non-zero exit code: %s", _result.returncode
            )
            if _result.stdout:
                logger.error("STDOUT: %s\n", _result.stdout)
            if _result.stderr:
                logger.error("STDERR: %s\n", _result.stderr)
            if self.ignore_custom_command_failure:
                return True
            else:
                helpers.exiter(1)

        def _on_success(result):
            """ Manage an successful result from subprocess """
            _result = result
            logger.debug("Command succeeded.")
            if _result.stdout:
                logger.debug("STDOUT: %s", _result.stdout)
                return _result.stdout
            else:
                return True

        def _run_cmd(cmd):
            _cmd = cmd
            _result = None
            _env = {
                "USBEVENTMANAGER_EVENT_TYPE": self.event_type,
                "USBEVENTMANAGER_DEVICE_ID": self.device,
                "USBEVENTMANAGER_PLATFORM": self.platform,
            }
            if self.app_config["custom_command_timeout"] != 0:
                _timeout = self.app_config["custom_command_timeout"]
                try:
                    _result = subprocess.run(
                        _cmd,
                        capture_output=True,
                        text=True,
                        shell=True,
                        timeout=_timeout,
                        env=_env,
                    )
                except subprocess.TimeoutExpired:
                    logger.error("Command timed out. Timeout: %s sec.", _timeout)
                    if self.app_config["ignore_custom_command_failure"]:
                        return True
                    else:
                        helpers.exiter(1)
            else:
                _result = subprocess.run(
                    _cmd, capture_output=True, text=True, shell=True, env=_env
                )
            if _result.returncode == 0:
                _result = _on_success(_result)
            else:
                _result = _on_error(_result)
            return _result

        if type(cmds) == dict:
            if _cmd := _platform_switcher(cmds):
                return _run_cmd(_cmd)
            else:
                logger.warning("%s not supported on %s.", _desc, self.platform)
        else:
            _cmd = cmds
            return _run_cmd(_cmd)

    # Built-in actions go here
    def _clear_memory(self):
        # TODO: This.
        logger.warning("Memory clear is pending implementation.")
        return True
        _desc = "Clear Memory"
        logger.info("Running: " + _desc)
        if self.no_action:
            logger.info("     Skipping...")

    def _clear_swap(self):
        _desc = "Clear Swap"
        logger.info("Running: " + _desc)
        # TODO: Find a way to do this on Darwin and Windows.;
        if self.no_action:
            logger.info("     Skipping...")
            return True
        if self.platform == "Linux":
            _c = "swapoff - a && swapon - a"
            self.run_subprocess(cmds=_c, desc=_desc)
        if self.platform in ["Darwin", "Windows"]:
            logger.warning("Clearing swap isn't supported on %s.", self.platform)

    def _custom_commands(self):
        _desc = "User Specified Custom Commands"
        logger.info("Running: " + _desc)
        _cmds = self.queued_actions["custom_commands"]
        for _cmd in _cmds:
            logger.info('Running command "%s"', _cmd)
            if self.no_action:
                logger.debug("     Skipping...")
            else:
                return self.run_subprocess(cmds=_cmd, desc=_desc)

    def _delete(self):
        _desc = "Filesystem delete"
        logger.info("Running: %s", _desc)
        from pathlib import Path

        _paths = self.queued_actions["delete"]

        def _directory_delete(dir):
            """ Delete a directory"""
            _dir = Path(dir)
            if self.no_action:
                logger.debug("     Skipping delete of %s", str(_dir))
                return True
            else:
                _dir.rmdir()

        def _file_delete(file):
            """ Delete a file """
            _file = Path(file)
            if self.no_action:
                logger.debug("     Skipping delete of %s", str(_file))
                return True
            else:
                _file.unlink()

        for _path in _paths:
            _path = Path(_path)
            _path = _path.expanduser()
            if _path.exists():
                if _path.is_file():
                    # If the path in the config file is a file we delete it directly.
                    _file_delete(_path)
                elif _path.is_dir():
                    # If the path in the config file is a dir we iterate from the bottom up.
                    for _root, _dirs, _files in os.walk(_path, topdown=False):
                        _root = Path(_root)
                        for _file in _files:
                            _file = Path(_file)
                            _file_path = _root.joinpath(_file)
                            _file_delete(_file_path)
                        for _dir in _dirs:
                            _dir = Path(_dir)
                            _dir_path = _root.joinpath(_dir)
                            _directory_delete(_dir_path)
                    # If the path in the config file is a dir and doesn't end in a "/" delete it.
                    if _path[-1] != "/":
                        _directory_delete(_path)
            else:
                logger.warning('Path "%s" doesn\'t exist.', str(_path))

    def _disable_device(self):
        _desc = "Disable USB device"
        if self.event_type == "ADDED":
            logger.info("Running: %s", _desc)
            if self.no_action:
                logger.info("     Skipping...")
                return True
            usb.unbind(self.device)

    def _disable_ports(self):
        # TODO: This.
        logger.warning("Disabling USB ports is pending implementation.")
        return True
        _desc = "Disabling USB port."
        logger.info("Running: " + _desc)
        if self.no_action:
            logger.info("     Skipping...")

    def _filesystem_sync(self):
        _desc = "Filesystem Sync"
        logger.info("Running: " + _desc)
        if self.no_action:
            logger.info("     Skipping...")
            return True
        if self.platform == "Linux":
            os.sync()
        else:
            _cmds = {
                "Darwin": "sync",
                "Windows": "sync",  # Requires https://docs.microsoft.com/en-us/sysinternals/downloads/sync
            }
            self.run_subprocess(cmds=_cmds, desc=_desc)

    def _force_reboot(self):
        _desc = "Forced Reboot"
        logger.info("Running: " + _desc)
        if self.no_action:
            logger.info("     Skipping...")
            return True
        _cmds = {
            "Linux": "/usr/sbin/halt --reboot --force --force",
            "Darwin": "/usr/sbin/reboot -n -q",
            "Windows": "shutdown /r /f /t 0",
        }
        self.run_subprocess(cmds=_cmds, desc=_desc)

    def _force_shutdown(self):
        logger.info("Performing forced shutdown...")
        _desc = "Forced Shutdown"
        if self.no_action:
            logger.info("     Skipping...")
            return True
        _cmds = {
            "Linux": "/usr/sbin/halt --force --force",
            "Darwin": "/usr/sbin/halt -n -q",
            "Windows": "shutdown /f /t 0",
        }
        self.run_subprocess(cmds=_cmds, desc=_desc)

    def _melt(self):
        # TODO: This
        logger.warning("Melting pending implementation.")
        return True
        logger.info("Melting UsbEventManager...")
        if self.no_action:
            logger.info("     Skipping...")
        pass

    def _safe_reboot(self):
        _desc = "Safe Reboot"
        logger.info("Running: " + _desc)
        if self.no_action:
            logger.info("     Skipping...")
            return True
        _cmds = {
            "Linux": "/usr/sbin/shutdown -r now",
            "Darwin": "/usr/sbin/shutdown -r now",
            "Windows": "shutdown /r /t 0",
        }
        self.run_subprocess(cmds=_cmds, desc=_desc)

    def _safe_shutdown(self):
        _desc = "Safe Shutdown"
        logger.info("Running: " + _desc)
        if self.no_action:
            logger.info("     Skipping...")
            return True
        _cmds = {
            "Linux": "/usr/sbin/shutdown now",
            "Darwin": "/usr/sbin/shutdown now",
            "Windows": "shutdown /t 0",
        }
        self.run_subprocess(cmds=_cmds, desc=_desc)

    def _screen_lock(self):
        _desc = "Screen Lock"
        logger.info("Running: " + _desc)
        if self.no_action:
            logger.info("     Skipping...")
            return True
        if self.platform == "Linux":
            user_sessions = self.run_subprocess(
                cmds="/usr/bin/loginctl --no-legend", desc=_desc
            )
            for _session in user_sessions.splitlines():
                _s = _session.split()
                _c = "/usr/bin/loginctl lock-session " + _s[0]
                _desc = "Locking Screen for session: " + _session
                self.run_subprocess(cmds=_c, desc=_desc)
        if self.platform == "Darwin":
            _session = ctypes.CDLL(
                "/System/Library/PrivateFrameworks/login.framework/Versions/Current/login"
            )
            _session.SACLockScreenImmediate()
        if self.platform == "Windows":
            ctypes.windll.user32.LockWorkStation()

    def _secure_delete(self):
        """ Securely delete files and folders """
        import string
        import random
        from pathlib import Path

        _paths = self.queued_actions["secure_delete"]
        _passes = self.app_config["secure_delete_passes"]
        logger.info("Securely deleting files with %s overwrite passes.", _passes)

        def _rnd_str() -> str:
            """ Create a randomish string of _str_length length"""
            _str_length = random.randrange(1, 48)
            _chars = string.ascii_letters + string.digits
            _str = "".join((random.choice(_chars) for _ in range(_str_length)))
            return _str

        def _directory_delete(path):
            """ Rename then delete a directory """
            _path = Path(path)
            if self.no_action:
                logger.debug("     Skipping secure delete of %s", str(_path))
                return True

            _new_path = _path.rename(_rnd_str())
            try:
                _new_path.rmdir()
                logger.debug("Deleted directory %s", _path)
            # We don't follow symlinks when we delete files so
            # it's possible we can't delete a dir. We ignore that error.
            except OSError:
                pass

        def _file_delete(file, passes):
            """ Securely delete a file """
            # With thanks to phealy3330 @ https://stackoverflow.com/questions/17455300/python-securely-remove-file
            _file = file
            _passes = passes
            if self.no_action:
                logger.debug("     Skipping secure delete of %s", _path)
                return True

            with open(_file, "ba+", buffering=0) as f:
                file_length = f.tell()
            f.close()
            with open(_file, "br+", buffering=0) as f:
                # Overwrite the file x times.
                for x in range(passes):
                    f.seek(0, 0)
                    f.write(os.urandom(file_length))
                    logger.debug(
                        "Secure delete pass %s of %s complete for %s", x, _passes, _file
                    )
                f.seek(0)
                # Do a final overwrite of all zeros.
                for _ in range(file_length):
                    f.write(b"\x00")
            # Rename the file to a randomish string
            _new_path = _file.rename(_rnd_str())
            # Delete the file
            _new_path.unlink()
            logger.debug("Secure delete complete for %s", _file)

        for _path in _paths:
            _path = Path(_path)
            _path = _path.expanduser()
            if _path.exists():
                # If the path in the config file is a file we delete it directly.
                if _path.is_file():
                    _file_delete(file=_path, passes=_passes)
                # If the path in the config file is a dir we iterate from the bottom up.
                elif _path.is_dir():
                    for _root, _dirs, _files in os.walk(_path, topdown=False):
                        _root = Path(_root)
                        for _file in _files:
                            _file = Path(_file)
                            _file_path = _root.joinpath(_file)
                            _file_delete(file=_file_path, passes=_passes)
                        for _dir in _dirs:
                            _dir = Path(_dir)
                            _dir_path = _root.joinpath(_dir)
                            _directory_delete(path=_dir)
                    # If the path in the config file is a dir and doesn't end in a "/" delete it.
                    if _path[-1] != "/":
                        _directory_delete(_path)
            else:
                logger.warning('Path "%s" doesn\'t exist.', str(_path))
