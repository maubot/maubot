import setuptools
import os

path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "maubot", "__meta__.py")
__version__ = "UNKNOWN"
with open(path) as f:
    exec(f.read())

setuptools.setup(
    name="maubot",
    version=__version__,
    url="https://github.com/maubot/maubot",

    author="Tulir Asokan",
    author_email="tulir@maunium.net",

    description="A plugin-based Matrix bot system.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",

    packages=setuptools.find_packages(),

    install_requires=[
        "mautrix>=0.4,<0.5",
        "aiohttp>=3.0.1,<4",
        "SQLAlchemy>=1.2.3,<2",
        "alembic>=1.0.0,<2",
        "commonmark>=0.8.1,<1",
        "ruamel.yaml>=0.15.35,<0.16",
        "attrs>=18.1.0,<19",
    ],

    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Topic :: Communications :: Chat",
        "Framework :: AsyncIO",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    entry_points="""
        [console_scripts]
        maubot=maubot.__main__:main
    """,
    data_files=[
        (".", ["example-config.yaml"]),
    ],
)
