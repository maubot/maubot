import setuptools
import maubot

setuptools.setup(
    name="maubot",
    version=maubot.__version__,
    url="https://github.com/maubot/maubot",

    author="Tulir Asokan",
    author_email="tulir@maunium.net",

    description="A plugin-based Matrix bot system.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",

    packages=setuptools.find_packages(),

    install_requires=[
        "aiohttp>=3.0.1,<4",
        "SQLAlchemy>=1.2.3,<2",
        "Markdown>=2.6.11,<3",
        "ruamel.yaml>=0.15.35,<0.16",
    ],

    classifiers=[
        "Development Status :: 3 :: Alpha",
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
