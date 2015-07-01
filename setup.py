import os
from setuptools import setup

try:
    from pypandoc import convert
    read_md = lambda f: convert(f, 'rst')
except ImportError:
    print("warning: pypandoc module not found, could not convert Markdown to RST")
    read_md = lambda f: open(f, 'r').read()

readme = os.path.join(os.path.dirname(__file__), 'README.md')
setup(
    name='everytrail_export',
    description='scraper for downloading trips from EveryTrail, including GPS data, story, and photos.',
    long_description=read_md(readme) if os.path.exists(readme) else '',
    version='0.2.1',
    url='https://github.com/mddub/everytrail_export',
    author='Mark Wilson',
    author_email='mark@warkmilson.com',
    license='MIT',
    packages=['everytrail_export'],
    install_requires=[
        'pyquery',
        'requests',
        'simplejson',
    ],
    # TODO
    entry_points={
        'console_scripts': [
            'everytrail_export = everytrail_export.cli:main'
        ]
    },
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
)
