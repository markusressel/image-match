"""
image_match is a simple package for finding approximate image matches from a
corpus. It is similar, for instance, to pHash <http://www.phash.org/>, but
includes a database backend that easily scales to billions of images and
supports sustained high rates of image insertion: up to 10,000 images/s on our
cluster!

Based on the paper An image signature for any kind of image, Goldberg et
al <http://www.cs.cmu.edu/~hcwong/Pdfs/icip02.ps>.
"""
import io
import os
import re

from setuptools import setup, find_packages


def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ) as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(
        r'^__version__ = [\'"]([^\'"]*)[\'"]', version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


def locked_requirements(section):
    """
    Look through the 'Pipfile.lock' to fetch requirements by section.
    """
    import json

    with open('Pipfile.lock') as pip_file:
        pipfile_json = json.load(pip_file)

    if section not in pipfile_json:
        print("{0} section missing from Pipfile.lock".format(section))
        return []

    return [package + detail.get('version', "")
            for package, detail in pipfile_json[section].items()]


dev_require = [
    'ipdb',
    'ipython',
]

docs_require = [
    'recommonmark>=0.4.0',
    'Sphinx>=1.3.5',
    'sphinxcontrib-napoleon>=0.4.4',
    'sphinx-rtd-theme>=0.1.9',
]

setup(
    name='image_match',
    version=find_version('image_match', '__init__.py'),
    description='image_match is a simple package for finding approximate ' \
                'image matches from a corpus.',
    long_description=__doc__,
    url='https://github.com/ascribe/image-match/',
    author='Ryan Henderson',
    author_email='ryan@bigchaindb.com',
    license='Apache License 2.0',
    zip_safe=True,

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Database',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: Software Development',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Topic :: Multimedia :: Graphics',
    ],

    packages=find_packages(),

    install_requires=locked_requirements('default'),
    tests_require=locked_requirements('develop'),
    extras_require={
        'test': locked_requirements('develop'),
        'dev': dev_require + locked_requirements('develop') + docs_require,
        'docs': docs_require,
        'extra': ['cairosvg>1,<2'],
    },
)
