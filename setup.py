# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    install_requires=required,
    name='social_media_image_generator',
    version='0.1.0',
    description='This module allows you to generate social media images for your projects.',
    long_description=readme,
    author='Kyle Kirkby',
    author_email='kyle.kirkby@linaro.org',
    url='https://github.com/linaro-marketing/SocialMediaImageGenerator',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
