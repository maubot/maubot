import setuptools
import glob
import os

with open("requirements.txt") as reqs:
    install_requires = reqs.read().splitlines()

with open("optional-requirements.txt") as reqs:
    extras_require = {}
    current = []
    for line in reqs.read().splitlines():
        if line.startswith("#/"):
            extras_require[line[2:]] = current = []
        elif not line or line.startswith("#"):
            continue
        else:
            current.append(line)

extras_require["all"] = list({dep for deps in extras_require.values() for dep in deps})

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

    install_requires=install_requires,
    extras_require=extras_require,

    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Topic :: Communications :: Chat",
        "Framework :: AsyncIO",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    entry_points="""
        [console_scripts]
        mbc=maubot.cli:app
    """,
    data_files=[
        (".", ["example-config.yaml", "alembic.ini"]),
        ("alembic", ["alembic/env.py"]),
        ("alembic/versions", glob.glob("alembic/versions/*.py")),
    ],
    package_data={
        "maubot": ["management/frontend/build/*", "management/frontend/build/static/css/*",
                   "management/frontend/build/static/js/*"],
        "maubot.cli": ["res/*"],
    },
)
