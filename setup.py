#!/usr/bin/python

from setuptools import setup


setup(name='lms',
      version="1.1.10",
      description='Squeezebox server',
      py_modules=['lms'],
      url='https://github.com/molobrakos/lms',
      license="",
      scripts=["lms"],
      author='',
      author_email='',
      install_requires=list(
          open('requirements.txt').read().strip().split()))
