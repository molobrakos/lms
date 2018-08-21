#!/usr/bin/python

from setuptools import setup
from lms import __version__


setup(name='lms',
      version=__version__,
      description='Squeezebox server',
      py_modules=['lms'],
      url='https://github.com/molobrakos/lms',
      license="",
      scripts=["lms"],
      author='',
      author_email='',
      install_requires=list(
          open('requirements.txt').read().strip().split()))
