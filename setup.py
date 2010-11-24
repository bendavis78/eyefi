from setuptools import setup, find_packages

setup(
    name = "EyeFi",
    version = "0.1",
    packages = find_packages(),
    # scripts = ['say_hello.py'],

    install_requires = ['docutils>=0.3'],
    package_data = {
        # '': ['*.txt', '*.rst'],
    },

    author = "Robert Jordens",
    author_email = "jordens@phys.ethz.ch",
    description = "Eye-Fi SDHC cards + WiFi tools",
    long_description = """ """,
    license = "GPL",
    keywords = "eyefi twisted wifi photo cameras",
    #url = "http://",   # project home page, if any
)
