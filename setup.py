#!/usr/bin/env python
#-*- coding:utf-8 -*-

from email.utils import parseaddr
try:
	from setuptools import setup
except:
	from distutils.core import setup
import twopy
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
)
