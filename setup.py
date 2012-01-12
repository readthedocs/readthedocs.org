import os
from setuptools import setup, find_packages

#libraries = [l.strip() for l in open('pip_requirements.txt').readlines()]

setup(
    name='readthedocs',
    version="1.0",
    description='A documentation hosting website',
    #long_description=readme,
    author='Eric Holscher, Charles Leifer, Bobby Grace',
    author_email='eric@ericholscher.com',
    url='http://readthedocs.org',
    packages=find_packages(),
    include_package_data=True,
    #install_requires=libraries,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    #test_suite='readthedocs.tests.rtd_tests.runtests'
)
