import configparser
import datetime
import json
import pathlib
import re
import shutil
import subprocess
from functools import cached_property, lru_cache
from string import Template
from typing import List

import click


class JinjaConstructRemover:
    def __init__(self, patterns: List[str]) -> None:
        self.patterns = self.verify_patterns(patterns)

    @staticmethod
    def verify_patterns(patterns: List[str]) -> List[str]:
        for pattern in patterns:
            assert pattern[0] == "^", "Must assert start of line"

        return patterns

    def maybe_comment(self, content: str) -> str:
        if len(self.regexes[0].findall(content)):
            for regex in self.regexes:
                content = regex.sub(r"{# \1 #}", content)
        return content

    def maybe_uncomment(self, content: str) -> str:
        if len(self.commented_regexes[0].findall(content)):
            for regex in self.commented_regexes:
                content = regex.sub(r"\1", content)
        return content

    @cached_property
    def regexes(self) -> List[re.Pattern]:
        return [re.compile(pattern, flags=re.MULTILINE) for pattern in self.patterns]

    @cached_property
    def commented_regexes(self) -> List[re.Pattern]:
        commented_template = r"^{# %s #}"
        return [
            re.compile(commented_template % pattern[1:], flags=re.MULTILINE)
            for pattern in self.patterns
        ]


@lru_cache()
def repo_root():
    result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8').strip()


@click.group()
@click.pass_context
def main(ctx: click.Context):
    ctx.ensure_object(dict)
    ctx.obj["root_dir"] = pathlib.Path(repo_root())
    ctx.obj["local_dir"] = ctx.obj["root_dir"] / "local"
    ctx.obj["dbt_dir"] = ctx.obj["root_dir"] / "dbt"
    ctx.obj["macros_dir"] = ctx.obj["dbt_dir"] / "macros"
    ctx.obj["dbt_cfg"] = configparser.ConfigParser()

    ctx.obj["dbt_cfg"].read(str(ctx.obj["dbt_dir"] / "setup.cfg"))


@main.command("prelint")
@click.pass_context
def prelint(ctx: click.Context):
    backup_macros(ctx.obj["local_dir"], ctx.obj["macros_dir"])
    comment_all(ctx.obj["dbt_cfg"], ctx.obj["macros_dir"])


@main.command("postlint")
@click.pass_context
def postlint(ctx: click.Context):
    uncomment_all(ctx.obj["dbt_cfg"], ctx.obj["macros_dir"])


def backup_macros(local_dir: pathlib.Path, macros_dir: pathlib.Path):
    click.echo("Backing up dbt macros.")
    backup_dir = local_dir / "backups" / str(datetime.datetime.utcnow().timestamp())
    backup_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(macros_dir, backup_dir)
    click.echo(f"Successfully backed up dbt macros to {backup_dir}")


def get_jinja_construct_removers(
    dbt_cfg: configparser.ConfigParser,
) -> List[JinjaConstructRemover]:
    macro_suffixes = json.loads(
        dbt_cfg.get("sqlfluff-helper", "jinja_macros_to_comment_out")
    )
    macro_suffixes_joined = "|".join(map(re.escape, macro_suffixes))
    calls_fullmatch = json.loads(
        dbt_cfg.get("sqlfluff-helper", "jinja_calls_to_comment_out")
    )
    calls_fullmatch_joined = "|".join(map(re.escape, calls_fullmatch))

    macro_begin = Template(
        r"^(\s*{%[\+\-]?\s*macro\s*.*?(${suffixes_joined})\s*\((.|\s)*?\s*%})"
    ).substitute(suffixes_joined=macro_suffixes_joined)
    macro_end = r"^(\s*{%[\+\-]?\s*endmacro\s.*\s*%})"
    call_sql_header_begin = Template(
        r"^(\s*{%[\+\-]?\s*call\s*(${fullmatch_joined})\s*\((.|\s)*?\s*%})"
    ).substitute(fullmatch_joined=calls_fullmatch_joined)
    call_end = r"^(\s*{%[\+\-]?\s*endcall\s.*\s*%})"

    return [
        JinjaConstructRemover(patterns=[macro_begin, macro_end]),
        JinjaConstructRemover(patterns=[call_sql_header_begin, call_end]),
    ]


def comment_all(dbt_cfg: configparser.ConfigParser, macros_dir: pathlib.Path):
    removers = get_jinja_construct_removers(dbt_cfg)
    click.echo("Commenting jinja construct that interferes with linting.")
    for sql_file in macros_dir.glob("**/*.sql"):
        with sql_file.open("r") as fd:
            content = fd.read()
            for remover in removers:
                content = remover.maybe_comment(content)
        with sql_file.open("w") as fd:
            fd.write(content)
    click.echo("Successfully commented jinja construct that interferes with linting.")


def uncomment_all(dbt_cfg: configparser.ConfigParser, macros_dir: pathlib.Path):
    removers = get_jinja_construct_removers(dbt_cfg)
    click.echo("Un-commenting jinja construct that interferes with linting.")
    for sql_file in macros_dir.glob("**/*.sql"):
        with sql_file.open("r") as fd:
            content = fd.read()
            for remover in removers:
                content = remover.maybe_uncomment(content)
        with sql_file.open("w") as fd:
            fd.write(content)
    click.echo(
        "Successfully un-commented jinja construct that interferes with linting."
    )


def entrypoint():
    main(obj={})
