from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()
setup(
    name="osai",
    version="0.0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "osai = utils.cli:cli",
        ]
    },
    author="osai",
    author_email="abel@osai.com",
    description="Welcome to osai",
    long_description=open("readme.rst").read(),
    long_description_content_type="text/x-rst",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    include_package_data=True,
    install_requires=requirements,
    extras_require={"dev": ["pytest", "wheel", "twine", "black", "setuptools"]},
    dependency_links=[
        "git+ssh://git@github.com/InfinityCodebase/os-monitor-ai.git@e8aa987116606be359275052dd902496c142fadd#egg=osai&subdirectory=server"
    ]
)
