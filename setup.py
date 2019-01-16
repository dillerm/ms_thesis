from distutils.core import setup


with open("README.md") as f:
    readme = f.read()

with open("LICENSE.txt") as f:
    license = f.read()

setup(
    name="Flu Scraper and Entity Resolver",
    version="0.1.0",
    description="Tool for scraping textual web-based reports on influenza epidemics; extracting location, date, pathogen, and host information; identifying individual epidemics; and connecting information about the same epidemic.",
    long_description=readme,
    author="Matthew Diller",
    author_email="diller17@ufl.edu",
    url="https://github.com/dillerm/ms_thesis",
    license=license,
    #packages=find_packages(exclude=[])
)