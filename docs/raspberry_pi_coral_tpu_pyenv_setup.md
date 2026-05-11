# Raspberry Pi 5 + Google Coral USB TPU Setup with Python 3.9, pyenv, and Virtual Environment

This guide documents a working setup for using a Google Coral USB Accelerator on a Raspberry Pi with Python 3.9. It is written for users who need a clean Python environment for Coral inference, such as image classification or computer vision projects.

The main problems this guide avoids are:

* Accidentally using the system Python.
* Installing the wrong `pycoral` package from PyPI/piwheels.
* Installing NumPy 2.x, which breaks current PyCoral wheels.
* Using the outdated `apt-key` command on newer Raspberry Pi OS / Debian.
* Downloading a broken or outdated test image URL.

\---

## 0\. Assumptions

This guide assumes:

* You are using Raspberry Pi OS based on Debian Bookworm or Trixie.
* You are using a 64-bit Raspberry Pi OS.
* You have a Google Coral USB Accelerator.
* You want Python 3.9.
* Your project folder is:

```bash
\~/salmoncv
```

You can change `\~/salmoncv` to another project path if needed.

\---

## 1\. Update the Raspberry Pi

```bash
sudo apt update
sudo apt upgrade -y
```

Install basic tools:

```bash
sudo apt install -y curl wget git build-essential gpg
```

\---

## 2\. Install build dependencies for pyenv

Python must be compiled from source when installed with `pyenv`, so these packages are required:

```bash
sudo apt install -y \\
  make build-essential libssl-dev zlib1g-dev \\
  libbz2-dev libreadline-dev libsqlite3-dev \\
  wget curl llvm libncursesw5-dev xz-utils tk-dev \\
  libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \\
  git
```

\---

## 3\. Install pyenv

Install `pyenv`:

```bash
curl https://pyenv.run | bash
```

Add `pyenv` to your shell startup file:

```bash
cat << 'EOF' >> \~/.bashrc

# Pyenv setup
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

EOF
```

Reload your shell:

```bash
source \~/.bashrc
```

Confirm that `pyenv` works:

```bash
pyenv --version
```

\---

## 4\. Install Python 3.9 with pyenv

Install Python 3.9.18:

```bash
pyenv install 3.9.18
```

This can take a while on a Raspberry Pi.

Confirm it installed:

```bash
pyenv versions
```

\---

## 5\. Create the project folder and set Python 3.9 locally

Create and enter your project folder:

```bash
mkdir -p \~/salmoncv
cd \~/salmoncv
```

Tell `pyenv` to use Python 3.9.18 inside this project:

```bash
pyenv local 3.9.18
```

Check Python:

```bash
python --version
which python
```

You should see Python 3.9.18.

\---

## 6\. Create a virtual environment

From inside `\~/salmoncv`:

```bash
python -m venv venv
source venv/bin/activate
```

You should now see `(venv)` at the start of your terminal prompt.

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Check that you are using the virtual environment Python:

```bash
which python
which pip
python --version
```

The paths should point to something like:

```text
/home/nalaquq/salmoncv/venv/bin/python
/home/nalaquq/salmoncv/venv/bin/pip
```

\---

## 7\. Install the Coral Edge TPU runtime

Newer Debian/Raspberry Pi OS versions do not use `apt-key`. Use the modern keyring method instead.

Create the keyring folder:

```bash
sudo mkdir -p /usr/share/keyrings
```

Download and install the Google Coral repository key:

```bash
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | \\
sudo gpg --dearmor -o /usr/share/keyrings/coral-edgetpu.gpg
```

Add the Coral package repository:

```bash
echo "deb \[signed-by=/usr/share/keyrings/coral-edgetpu.gpg] https://packages.cloud.google.com/apt coral-edgetpu-stable main" | \\
sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
```

Update apt:

```bash
sudo apt update
```

Install the standard Edge TPU runtime:

```bash
sudo apt install -y libedgetpu1-std
```

The standard runtime is recommended because it runs cooler and uses less power.

Optional maximum-performance runtime:

```bash
sudo apt install -y libedgetpu1-max
```

Do **not** install both `libedgetpu1-std` and `libedgetpu1-max` at the same time.

For field deployments, battery systems, and enclosed boxes, use:

```bash
sudo apt install -y libedgetpu1-std
```

\---

## 8\. Plug in the Coral USB Accelerator

After installing `libedgetpu1-std`, unplug and replug the Coral USB Accelerator.

Check that the Pi sees it:

```bash
lsusb
```

You should see a Google device listed.

\---

## 9\. Install Python packages inside the virtual environment

Make sure the virtual environment is active:

```bash
cd \~/salmoncv
source venv/bin/activate
```

Install core packages:

```bash
python -m pip install Pillow
python -m pip install "numpy==1.26.4"
python -m pip install tflite-runtime
```

Important: keep NumPy below version 2.

If NumPy 2.x is installed, PyCoral can fail with an error like:

