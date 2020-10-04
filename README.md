# USBEventManager
Inspired and by default implements the same behaviour as [usbkill](https://github.com/hephaest0s/usbkill).

**If you are using USBEventManager to protect your system the data you are protecting must be encrypted and require a 
password after a reboot to access. All modern OSes support encrypting root and data volumes.**

USBEventManager improves the security and functionality of any computer system by giving users the  ability to take an arbitrary set of actions when a USB device is added or removed from the system. By default USBEventManager disables the new USB device, locks the screen, and performs an immediate forced shutdown** of the system within .25 seconds of a change that hasn't been explicitly allowed.

**Default behaviour may be different on some platforms, see Platforms below.

While the default functionality is to protect systems USBEventManager is also platform independent tool 
for automating arbitrary actions when a USB device is added or removed from a system. This is especially helpful for 
systems without programmatic remote access. For example -
1. If a whitelisted USB device is plugged in and it contains a `hosts` file overwrite the hosts file at `/etc/hosts`.
2. If any USB device is plugged in automatically copy `/var/logs/*` to the USB stick then unmount it.
3. If a USB device is plugged in and it has a `*.cab` file use the file to apply a firmware update.

There are basic examples of some custom_commands in the `examples` folder.

## Install -
##### Ubuntu -
```
sudo apt install -y  libusb-1.0-0-dev 
git clone https://github.com/Gestas/USBEventManager.git && cd USBEventManager
./install.sh
```
##### MacOS -
```
git clone https://github.com/gestas/USBEventManager && cd USBEventManager
./install.sh
```
##### Windows 10 -
```
TODO
```
USBEventManager needs to run with root/Administrator permissions. It's bad practice to setup a virtualenv or do a pip install as root/Administrator. In the alternative we install as a non-privileged user then start USBEventManager with a Bash or Powershell wrapper that activates the virtualenv then USBEventManager.

## Usage -
Must be run with root/Administrator permissions. Start by whitelisting any USB devices that you regularly use. 
You can do this by starting USBEventManager in learning mode, `$ sudo USBEventManager --learn`. You can remove USB devices
from the whitelist by running `$ sudo USBEventManager --remove xxxx:xxxx`.

Alternatively you can directly edit the configuration file at `/etc/usbeventmanager.yml`. Either or both the
manufacturer and product IDs can be a wildcard, e.g `*:*`, `*:zzzz`, `yyyy:*`.

Devices can be defined in three different lists -
* `whitelist` is the default list, devices listed here do not trigger any actions. If an ID is listed more than once (x) up to x devices will be tolerated.
* `removal_blacklist` devices on this list won't trigger actions when added to a system, they will if removed. 
* `device_specific` this list allows users to trigger event specific actions for specified devices.

When change is detected the lists are checked in this order -
1. `device_specific`
1. `removal_blacklist`
1. `whitelist`

```
$ sudo USBEventManager --help
Options:
  --loglevel [ERROR|WARNING|INFO|DEBUG]
                                  Sets the logging level. Defaults to WARNING.
  --no-actions                    Don't actually perform any actions. Used for
                                  testing and development.

  --help                          Show this message and exit.

Commands:
  automatic-start  Configure USBEventManager to start automatically.
  learn            Learn new USB devices.
  list-actions     List enabled actions.
  list-devices     List devices in the config file.
  monitor          Monitor for added and removed USB devices
  remove           Remove one or more USB devices from the configuration. -> 'remove "xxxx:xxxx" "yyyy:yyyy"'
```

#### Starting USBEventManager when the system starts -
USBEventManager can create the required service for you, run -

```$ sudo USBEventManager --automatic-start```

## Platforms -
* FreeNas

## Included actions
* Device disable (**Enabled by default**)
  * Immediately disable a newly attached device. Designed to prevent a virtual keyboard or mouse jiggler from
  interfering with subsequent actions.
* Screen Lock (**Enabled by default**)
* Clear Memory
  * TODO 
* Clear Swap
  * Only supported on Linux systems with the `swapon` and `swapoff` commands.
  * TODO: Find a solution for MacOS and Windows.
* Custom Command Handler
  * Runs any command specified by the user.
* Port disabling
  * TODO: Proactively disable any unused USB ports when USBEventManager starts.
* Delete any files and folders as specified by the user.
* Securely delete any files and folders as specified by the user.
  * For ease of cross-platform support secure delete is implemented directly, see actions.py, `_secure_delete`. 
  Depending on the details of your system it may be preferable to implement this differently using the
  Custom Command Handler.
* Filesystem sync
  * Syncs the root volume.
  * On Windows this requires [Sync](https://docs.microsoft.com/en-us/sysinternals/downloads/sync).
* Melt
  * TODO: Destroy any evidence of this tool
* Safe reboot
* Forced reboot
* Safe shutdown
* Forced shutdown (**Enabled by default**)

## Custom commands -
Take note of the `custom_command_timeout` and `ignore_custom_command_failure` options in the config file. 
Make sure commands are executable and specified with a full path. When a custom command is run these environment variables are exported -
```
USBEVENTMANAGER_PLATFORM="Linux | Darwin | Windows | FreeNas | Synology"
USBEVENTMANAGER_EVENT_TYPE="ADDED | REMOVED"
USBEVENTMANAGER_DEVICE_ID="xxxx:xxxx"
```
## HOWTOs
* You can set event (ADDED | REMOVED) specific default actions by disabling all the actions in the `default_actions` 
list then adding a '\*:\*' device to the `device_specific` list. Specify your defaults in the event lists. As devices are
evaluated from the top of each list down you can still set actions for specific devices above the '\*:\*' device.

## Thanks to
* [usbkill](https://github.com/hephaest0s/usbkill)
* phealy3330 @ https://stackoverflow.com/questions/17455300/python-securely-remove-file


### Removing USBEventManager
##### Ubuntu -
```
# In the USBEventManager folder - 
source /venv/bin/activate
pip uninstall -y USBEventManager
rm -rf * .git
cd ..
rmdir USBEventManager
sudo rm /usr/local/bin/USBEventManager

# To remove the configuration file - 
sudo rm /etc/usbeventmanager.yml 

# If automatic start is setup - 
sudo systemctl stop USBEventManager.service
sudo systemctl disable USBEventManager.service
sudo rm /etc/systemd/system/USBEventManager.service
sudo systemctl daemon-reload
sudo systemctl reset-failed
```
##### MacOS -
```
TODO
```
##### Windows 10 -
```
TODO
```