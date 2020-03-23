from setuptools import setup, find_packages
from shutil import copyfile
import os, platform


def get_long_description():
    this_directory = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(this_directory, 'docs/README.md')) as f:
        long_description = f.read()
        return long_description


def copy_docs():
    docs_dir = "musey/docs"
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    copyfile("docs/Header.png", docs_dir + "/Header.png")
    copyfile("docs/README.md", docs_dir + "/README.md")
    copyfile("docs/background.png", docs_dir + "/background.png")


copy_docs()
long_description = get_long_description()

setup(
    name="musey",
    version="1.0.0",
    description="Stream and visualize EEG data from the Muse headset.",
    keywords="muse lsl eeg ble neuroscience matlab UDP",
    url="",
    author="Bardia Barabadi",
    author_email="bardiabarabadi@uvic.ca",
    license="MIT",
    entry_points={"console_scripts": ["musey=musey.__main__:main"]},
    packages=['musey'],
    package_data={'musey': ['docs/Header.png', 'docs/background.png']},
    include_package_data=True,
    zip_safe=False,
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        "bitstring",
        "pygatt",
        "pandas",
        "scikit-learn",
        "numpy",
        "seaborn",
        "pexpect",
        "pillow",
        "kivy",
        "docutils",
        "pygments",
        "pyserial",
        "esptool",
        'pypiwin32 ; platform_system=="Windows"',
        'pylsl ; platform_system!="Linux"',
        'kivy.deps.glew ; platform_system=="Windows"',
        'kivy.deps.sdl2 ; platform_system=="Windows"',
        'kivy.deps.gstreamer ; platform_system=="Windows"',
        'pylsl==1.10.5 ; platform_system=="Linux"'
    ]
    ,
    classifiers=[
        # How mature is this project?  Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 4 - Beta",
        # Indicate who your project is intended for
        "Intended Audience :: Science/Research",
        "Topic :: Software Development",
        # Specify the Python versions you support here.  In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: MacOS",
        "Programming Language :: Python",
    ],
)
