# USBEventManager
Inspired by [usbkill](https://github.com/hephaest0s/usbkill). Many thanks to [Hephaestos](https://github.com/hephaest0s) 
for the original project.

#### Functionality changes v usbkill -
1. Adds support for Windows 10+.
1. Option to whitelist any active USB devices during installation.
1. Implements an event model where the user may specify any set of actions to be run when a USB device is added or 
   removed.
   * Supports running any application(s) as an action.
1. Allows for specific devices to be removed without triggering an event.
   * Valuable where built-in devices can appear/disappear.
     * Impetus for this project. On a Lenovo ThinkPad Carbon X1 Gen 6 a USB hub is started/stopped when a device is 
     plugged into a USB C port. This hub is also present for some time during system startup. 
     This makes [usbkill](https://github.com/hephaest0s/usbkill) behave inconsistently.
1. Defaults to immediately disabling any non-whitelisted USB devices to make running pre-shutdown tasks safer.
1. Defaults to locking the screen to make running pre-shutdown tasks safer.
1. Adds a "--learn" option to make it easy to add devices to the list of allowed devices.
1. Adds a "--remove" option to make it easier to remove devices from the list of allowed devices.
1. Supports wildcards in USB device IDs.
1. Option to install a service to make it easier to start automatically.
1. Increased logging verbosity by default, supports DEBUG logging.
1. Implements some non-merged pull requests against usbkill -
    * [FreeNAS support](https://github.com/hephaest0s/usbkill/pull/89)
    * TODO: [Support for sysrq](https://github.com/hephaest0s/usbkill/pull/4) available as an action. Not a default.

### CONTRIBUTING
Pull requests encouraged! If you are considering contributing to USBEventManager please open an issue that describes the
contribution and your implementation pattern. Once we're agreed on the best approach you can start developing! Make sure
to read the development notes.

##### Adding a built-in action -
USBEventManager supports a set of built-in actions. I encourage users that find themselves writing their own action to
contribute it back to the project, it's possible someone else will find it useful!

##### Adding a supported platform -
There are two approaches to adding a platform; with or without platform detection. Whenever resonable we prefer to not
have `if platform...` branches, we should make the codebase platform independent. Where that isn't possible add the
detection to the `_get_platform` function in the helpers class.

##### Generally -
* Use type hints.
* Comment aggressively.
* Prevent breaking changes.
* Use the [Black](https://pypi.org/project/black/) code formatter.
* More descriptive variable names are preferred e.g. `_cnt` v `_c` or `_dev` v `_d`.

#### TODOs:
1. [GitHub](https://github.com/Gestas/USBEventManager/issues?q=is%3Aissue+is%3Aopen+label%3ATODO)

##### Misc:
```
find ./USBEventManager -maxdepth 1 -name "*.py" -exec black {} \;
```