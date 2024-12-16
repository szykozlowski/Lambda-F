echo "Checking for existing lenv directory..."
if [ -d "lenv" ]; then
    echo "Removing existing lenv directory..."
    rm -rf lenv
fi

echo "Setting local Python version to 3.12.4..."
pyenv local 3.12.4

echo "Creating new virtual environment lenv..."
~/.pyenv/versions/3.12.4/bin/python -m venv lenv

echo "Activating new virtual environment..."
source lenv/bin/activate

echo 'python --version'
python --version 2>&1

python_version=$(python -c "import sys; print(sys.version.split()[0])")
if [[ $python_version != "3.12.4" ]]; then
    echo "Warning: Python version is $python_version, expected 3.12.4"
fi

echo "Installing requirements..."
pip install -r requirements.txt
