"""Setup file for an example rules plugin."""
from setuptools import find_packages, setup

# Change these names in your plugin, e.g. company name or plugin purpose.
PLUGIN_LOGICAL_NAME = "huq"
PLUGIN_ROOT_MODULE = "huq_sqlfluff_plugin"

setup(
    name=f"sqlfluff-plugin-{PLUGIN_LOGICAL_NAME}",
    version="1.1.0",
    include_package_data=True,
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "sqlfluff>=0.4.0",
        "click",
    ],
    entry_points={
        "sqlfluff": [f"sqlfluff_{PLUGIN_LOGICAL_NAME} = {PLUGIN_ROOT_MODULE}.rules"],
        'console_scripts': [f'sqlfluff-jinja-commenter={PLUGIN_ROOT_MODULE}.jinja_commenter:entrypoint'],
    },
)
