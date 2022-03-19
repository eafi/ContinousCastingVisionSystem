from distutils.core import setup
from Cython.Build import cythonize

setup(
    name='dd',
    ext_modules=cythonize(['camera.py'])
)