from setuptools import setup, find_packages

setup(
    name = 'mystique',
    version = '0.0.1',
    packages = find_packages(
        '.', 
        exclude = [
            '*.tests', '*.tests.*', 'tests.*', 'tests',
        ]
    ),
    package_dir = {
        '' : '.'
    },
    author = 'takumakanari',
    author_email = 'chemtrails.t@gmail.com',
    maintainer = 'takumakanari',
    maintainer_email = 'chemtrails@gmail.com',
    description = 'Mystique, MySQL utilities on terminal GUI.',
    classifiers = [
        'Development Status :: 4 - Beta'
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires = [
        'Cython',
        'MySQL-python',
        'urwid',
        'blinker'
    ],
    zip_safe = False,
    include_package_data = True,
    entry_points="""
    [console_scripts]
    mystique=mystique.mystique:main
    """
)

