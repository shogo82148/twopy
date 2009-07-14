#!/usr/bin/env python
#-*- coding:utf-8 -*-

from email.Utils import parseaddr
try:
	from setuptools import setup
except:
	from distutils.core import setup

name = twopy.__name__
author, email = parseaddr(twopy.__author__)

setup(
	name             = "twopy",
	version          = twopy.__version__,
	author           = author,
	author_email     = email,
	url              = twopy.__url__,
	license          = twopy.__license__,
	packages         = ["twopy"],
	platforms        = ["any"],
	install_requires = [""],
	zip_safe         = True,
)
