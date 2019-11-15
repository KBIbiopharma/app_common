from os.path import abspath, dirname, join
from setuptools import setup, find_packages

HERE = dirname(abspath(__file__))

PKG_NAME = "app_common"

info = {}
init_file = join(HERE, PKG_NAME, "__init__.py")
exec(open(init_file).read(), globals(), info)


def read(fname):
    """ Returns content of the passed file.
    """
    return open(join(HERE, fname)).read()


setup(
    name=PKG_NAME,
    version=info["__version__"],
    author='KBI Biopharma Inc',
    author_email='jrocher@kbibiopharma.com',
    license='Proprietary',
    url='http://www.kbibiopharma.com/',
    description='Common Tools for KBI Applications',
    long_description=read('README.md'),
    ext_modules=[],
    packages=find_packages(),
    install_requires=[],
    requires=[],
    # Additional data files
    data_files=[(".", ["README.md", "LICENSE"])],
    entry_points={
        'console_scripts': [],
      },
)
