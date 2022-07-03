import os
import pathlib
import subprocess
import sys

from aws_cdk.aws_lambda import Architecture, Code, Function, Runtime
from constructs import Construct


class BuildError(Exception):
    pass


class RustFunction(Function):
    _already_compiled = set()

    def __init__(
        self,
        scope: Construct,
        id_: str,
        *,
        binary_name: str,
        project_dir: str = None,
        **kwargs,
    ):
        project_dir = project_dir or os.getcwd()
        self._compile(project_dir)

        project_path = pathlib.Path(project_dir)
        asset_path = project_path / "target" / "lambda" / binary_name / "bootstrap.zip"
        code = Code.from_asset(asset_path.as_posix())

        super().__init__(
            scope,
            id_,
            handler="does.not.matter",
            runtime=Runtime.PROVIDED_AL2,
            architecture=Architecture.ARM_64,
            code=code,
            **kwargs,
        )

    def _compile(self, project_dir: str):
        if project_dir not in self._already_compiled:
            command = [
                "cargo",
                "lambda",
                "build",
                "--release",
                "--arm64",
                "--output-format",
                "zip",
            ]
            try:
                subprocess.run(command, capture_output=True, text=True, check=True)
            except subprocess.CalledProcessError as err:
                raise BuildError(f"failed to compile {project_dir}: {err.stderr}")

            self.__class__._already_compiled.add(project_dir)
            sys.stdout.write(f"Compiled cargo project in {project_dir}")
