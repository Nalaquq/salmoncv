# Coral TPU Setup

The Google Coral USB Accelerator requires Python 3.9 and specific PyCoral wheels. This guide sets up a clean environment using `pyenv` to avoid conflicts with the system Python.

## Why Python 3.9?

The PyCoral runtime libraries are only available as pre-built wheels for Python 3.9. Using the system Python (3.11+) or installing from PyPI will give you broken or incompatible packages.

## Install pyenv

Install build dependencies:

```bash
sudo apt install -y \
  make build-essential libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev \
  wget curl llvm libncursesw5-dev xz-utils tk-dev \
  libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
  git
```

Install pyenv:

```bash
curl https://pyenv.run | bash
```

Add to your shell startup (`~/.bashrc`):

```bash
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
```

Reload:

```bash
source ~/.bashrc
```

## Install Python 3.9

```bash
pyenv install 3.9.21
```

This compiles from source and takes 10--15 minutes on a Pi 5.

## Create Virtual Environment

```bash
cd ~/salmoncv
pyenv local 3.9.21
python -m venv venv
source venv/bin/activate
```

Verify:

```bash
python --version
# Should show Python 3.9.x
```

## Install Coral Libraries

Add the Coral apt repository:

```bash
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | \
  sudo tee /etc/apt/sources.list.d/coral-edgetpu.list

curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
  sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/coral.gpg

sudo apt update
sudo apt install -y libedgetpu1-std
```

Install PyCoral and TFLite:

```bash
pip install --extra-index-url https://google-coral.github.io/py-repo/ \
  pycoral~=2.0 tflite-runtime
```

!!! warning "NumPy version"
    PyCoral requires NumPy < 2.0. If you get NumPy errors:
    ```bash
    pip install "numpy<2"
    ```

## Verify

```bash
python -c "from pycoral.utils.edgetpu import list_edge_tpus; print(list_edge_tpus())"
```

Should print a list with one device. If empty, check the USB connection.

## Install SalmonCV

With the Coral libraries installed, install the full package:

```bash
cd ~/salmoncv
pip install -e .
```

## Test Inference

```bash
salmoncv-camera --model ~/salmoncv/models/fish_model.tflite \
                --labels ~/salmoncv/models/fish_labels.txt \
                --outdir ~/salmoncv/test_captures
```

!!! note
    You need a TFLite model and labels file. These are not included in the repository --- train or download a model separately.

## Next Steps

- [Getting Started](getting-started.md) --- test the full system
