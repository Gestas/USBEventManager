import time
import logging


from actions import Actions
from helpers import Helpers
from usb_helpers import USBTools

usb = USBTools()
helpers = Helpers()

logger = logging.getLogger(__name__)


class USBEventManager(object):
    def __init__(self, no_actions):

        self._event = False
        self._no_actions = no_actions
        self._app_config = helpers.config
        self._config_path = helpers.config_path

        # Configuration details
        self._default_actions: dict = self._app_config["default_actions"]
        self._check_interval: int = int(self._app_config["check_interval"])
        self._allow_unknown_removal: bool = self._app_config["allow_unknown_removal"]
        self._devices_with_specific_actions: dict = self._app_config["device_specific"]
        self._allow_unknown_devices_at_start: bool = self._app_config[
            "allow_unknown_devices_at_start"
        ]

        # Load the white/blacklists from the configuration file.
        self._get_lists()

        self._actions = None
        self._startup_devices: dict = {}
        self._session_allowed_devices: dict = {}
        self._current_attached_devices: dict = {}
        self._unknown_devices_at_startup: dict = {}
        self._removal_blacklisted_devices: list = []
        self._session_allowed_attached_devices: dict = {}
        self._session_removal_blacklisted_devices: list = []

        logger.debug("USBEventManager configuration: %s", self._app_config)

        if self._no_actions:
            logger.info("No actions is True")

    def _get_lists(self):
        """ Load the white/black lists from the configuration file """
        self._default_whitelist: dict = helpers.aggregate_list_dupes(
            self._app_config["whitelist"]
        )
        self._removal_blacklist: dict = helpers.aggregate_list_dupes(
            self._app_config["removal_blacklist"]
        )
        self._platform_specific_default_actions: dict = self._app_config[
            "platform_specific_default_actions"
        ]

    def learn(self):
        """ Learn new USB device IDs """
        logger.debug("Learning...")
        _update = False
        _first_loop = True
        try:
            _startup_attached_devices: dict = usb.devices
            while True:
                if _first_loop:
                    # Add all devices attached to the system to the default whitelist.
                    # If there is more than one device attached (x) add the device x times.
                    print("Adding any new, attached devices to the default whitelist.")
                    for _device, _cnt in _startup_attached_devices.items():
                        if (
                            _device not in self._devices_with_specific_actions.keys()
                            and _device not in self._removal_blacklist.keys()
                        ):
                            if _device not in self._default_whitelist.keys():
                                print(f"     Added {_device} : {_cnt}")
                                if self._no_actions:
                                    print(f"     Skipping...")
                                else:
                                    self._default_whitelist[_device] = _cnt
                                _update = True
                            else:
                                if _cnt > self._default_whitelist[_device]:
                                    self._default_whitelist[_device] = _cnt
                                    print(f"     Updated {_device} : {_cnt}")
                                    _update = True
                    print(" ")
                    print("Attach a USB device to add it to the default whitelist.")
                    print("Ctrl-C to quit...")
                _attached_devices: dict = usb.devices
                for device in _attached_devices.keys():
                    if device not in self._default_whitelist:
                        self._default_whitelist[device] = 1
                        print(f"     Added {device} : 1")
                        print(" ")
                        print("Insert a device to add it to the default whitelist.")
                        print("Ctrl-C to quit...")
                        _update = True
                _first_loop = False
                time.sleep(self._check_interval)
        except KeyboardInterrupt:
            print("")
            if _update:
                _whitelist: dict = {
                    "whitelist": helpers.disaggregate_dict_dupes(
                        self._default_whitelist
                    )
                }
                helpers.update_config(data=_whitelist)
                print("Updated: ")
                print(
                    "     "
                    + helpers.pretty_default_whitelist(
                        whitelist=self._default_whitelist
                    )
                )
            else:
                print("No changes.")
        helpers.exiter(0)

    def list_actions(self):
        """ Print a list of enabled actions. """
        print("Default actions: ")
        if not self._default_actions.keys():
            print("     <none>")
        else:
            for action, enabled in self._default_actions.items():
                if enabled:
                    if type(enabled) is bool:
                        print(f"          {action}")
                    else:
                        print(f"          {action}")
                        print(f"               {enabled}")

        print("Platform specific default actions: ")
        if not self._platform_specific_default_actions.keys():
            print("     <none>")
        else:
            for platform, actions in self._platform_specific_default_actions.items():
                print(f"     {platform}")
                if not actions.keys:
                    print("          <none>")
                else:
                    for action, enabled in actions.items():
                        if enabled:
                            if type(enabled) is bool:
                                print(f"          {action}")
                            else:
                                print(f"          {action}")
                                print(f"               {enabled}")
        print(
            helpers.pretty_devices_with_specific_actions(
                self._devices_with_specific_actions
            )
        )
        return True

    def list_devices(self):
        """ Print a list of all devices in the config file. """
        print(helpers.pretty_default_whitelist(self._default_whitelist))
        print(helpers.pretty_removal_blacklist(self._removal_blacklist))
        print(
            helpers.pretty_devices_with_specific_actions(
                self._devices_with_specific_actions
            )
        )
        return True

    def remove_devices(self, device_ids: tuple):
        """ Remove one of more devices from the configuration """
        _device_ids = device_ids
        for _dev in _device_ids:
            logger.info('Removing device "%s" from configuration.', _dev)
            _dw_update = False
            _bl_update = False
            _ds_update = False
            if _dev in self._default_whitelist:
                if self._no_actions:
                    print(f"     Skipping removal from the default whitelist...")
                else:
                    del self._default_whitelist[_dev]
                    logger.info("     Removed from the default whitelist.")
                _dw_update = True
            if _dev in self._removal_blacklist:
                if self._no_actions:
                    print(f"     Skipping removal from the removal blacklist...")
                else:
                    del self._removal_blacklist[_dev]
                    logger.info("     Removed from removal blacklist.")
                _bl_update = True
            if _dev in self._devices_with_specific_actions.keys():
                if self._no_actions:
                    print(f"     Skipping removal from device specific options.")
                else:
                    self._devices_with_specific_actions.pop(_dev, None)
                    logger.info("     Removed from device specific options.")
                _ds_update = True
            if _dw_update:
                _dw: dict = {
                    "whitelist": helpers.disaggregate_dict_dupes(
                        self._default_whitelist
                    )
                }
                helpers.update_config(data=_dw)
                print("New default whitelist: ")
                print(
                    "     " + helpers.pretty_default_whitelist(self._default_whitelist)
                )
            if _bl_update:
                _bl: dict = {"removal_blacklist": self._removal_blacklist}
                helpers.update_config(data=_bl)
                print("New removal blacklist: ")
                print(
                    "     " + helpers.pretty_removal_blacklist(self._removal_blacklist)
                )
            if _ds_update:
                _ds: dict = {"device_specific": self._devices_with_specific_actions}
                helpers.update_config(data=_ds)
                print("New specific actions: ")
                print(
                    "     "
                    + helpers.pretty_devices_with_specific_actions(
                        self._devices_with_specific_actions
                    )
                )
            if not _dw_update and not _bl_update and not _ds_update:
                logger.info("     Device %s not found in config.", _dev)
        helpers.exiter(0)

    def _setup_monitor_mode(self):

        if not helpers.is_root:
            logger.error("Monitor mode requires root/Administrator permissions.")
            helpers.exiter(1)

        self._actions = Actions(app_config=self._app_config)

        # Here we build session specific lists of devices #
        # _startup_devices == USB devices attached when USBEventManager is started
        # _session_allowed_attached_devices == devices that can be attached without triggering actions
        #    This dict may be mutated during the session.
        # _devices_with_specific_actions == specific devices that trigger specific actions on add or removal
        # _unknown_devices_at_startup == devices that are attached at start and that are not in the config file
        # _session_removal_blacklisted_devices == devices that are already attached or can be attached without
        #     triggering actions but will on removal.

        self._startup_devices: dict = usb.devices
        logger.debug("USB devices attached at startup: %s", self._startup_devices)

        # Build the _session_allowed_attached_devices whitelist
        # Add the default whitelist
        self._session_allowed_attached_devices = self._default_whitelist
        # Add the removal blacklist.
        for device in self._removal_blacklist:
            if device not in self._session_allowed_attached_devices:
                self._session_allowed_attached_devices[device] = 1
        # Add devices with specific actions
        for device in self._devices_with_specific_actions:
            if device not in self._session_allowed_attached_devices:
                self._session_allowed_attached_devices[device] = 1

        # Devices attached at startup that are not on any whitelists or where the count
        # of attached devices with the same ID is greater that allowed via the whitelist.
        for device, attached_cnt in self._startup_devices.items():
            if not helpers.usb_device_id_match(
                config_devices=self._session_allowed_attached_devices, device=device
            ):
                self._unknown_devices_at_startup[device] = attached_cnt
            if helpers.usb_device_id_match(
                config_devices=self._session_allowed_attached_devices, device=device
            ):
                if attached_cnt > self._session_allowed_attached_devices[device]:
                    self._unknown_devices_at_startup[device] = (
                        attached_cnt - self._session_allowed_attached_devices[device]
                    )
        logger.debug(
            "Devices attached at startup that don't match a whitelist: %s",
            self._unknown_devices_at_startup,
        )

        # Add all devices attached at startup to the session allowed devices list
        # unless configured ("allow_unknown_removal" in the config) otherwise.
        if self._allow_unknown_devices_at_start:
            logger.debug(
                "The allow_unknown_devices_at_start option is true. "
                "Whitelisting all devices attached at startup."
            )
            for _device, _attached_cnt in self._startup_devices.items():
                _allowed_cnt = self._session_allowed_attached_devices.get(
                    _device, False
                )
                if _allowed_cnt:
                    if _attached_cnt > _allowed_cnt:
                        self._session_allowed_attached_devices[_device] = _attached_cnt
                else:
                    self._session_allowed_attached_devices[_device] = _attached_cnt
        else:
            logger.debug(
                "The allow_unknown_devices_at_start option is false."
                "Not automatically whitelisting devices attached at startup."
            )
        logger.debug(
            "All devices whitelisted for attachment this session: %s",
            self._session_allowed_attached_devices,
        )

        # Build the complete removal blacklist
        # Add the explicit removal blacklist
        for k in self._removal_blacklist.keys():
            self._session_removal_blacklisted_devices.append(k)
        # If configured ("allow_unknown_removal" in the config) add unknown devices attached at startup
        if not self._allow_unknown_removal:
            for k in self._unknown_devices_at_startup:
                self._session_removal_blacklisted_devices.append(k)
        logger.debug(
            "Devices blacklisted for detach: %s",
            self._session_removal_blacklisted_devices,
        )

    def monitor(self):
        """ Monitor for changes in attached devices  """
        logger.info("Monitoring...")

        self._setup_monitor_mode()
        _old_attached_devices: dict = {}
        try:
            print("Ctrl-C to quit...")
            while True:
                _delta: dict = {}
                self._current_attached_devices: dict = usb.devices
                logger.debug(
                    "%s devices attached: %s",
                    sum(self._current_attached_devices.values()),
                    self._current_attached_devices,
                )

                _old_device_cnt = sum(_old_attached_devices.values())
                _current_device_cnt = sum(self._current_attached_devices.values())
                if _current_device_cnt > _old_device_cnt:
                    self._event = "ADDED"
                if _current_device_cnt < _old_device_cnt:
                    self._event = "REMOVED"

                if self._event:
                    if self._event == "ADDED":
                        for (
                            _device,
                            _attached_device_cnt,
                        ) in self._current_attached_devices.items():
                            _delta = {}
                            for x in range(0, _attached_device_cnt):
                                if _device not in _old_attached_devices:
                                    _desc = usb.friendly_device_desc(_device)
                                    logger.info(
                                        "New device added: %s, %s", _device, _desc
                                    )
                                    _delta[_device] = _attached_device_cnt
                                    self._check_lists(
                                        devices=_delta, event_type=self._event
                                    )
                                if _device in _old_attached_devices:
                                    if (
                                        _attached_device_cnt
                                        < _old_attached_devices[_device]
                                    ):
                                        _desc = usb.friendly_device_desc(_device)
                                        logger.info(
                                            "Additional instance of %s, %s added.",
                                            _device,
                                            _desc,
                                        )
                                        _delta[_device] = _attached_device_cnt
                                        self._check_lists(
                                            devices=_delta, event_type=self._event
                                        )
                    if self._event == "REMOVED":
                        for _device in _old_attached_devices.keys():
                            if _device not in self._current_attached_devices:
                                logger.info("Device %s removed", _device)
                                _devices = {_device: 1}
                                self._check_lists(
                                    devices=_devices, event_type=self._event
                                )
                time.sleep(self._check_interval)
                self._event = False
                _old_attached_devices = dict(self._current_attached_devices)
        except KeyboardInterrupt:
            helpers.exiter(0)

    def _check_lists(self, devices: dict, event_type: bool):
        """ Check added or removed devices against the device lists and trigger actions if required. """
        logger.debug("Checking lists for: %s", devices)
        _devices = devices
        _event = event_type
        if _event == "ADDED":
            for _dev, _connected_cnt in devices.items():
                if _dev not in self._session_allowed_attached_devices:
                    logger.info(
                        "Device %s not whitelisted. Triggering %s actions.",
                        _dev,
                        _event,
                    )
                    self._actions.trigger_actions(_dev, _event)
                elif _dev in self._session_allowed_attached_devices:
                    _allowed_ct = self._session_allowed_attached_devices.get(
                        _dev, False
                    )
                    if _allowed_ct:
                        if _allowed_ct < _connected_cnt:
                            logger.info(
                                "%s instances of device %s allowed, %s found. "
                                "Triggering actions.",
                                _allowed_ct,
                                _dev,
                                _connected_cnt,
                            )
                            self._actions.trigger_actions(_dev, _event)
                        else:
                            logger.info('Device "%s" whitelisted for attachment.', _dev)
                    else:
                        logger.info(
                            'Device "%s" whitelisted for attachment. No action required.',
                            _dev,
                        )
        if _event == "REMOVED":
            for _dev in devices.keys():
                if _dev in self._removal_blacklist:
                    logger.info(
                        "Device %s explicitly blacklisted for removal. Triggering %s actions.",
                        _dev,
                        _event,
                    )
                    self._actions.trigger_actions(_dev, _event)
                # If the removed device was attached at startup and not otherwise whitelisted
                # remove it from the list of devices that can be attached. This prevents the device
                # from being re-attached.
                if _dev in self._unknown_devices_at_startup.keys():
                    if self._allow_unknown_removal:
                        self._session_allowed_attached_devices.pop(_dev, None)
                        logger.info(
                            "Non-whitelisted device %s was attached at startup. Removal of these "
                            "devices is allowed.",
                            _dev,
                        )
                    else:
                        logger.info(
                            "Non-whitelisted device %s was attached at startup. Removal of these "
                            "devices is not allowed. Triggering %s actions.",
                            _dev,
                            _event,
                        )
                        self._actions.trigger_actions(_dev, _event)
                elif _dev not in self._session_allowed_devices:
                    logger.info(
                        "Device %s is not whitelisted for removal. Triggering %s actions.",
                        _dev,
                        _event,
                    )
                    self._actions.trigger_actions(_dev, _event)

    @staticmethod
    def create_service():
        """ Create a service to start USBEventManager automatically """
        if helpers.platform == "Linux":
            from services import SystemD
            service = SystemD()
