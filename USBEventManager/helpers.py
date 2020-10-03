import os
import sys
import copy
import ctypes
import logging
import platform
from pathlib import Path

# We use ruamel.yaml so we can update the config file while maintaining
# the comments, https://yaml.readthedocs.io/en/latest/index.html.
# https://github.com/yaml/pyyaml/issues/90
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)


class Helpers(object):
    def __init__(self):

        _config_file: Path = Path("usbeventmanager.yml")
        _config_file_parent = Path("/etc")
        self.app_path: Path = Path("~/.usbeventmanager/")
        self.app_path: Path = self.app_path.expanduser()
        self.config_file_path: Path = _config_file_parent.joinpath(_config_file)
        # Copy the config file to the appropriate path
        if not self.config_file_path.is_file():
            import shutil

            logger.info("Copying %s to %s.", _config_file, self.app_path)
            _config_file_parent.mkdir(exist_ok=True)
            shutil.copy(_config_file, self.config_file_path)
        self.app_config = self._load_yaml_file(path=self.config_file_path)

    @staticmethod
    def exiter(code):
        """ Exit tasks """
        sys.exit(code)

    def update_config(self, data) -> None:
        """ Update the configuration """
        logger.debug("Updating the configuration.")
        _data = data
        logger.debug("Update is: %s", _data)
        _key = next(iter(_data))
        _config = self._load_yaml_file(path=self.config_file_path)

        # We need to do some work to maintain the comments.
        # https://stackoverflow.com/questions/57582926/preserving-following-comments-when-removing-last-dict-key-with-ruamel-yaml
        _comment_index = len(_config[_key])
        _comment_index = _comment_index - 1
        _comment_to_be_saved = copy.deepcopy(_config[_key].ca)
        _comment_to_be_saved = _comment_to_be_saved.items[_comment_index]
        _config[_key].clear()
        for i in _data[_key]:
            _config[_key].append(i)
        _comment_index = len(_config[_key])
        _comment_index = _comment_index - 1
        _config[_key].ca.items[_comment_index] = _comment_to_be_saved
        self._dump_yaml_to_file(path=self.config_file_path, data=_config)

    def _load_yaml_file(self, path: Path):
        """ Load a YAML file """
        yaml = YAML()
        _path: Path = Path(path)
        yaml.typ = "safe"
        yaml.indent(mapping=3, offset=2)

        logger.debug("Opening %s.", str(_path))
        if _path.is_file():
            with open(_path, "r") as f:
                data = yaml.load(f)
            return data
        else:
            logger.error("Couldn't open YAML file: %s", str(_path))
            self.exiter(1)

    @staticmethod
    def _dump_yaml_to_file(path: Path, data: dict) -> None:
        yaml = YAML()
        yaml.indent(mapping=3, offset=2)
        _data = data
        _path: Path = Path(path)
        logger.debug("Dumping %s to disk.", str(_path))
        with open(_path, "w") as f:
            yaml.dump(data, f)

    @staticmethod
    def usb_device_id_match(config_devices: dict, device: str) -> [str, bool]:
        """ Match USB devices to device ID strings in the config file and return the value from the config file. """
        _dev_id = device
        _config_devices = config_devices
        for _cfg_devid in _config_devices.keys():
            # If the device ID in the config file == the actual device id or
            # if the device ID in the config file is `*:*` return the match.
            if _cfg_devid == _dev_id or _cfg_devid == "*:*":
                return _cfg_devid
            # Split the devices IDs from the config file and actual device.
            _cfg_vid, _cfg_pid = _cfg_devid.split(":")
            _dev_vid, _dev_pid = _dev_id.split(":")
            # Match the manufacturer ID
            if _cfg_vid == "*" and _cfg_pid == _dev_pid:
                return _cfg_devid
            # Match the product ID
            if _cfg_pid == "*" and _cfg_vid == _dev_vid:
                return _cfg_devid
        return False

    @staticmethod
    def aggregate_list_dupes(lst: list) -> dict:
        """ Return a dict with frequency count of elements in a given list """
        d = dict()
        try:
            for i in lst:
                if i in d:
                    d[i] += 1
                else:
                    d[i] = 1
        # Catch empty lists
        except TypeError:
            return d
        return d

    @staticmethod
    def disaggregate_dict_dupes(d: dict) -> list:
        """ How do I describe this thingy?? """
        _d: dict = d
        _lst: list = []
        for _dev, _cnt in _d.items():
            for _ in range(_cnt):
                _lst.append(_dev)
        return _lst

    @staticmethod
    def _check_root() -> bool:
        """ Checks for root/Administrator permissions. """
    # Thanks to https://raccoon.ninja/en/dev/using-python-to-check-if-the-application-is-running-as-an-administrator/
        try:
            if os.getuid() == 0:
                return True
        except AttributeError:
            if ctypes.windll.shell32.IsUserAnAdmin() != 0:
                return True
        return False

    @staticmethod
    def pretty_default_whitelist(whitelist: dict) -> str:
        """ Return a pretty printed list of devices on the default whitelist """
        _whitelist: dict = whitelist
        _str = "Default whitelist: \n"
        if not _whitelist.keys():
            _str = _str + "     <none>\n"
        else:
            for device, cnt in _whitelist.items():
                _str = _str + "     " + str(device) + " : " + str(cnt) + "\n"
        return _str

    @staticmethod
    def pretty_removal_blacklist(blacklist: dict) -> str:
        """ Return a pretty printed list of devices on the removal blacklist """
        _removal_blacklist: dict = blacklist
        _str = "Removal blacklist: \n"
        if not _removal_blacklist.keys():
            _str = _str + "     <none>\n"
        else:
            for device in _removal_blacklist.keys():
                _str = _str + "     " + device + "\n"
        return _str

    @staticmethod
    def pretty_devices_with_specific_actions(whitelist: dict) -> str:
        """Return a pretty printed list of devices with specific actions and
        their details.
        """
        _devices_with_specific_actions: dict = whitelist
        _str = "Devices with device specific actions: \n"
        if not _devices_with_specific_actions.keys():
            _str = _str + "     <none>\n"
        else:
            for device, event_type in _devices_with_specific_actions.items():
                _str = _str + "     " + device + "\n"
                if not event_type.keys():
                    _str = _str + "          Events: <none>\n"
                else:
                    for event, action in event_type.items():
                        _str = _str + "          Event: " + event + "\n"
                        for a, state in action.items():
                            if state:
                                _str = _str + "            " + str(a) + "\n"
                                if type(state) is not bool:
                                    _str = (
                                        _str + "                 " + str(state) + "\n"
                                    )
                            else:
                                _str = _str + "            <none>\n"
        return _str

    def _get_platform(self) -> str:
        """ Returns the OS we're running on """
        p = platform.uname()
        if not p[0]:
            logger.error("Unable to determine platform.")
            self.exiter(1)
        elif "freenas" in platform.uname()[3]:
            return "FreeNAS"
        else:
            return p[0]

    @property
    def platform(self) -> str:
        return self._get_platform()

    @property
    def config(self):
        return self.app_config

    @property
    def config_path(self) -> Path:
        return self.config_file_path

    @property
    def is_root(self) -> bool:
        return self._check_root()
