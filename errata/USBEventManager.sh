#!/bin/bash
### Activates the virtualenv then starts USBEventManager. Allows us to run as sudo.
set -e

# Check for root
if [[ $EUID -ne 0 ]]; then
  echo "USBEventManager must be run as root"
  exit 1
fi

# Get the directory this file is in. Thanks to
# https://stackoverflow.com/questions/59895/how-to-get-the-source-directory-of-a-bash-script-from-within-the-script-itself
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"


# Activate the virtualenv
# shellcheck source=../venv/bin/activate
source "$DIR/venv/bin/activate"
# Run USBEventManager
python "$DIR/USBEventManager/usbeventmanager.py" "$@"
