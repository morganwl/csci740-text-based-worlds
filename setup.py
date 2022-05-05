import setuptools
import os

with open("README.md", "r") as fh:
    long_description = fh.read()

scripts = [os.path.join('scripts', script) for script in
           os.listdir('scripts') if script.endswith('.py')]

setuptools.setup(
    name="text-based-mwl",
    version="0.0.0",
    author="Morgan Wajda-Levie",
    author_email="morgan.wajdalevie@gmail.com",
    description=("Hunter class project. "
                 "AI agent for playing text-based games."),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/morganwl/csci740-text-based-worlds",
    packages=setuptools.find_packages(),
    scripts=scripts,
)