```text
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.0.2
AttributeError: \_ARRAY\_API not found
```

Fix that with:

```bash
python -m pip uninstall -y numpy
python -m pip install "numpy==1.26.4"
```

\---

## 10\. Install the correct Google Coral PyCoral package

Do **not** run this by itself:

```bash
pip install pycoral
```

That can install the wrong `pycoral` package from PyPI/piwheels and may fail while trying to build GIS packages such as `fiona` and GDAL.

Instead, install PyCoral from the Google Coral Python package index:

```bash
python -m pip install \\
  --extra-index-url https://google-coral.github.io/py-repo/ \\
  "pycoral\~=2.0"
```

Test the import:

```bash
python -c "from pycoral.adapters import classify; print('pycoral classify import works')"
python -c "from pycoral.utils.edgetpu import make\_interpreter; print('pycoral edgetpu import works')"
```

\---

## 11\. Create a Coral test folder

```bash
mkdir -p \~/salmoncv/coral\_test
cd \~/salmoncv/coral\_test
```

\---

## 12\. Download the example classification script

Use the Google Coral example script:

```bash
wget -O classify\_image.py \\
https://raw.githubusercontent.com/google-coral/pycoral/master/examples/classify\_image.py
```

If that URL changes in the future, you can clone the repo instead:

```bash
cd \~/salmoncv
git clone https://github.com/google-coral/pycoral.git
cp pycoral/examples/classify\_image.py coral\_test/classify\_image.py
cd coral\_test
```

\---

## 13\. Download a test model

Download the Edge TPU compiled MobileNet bird model:

```bash
wget -O mobilenet\_v2\_1.0\_224\_inat\_bird\_quant\_edgetpu.tflite \\
https://github.com/google-coral/test\_data/raw/master/mobilenet\_v2\_1.0\_224\_inat\_bird\_quant\_edgetpu.tflite
```

Download labels:

```bash
wget -O inat\_bird\_labels.txt \\
https://github.com/google-coral/test\_data/raw/master/inat\_bird\_labels.txt
```

\---

## 14\. Download a valid test image

Some older tutorials use an outdated image URL that now returns a 404. Use this instead:

```bash
wget -O parrot.jpg \\
https://github.com/google-coral/test\_data/raw/master/parrot.jpg
```

Check that the file is a real JPEG:

```bash
file parrot.jpg
```

You should see something like:

```text
parrot.jpg: JPEG image data
```

If the image is broken, delete and re-download it:

```bash
rm parrot.jpg
wget -O parrot.jpg \\
https://github.com/google-coral/test\_data/raw/master/parrot.jpg
```

\---

## 15\. Run the Coral image classification test

Make sure the virtual environment is active:

```bash
cd \~/salmoncv/coral\_test
source \~/salmoncv/venv/bin/activate
```

Run inference:

```bash
python3 classify\_image.py \\
  --model mobilenet\_v2\_1.0\_224\_inat\_bird\_quant\_edgetpu.tflite \\
  --labels inat\_bird\_labels.txt \\
  --input parrot.jpg
```

You should see inference timing and a classification result.

The first inference is usually slower because the model is being loaded into the Edge TPU.

\---

## 16\. Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'PIL'`

Install Pillow:

```bash
python -m pip install Pillow
```

Test:

```bash
python -c "from PIL import Image; print('Pillow works')"
```

\---

### Problem: `ModuleNotFoundError: No module named 'pycoral'`

Install the correct PyCoral package:

```bash
python -m pip install \\
  --extra-index-url https://google-coral.github.io/py-repo/ \\
  "pycoral\~=2.0"
```

Test:

```bash
python -c "from pycoral.adapters import classify; print('pycoral works')"
```

\---

### Problem: `pip install pycoral` tries to install `fiona`, `shapely`, `pyproj`, or `pandas`

You are getting the wrong `pycoral` package.

Cancel that install and run:

```bash
python -m pip uninstall -y pycoral
python -m pip install \\
  --extra-index-url https://google-coral.github.io/py-repo/ \\
  "pycoral\~=2.0"
```

\---

### Problem: `A module that was compiled using NumPy 1.x cannot be run in NumPy 2.0.2`

Downgrade NumPy:

```bash
python -m pip uninstall -y numpy
python -m pip install "numpy==1.26.4"
```

Test:

```bash
python -c "import numpy; print(numpy.\_\_version\_\_)"
python -c "from pycoral.utils.edgetpu import make\_interpreter; print('pycoral ok')"
```

\---

### Problem: `PIL.UnidentifiedImageError: cannot identify image file 'parrot.jpg'`

The image is broken, empty, or actually an HTML error page.

Check it:

```bash
file parrot.jpg
ls -lh parrot.jpg
head parrot.jpg
```

Fix it:

```bash
rm parrot.jpg
wget -O parrot.jpg \\
https://github.com/google-coral/test\_data/raw/master/parrot.jpg
```

