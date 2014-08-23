from setuptools import setup, find_packages
import codecs
from os import path

here = path.abspath(path.dirname(__file__))


def long_description():
    with codecs.open('README.rst', encoding='utf8') as f:
        return f.read()

setup(
    name='taileff',
    version='0.1.0',

    description='tail -f for humans',
    long_description=long_description(),

    # The project's main homepage.
    url='https://github.com/willemt/taileff',
    author='willemt',
    author_email='himself@willemthiart.com',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: System :: Logging',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='development logging',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=['pygments', 'tailer', 'sqlparse', 'termcolor', 'docopt'],
    package_data={},
    data_files=[],
    entry_points={
        'console_scripts': [
            'tailf = taileff.__main__:main',
        ],
    },
)
