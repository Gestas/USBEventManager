#!/bin/bash
# Activates the virtualenv then starts USBEventManager. Allows us to run
# a virtualenv not installed by the root user with root permissions.
# TODO: USBEventManager supports tab-completion on the CLI, this breaks it. Fix that.
# https://iridakos.com/programming/2018/03/01/bash-programmable-completion-tutorial
set -e

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
# Run USBEventManager, passing all the CLI options.
python "$DIR/USBEventManager/usbeventmanager.py" "$@"
