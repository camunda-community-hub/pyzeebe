import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="zeebepy",  # Replace with your own username
    version="0.0.1",
    author="Jonatan Martens",
    author_email="jonatanmartenstav@gmail.com",
    description="Zeebe client api",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JonatanMartens/pyzeebe",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
