# The setup.py file is essential for packaging. Here’s a basic template:

from setuptools import setup, find_packages

setup(
    name="OpenAIGymUtils",
    version="0.1",
    packages=find_packages(),
    install_requires=[],  # List your dependencies
    description="Various utilities for the Open AI Gym environment",
    author="Jan Orbech Pederseb",
    author_email="jan.o.pedersen@mail.dk",
    url="https://github.com/your_username/your_package_name",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11.11',
)