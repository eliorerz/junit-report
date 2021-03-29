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
    def increment_version(cls, branch_name: str):
        major, minor, patch = cls.get_version()
        if branch_name == "main":
            updated_patch = str(int(patch) + 1)
            updated_minor = minor
        else:
            updated_patch = 0
            updated_minor = str(int(minor) + 1)

        version = f"v{major}.{updated_minor}.{updated_patch}"
        print(f"Version patch incremented by one v{major}.{minor}.{patch} -> {version}")
        return version

    @classmethod
    def update_branch(cls):
        try:
            cls.sys_exec("git fetch --prune --unshallow".split())
        except subprocess.CalledProcessError:
            pass

    @classmethod
    def main(cls):
        print("Starting versioning process...")
        branch_name = cls.get_branch()
        if branch_name != "main" and not branch_name.startswith("release"):
            print("Tag occur only on release or main branch")
            return

        print(f"Fetching git history ({branch_name})... ", end="")
        cls.update_branch()
        print("Done")

        cls.tag(cls.increment_version(branch_name))
        print("Versioning process done!")


if __name__ == "__main__":
    GitVersion.main()
