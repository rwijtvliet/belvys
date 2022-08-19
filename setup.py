from setuptools import setup
from setuptools import find_packages
import versioneer

setup(
    name="belvys",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="Ruud Wijtvliet",
    zip_safe=False,
    packages=find_packages(exclude=["tests"]),
    description="Getting timeseries data from Belvis Rest API.",
    long_description=open("README.rst").read(),
    long_description_content_type="text/x-rst",
    python_requires=">=3.8",
    install_requires=[line.strip() for line in open("requirements.txt", "r")],
    # package_data is data that is deployed within the python package on the
    # user's system. setuptools will get whatever is listed in MANIFEST.in
    include_package_data=True,
)
