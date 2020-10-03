#!/bin/bash
### Install USBEventManager on *nix and MacOS
set -e
echo "Installing USBEventManager..."

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

start_script="USBEventManager.sh"
final_config_path="/etc/usbeventmanager.yml"
source_start_script="./errata/$start_script"
executable_path="/usr/local/bin/USBEventManager"
source_config_file="$project_dir/errata/usbeventmanager.yml"

# We don't want to install the virtualenv or USBEventManager as root.
if [[ $EUID -eq 0 ]]; then
  echo "Don't start the USBEventManager installer as root."
  exit 1
fi

# Look for Python 3.8 or .9
echo "Checking for Python 3.8. or 3.9..."
python_path="$(command -v python3.8)"
if [[ -z "$python_path" ]]; then
  python_path="$(command -v python3.9)"
  if not [[ -z "$python_path" ]]; then
    echo "Can't find Python 3.8 or 3.9 in the path."
  fi
fi

# Make sure virtualenv is installed
virtualenv="$(command -v virtualenv)"
if [[ -z "$virtualenv" ]]; then
  echo "virtualenv is required."
  echo "Installation documentation - https://pypi.org/project/virtualenv/1.7.1.2/"
  exit 1
fi

if [[ ! -d "./venv" ]]; then
  echo "Creating a new virtualenv using $python_path"
  virtualenv --quiet --python="$python_path" "venv"
else
  current_venv_version="$(./venv/bin/python --version)"
  if [[ "$current_venv_version" == *"3.8"* ]] || [[ "$current_venv_version" == *"3.9"* ]]; then
    echo "Reusing current virtualenv."
  else
    echo "Existing virtualenv doesn't use Python 3.8 or 3.9."
    echo "Current version: $current_venv_version"
    exit 1
  fi
fi

# Activate the virtualenv
# shellcheck source=../venv/bin/activate
source "$project_dir/venv/bin/activate"

# We need the newest version of setuptools to avoid a "AttributeError: install_layout" error
pip install --upgrade setuptools
# Install USBEventManager
pip install "$project_dir"

# Copy the appropriate start script to the project root
cp "$source_start_script" "$project_dir"

echo " "
echo "Need root permissions to finish up..."
# Setup the executable in the path
if [[ ! -h "$executable_path" ]] || [[ ! -f "$executable_path" ]]; then
  echo "Linking $executable_path to $project_dir/$start_script..."
  sudo ln -s "$project_dir/$start_script" "$executable_path"
  echo "Making $executable_path executable..."
  sudo chmod +x "$executable_path"
fi

# Copy the default config file if it's not there.
if [[ ! -h "$final_config_path" ]] || [[ ! -f "$final_config_path" ]]; then
  echo "Copying default configuration file to $final_config_path"
  sudo cp "$source_config_file" "$final_config_path"
fi
echo " "
echo "Setup complete."
echo " "

echo "Do you want to add devices to the default whitelist? Yes/No"
read -r do_learn
do_learn="$(echo "$do_learn" | tr '[:upper:]' '[:lower:]')"
if [[ "$do_learn" == "y"* ]]; then
  sudo "$executable_path" learn
fi

echo " "
echo "Do you want to start USBEventManager automatically? Yes/No"
read -r do_make_service
do_make_service="$(echo "$do_make_service" | tr '[:upper:]' '[:lower:]')"
if [[ "$do_make_service" == "y"* ]]; then
  sudo "$executable_path" automatic-start
fi
exit 0