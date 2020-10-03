import logging
import usb.core
import usb.util
from helpers import Helpers

logger = logging.getLogger(__name__)

helpers = Helpers()


class USBTools(object):
    def _enumerate_devices(self) -> dict:
        """ Return human formatted USB devices ids in a dict including quantity """
        _devices_l: list = []
        _devices: dict = {}
        _ds = usb.core.find(find_all=True)
        for d in _ds:
            _device = self.pyusb_to_human(d)
            _devices_l.append(_device)
            _devices = helpers.aggregate_list_dupes(_devices_l)
        return _devices

    def friendly_device_desc(self, device):
        """ Returns a friendly description of the _d """
        _device = device
        _vid, _pid = self.human_to_pyusb(_device)
        _dev = usb.core.find(idVendor=_vid, idProduct=_pid)
        _manufacturer = usb.util.get_string(_dev, _dev.iManufacturer)
        _product = usb.util.get_string(_dev, _dev.iProduct)
        if not _manufacturer:
            _manufacturer = "<none>"
        if not _product:
            _product = "<none>"
        _name = _manufacturer + " : " + _product
        return _name

    def unbind(self, device):
        _device = device
        _vid, _pid = self.human_to_pyusb(_device)
        dev = usb.core.find(idVendor=_vid, idProduct=_pid)
        dev.detach_kernel_driver(0)
        logger.debug("Unbound _d: idVendor: %s, idProduct: %s", _vid, _pid)
        return True

    @staticmethod
    def human_to_pyusb(device: str) -> tuple:
        """ Convert a human USB _d id to a pyusb id """
        vid, pid = device.split(":")
        vid = int(vid, 16)
        pid = int(pid, 16)
        return vid, pid

    @staticmethod
    def pyusb_to_human(device) -> str:
        """ Convert pyusb _d id to human friendly format"""
        """ Convert pyusb _d id to human friendly format"""
        _vid = f"{device.idVendor:04x}"
        _pid = f"{device.idProduct:04x}"
        device_id: str = _vid + ":" + _pid
        return device_id

    @property
    def devices(self):
        return self._enumerate_devices()
