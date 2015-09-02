from distutils.core import setup

setup(
    name='purepos-python3',
    version='2.4.90',
    packages=['purepos'],
    url='https://github.com/ppke-nlpg/purepos-python3',
    license='GNU Lesser Public License v3',
    author='Móréh Tamás',
    author_email='morta@digitus.itk.ppke.hu',
    description='PurePos is an open source hybrid morphological tagger',
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Natural Language :: English",
        "Natural Language :: Hungarian",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Text Processing :: Markup"
    ],
    entry_points={"console_scripts": ["purepos=purepos"]}
)