\---

### Problem: Coral APT repository key error

If you see something like:

```text
Missing key 35BAA0B33E9EB396F59CA838C0BA5CE6DC6315A3
```

Use the modern keyring method:

```bash
sudo mkdir -p /usr/share/keyrings

curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | \\
sudo gpg --dearmor -o /usr/share/keyrings/coral-edgetpu.gpg

echo "deb \[signed-by=/usr/share/keyrings/coral-edgetpu.gpg] https://packages.cloud.google.com/apt coral-edgetpu-stable main" | \\
sudo tee /etc/apt/sources.list.d/coral-edgetpu.list

sudo apt update
sudo apt install -y libedgetpu1-std
```

\---

### Problem: Coral USB Accelerator is not detected

Check USB:

```bash
lsusb
```

Unplug and replug the Coral USB Accelerator.

You can also reboot:

```bash
sudo reboot
```

Then activate the environment again:

```bash
cd \~/salmoncv
source venv/bin/activate
```

\---

## 17\. Quick full install command sequence

This is the condensed version for users who want the whole setup in order.

```bash
sudo apt update
sudo apt upgrade -y

sudo apt install -y \\
  curl wget git build-essential gpg \\
  make libssl-dev zlib1g-dev libbz2-dev libreadline-dev \\
  libsqlite3-dev llvm libncursesw5-dev xz-utils tk-dev \\
  libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

curl https://pyenv.run | bash

cat << 'EOF' >> \~/.bashrc

# Pyenv setup
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

EOF

source \~/.bashrc

pyenv install 3.9.18

mkdir -p \~/salmoncv
cd \~/salmoncv
pyenv local 3.9.18

python -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
python -m pip install Pillow
python -m pip install "numpy==1.26.4"
python -m pip install tflite-runtime

python -m pip install \\
  --extra-index-url https://google-coral.github.io/py-repo/ \\
  "pycoral\~=2.0"

sudo mkdir -p /usr/share/keyrings

curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | \\
sudo gpg --dearmor -o /usr/share/keyrings/coral-edgetpu.gpg

echo "deb \[signed-by=/usr/share/keyrings/coral-edgetpu.gpg] https://packages.cloud.google.com/apt coral-edgetpu-stable main" | \\
sudo tee /etc/apt/sources.list.d/coral-edgetpu.list

sudo apt update
sudo apt install -y libedgetpu1-std

mkdir -p \~/salmoncv/coral\_test
cd \~/salmoncv/coral\_test

wget -O classify\_image.py \\
https://raw.githubusercontent.com/google-coral/pycoral/master/examples/classify\_image.py

wget -O mobilenet\_v2\_1.0\_224\_inat\_bird\_quant\_edgetpu.tflite \\
https://github.com/google-coral/test\_data/raw/master/mobilenet\_v2\_1.0\_224\_inat\_bird\_quant\_edgetpu.tflite

wget -O inat\_bird\_labels.txt \\
https://github.com/google-coral/test\_data/raw/master/inat\_bird\_labels.txt

wget -O parrot.jpg \\
https://github.com/google-coral/test\_data/raw/master/parrot.jpg

python3 classify\_image.py \\
  --model mobilenet\_v2\_1.0\_224\_inat\_bird\_quant\_edgetpu.tflite \\
  --labels inat\_bird\_labels.txt \\
  --input parrot.jpg
```

\---

## 18\. Recommended `requirements.txt`

Create a project requirements file:

```bash
cd \~/salmoncv

cat << 'EOF' > requirements-coral.txt
Pillow
numpy==1.26.4
tflite-runtime
pycoral\~=2.0
EOF
```

Install from it:

```bash
python -m pip install \\
  --extra-index-url https://google-coral.github.io/py-repo/ \\
  -r requirements-coral.txt
```

\---

## 19\. Notes for field deployment

For Raspberry Pi + Coral + battery/solar deployments:

* Use `libedgetpu1-std`, not `libedgetpu1-max`, unless you absolutely need maximum speed.
* Use a powered USB hub if the Coral disconnects under load.
* Keep the Coral outside sealed boxes if possible, or provide ventilation.
* Pin package versions once the setup works.
* Avoid upgrading NumPy to 2.x until PyCoral fully supports it.

\---

## 20\. Final verification commands

Run these any time you want to check the environment:

```bash
cd \~/salmoncv
source venv/bin/activate

python --version
python -c "import numpy; print('numpy', numpy.\_\_version\_\_)"
python -c "from PIL import Image; print('Pillow ok')"
python -c "from pycoral.adapters import classify; print('pycoral classify ok')"
python -c "from pycoral.utils.edgetpu import make\_interpreter; print('pycoral edgetpu ok')"
lsusb
```

If all of those work, your Raspberry Pi is ready for Coral inference.









https://pidiylab.com/coral-tpu-raspberry-pi-5-setup/ 





