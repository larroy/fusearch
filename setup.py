from setuptools import find_packages, setup


INSTALL_REQUIRES = ["textract", "nltk"]

EXTRAS_REQUIRE = {"test": ["flake8", "black", "mock", "pre-commit", "pytest"]}


with open("README.md", "r") as f:
    LONG_DESCRIPTION = f.read()


setup(
    name="fusearch",
    version="0.1",
    author="Pedro Larroy",
    author_email="pedro.larroy.lists@gmail.com",
    description="fusearch is a local full text search engine",
    license="Apache 2",
    keywords="search console fulltext documents",
    url="https://github.com/larroy/fusearch",
    project_urls={"Source Code": "https://github.com/larroy/fusearch",},
    packages=find_packages("src"),
    package_dir={"": "src"},
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
    ],
    package_data={},
    scripts=["bin/fusearchd.py"],
)
