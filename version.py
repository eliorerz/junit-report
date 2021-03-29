import re
import subprocess
from typing import List, Tuple


class GitVersion:
    CI_FLAG = "[CI]"

    @classmethod
    def sys_exec(cls, cmd: List[str]) -> None or str:
        try:
            out = subprocess.check_output(cmd).decode().strip()
        except subprocess.CalledProcessError:
            raise
        return out

    @classmethod
    def tag(cls, version: str):
        print(f"Adding new tag {version}")
        cls.sys_exec(f"git tag -a {version} -m ".split() + [" '{cls.CI_FLAG} - Version {version}'"])
        cls.sys_exec("git push origin --tags".split())

    @classmethod
    def get_branch(cls) -> str:
        return cls.sys_exec("git branch --show-current".split())

    @classmethod
    def get_version(cls) -> Tuple[str, str, str]:
        print("Getting version from last tag...")
        cls.sys_exec("python setup.py check".split())
        version = cls.sys_exec("git describe --abbrev=0".split())

        print(f"Found tag {version}")
        return re.compile(r"v([0-9])\.([0-9])\.([0-9])").findall(version).pop()  # major, minor, patch

    @classmethod
    def main(cls):
        print("Starting versioning process...")
        if cls.get_branch() != "main":
            print("Tag occur only on master/main branch")
            return

        print("Fetching git history... ", end="")
        cls.sys_exec("git fetch --prune --unshallow".split())
        print("Done")

        major, minor, patch = cls.get_version()
        updated_patch = str(int(patch) + 1)
        version = f"v{major}.{minor}.{updated_patch}"
        print(f"Version patch incremented by one v{major}.{minor}.{patch} -> {version}")
        cls.tag(version)

        print("Versioning process done!")


if __name__ == "__main__":
    GitVersion.main()
