curl https://www.python.org/ftp/python/3.8.8/python-3.8.8-amd64.exe --output python_installer.exe
python_installer.exe
pip install gdown

pip install numpy
pip install pyqt5
pip install pygame
gdown "https://drive.google.com/u/0/uc?id=12dC9Y2cRy6g0j_bqHw-SGgYNt1ku3w48&export=download"
tar -xf "chess app.zip"
del /f "chess app.zip"
del /f python_installer.exe
cd "chess app/dist"
rename Main.exe Chess.exe
Chess