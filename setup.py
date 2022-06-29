import os
import setuptools

__version__ = '0.1.0'


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='visip',
    version=__version__,
    license='GPL 3.0',
    description='Visual Simulation Programing',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Jan Brezina, Tomas Blazek',
    author_email='jan.brezina@tul.cz, tomas.blazek@tul.cz',
    url='https://github.com/geomop/visip',

    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3',
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Scientific/Engineering',
    ],

    keywords=[
        # eg: 'keyword1', 'keyword2', 'keyword3',
    ],

    packages=['visip', 'visip_gui'],  # setuptools.find_packages(where='src'),
    package_dir={'': 'src'},
    # py_modules=[os.path.splitext(os.path.basename(path))[0] for path in glob.glob('src/*.py')],
    # package_data={
    #     # If any package contains *.txt or *.rst files, include them:
    #     #'': ['*.txt', '*.rst'],
    #     # And include any *.msg files found in the 'hello' package, too:
    #     #'hello': ['*.msg'],
    # },

    # include automatically all files in the template MANIFEST.in

    include_package_data=True,
    zip_safe=False,
    install_requires=['numpy',
                      'PyQt5',
                      'attrs',
                      'pytypes',
                      'typing-inspect',
                      'pyqtgraph'],
    setup_requires=['wheel'],
    python_requires='>=3.8',
    # extras_require={
    #     # eg:
    #     #   'rst': ['docutils>=0.11'],
    #     #   ':python_version=="2.6"': ['argparse'],
    # },
    entry_points={
        'console_scripts': [
            'visip = visip_gui:main',
       ]
    },

    # ext_modules=ext_modules,
    # cmdclass={'build_ext': BuildExt}
    # test_suite='test.pytest_bih'
)