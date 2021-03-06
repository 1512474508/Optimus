import os
import re
import sys

from setuptools import setup, find_packages

from functools import reduce



# from optimus.version import __version__

# Get version without importing, which avoids dependency issues
def get_version():
    with open('optimus/version.py') as version_file:
        return re.search(r"""__version__\s+=\s+(['"])(?P<version>.+?)\1""",
                         version_file.read()).group('version')


if sys.version_info < (3, 6):
    raise RuntimeError('This version requires Python 3.6+')  # pragma: no cover


def readme():
    with open('README.md') as f:
        return f.read()


# Requirements
try:
    import google.colab

    IN_COLAB = True
except ImportError:
    IN_COLAB = False

if "DATABRICKS_RUNTIME_VERSION" in os.environ:
    with open('requirements-databricks.txt') as f:
        required = f.read().splitlines()
elif IN_COLAB:
    with open('requirements-google-colab.txt') as f:
        required = f.read().splitlines()
else:
    with open('requirements.txt') as f:
        required = f.read().splitlines()

extras_requirements_keys = ['spark', 'ai', 'db']
extras_requirements = {}
for extra in extras_requirements_keys:
    with open('requirements-'+extra+'.txt') as f:
        extras_requirements[extra] = f.read().splitlines()

lint_requirements = ['pep8', 'pyflakes']
test_requirements = ['pytest', 'mock', 'nose']
dependency_links = []
setup_requirements = ['pytest-runner']
if 'nosetests' in sys.argv[1:]:
    setup_requirements.append('nose')

setup(
    name='optimuspyspark',
    version=get_version(),
    author='Argenis Leon',
    author_email='argenisleon@gmail.com',
    url='https://github.com/ironmussa/Optimus/',
    description=('Optimus is the missing framework for cleaning and pre-processing data in a distributed fashion.'),
    long_description=readme(),
    long_description_content_type='text/markdown',
    license='APACHE',
    packages=find_packages(),
    install_requires=required,
    tests_require=test_requirements,
    setup_requires=setup_requirements,
    extras_require={
        'test': test_requirements,
        'all': test_requirements + reduce(lambda x, key: x + extras_requirements[key], extras_requirements, []),
        'docs': ['sphinx'] + test_requirements,
        'lint': lint_requirements,
        **extras_requirements
    },
    dependency_links=dependency_links,
    test_suite='nose.collector',
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords=['datacleaner', 'apachespark', 'spark', 'pyspark', 'data-wrangling', 'data-cleansing', 'data-profiling'],
)
