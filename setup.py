#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from setuptools import setup

setup(
    name="lwm2mclient",
    version="0.1.0+git",
    description="Lightweight M2M Client written in Python",
    author="Nuannuan Wang",
    author_email="1961295051@qq.com",
    install_requires=["aiocoap>=0.2", "hexdump"]
)
