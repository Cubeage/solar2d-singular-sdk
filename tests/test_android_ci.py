import io
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import unittest
import zipfile

from scripts.check_android_package import check_package, ENTRY_POINT, ROOT


def archive(members):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as result:
        for name, data in members.items():
            result.writestr(name, data)
    return output.getvalue()


class AndroidPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "android.tgz"
        self.classes = {ENTRY_POINT: b"\xca\xfe\xba\xbe"}
        self.files = {
            "metadata.lua": (ROOT / "metadata.lua").read_bytes(),
            "corona.gradle": (ROOT / "android/corona.gradle").read_bytes(),
        }

    def write_package(self, missing_manifest=False, extra_member=None):
        aar = {"classes.jar": archive(self.classes)}
        if not missing_manifest:
            aar["AndroidManifest.xml"] = b"manifest fixture"
        self.files.setdefault("plugin-release.aar", archive(aar))
        with tarfile.open(self.path, "w:gz") as package:
            for name, data in self.files.items():
                member = tarfile.TarInfo("./" + name)
                member.size = len(data)
                package.addfile(member, io.BytesIO(data))
            if extra_member:
                package.addfile(extra_member, io.BytesIO())

    def test_accepts_consumer_package_contract(self):
        self.write_package()
        check_package(self.path)

    def test_rejects_missing_entry_point(self):
        self.classes.clear()
        self.write_package()
        with self.assertRaises(KeyError):
            check_package(self.path)

    def test_rejects_invalid_bytecode(self):
        self.classes[ENTRY_POINT] = b"not compiled Java"
        self.write_package()
        with self.assertRaises(ValueError):
            check_package(self.path)

    def test_rejects_missing_manifest(self):
        self.write_package(missing_manifest=True)
        with self.assertRaises(ValueError):
            check_package(self.path)

    def test_rejects_bundled_runtimes(self):
        for prefix in ("com/ansca/corona", "com/naef/jnlua", "com/singular/sdk"):
            with self.subTest(prefix=prefix):
                self.files.pop("plugin-release.aar", None)
                self.classes = {ENTRY_POINT: b"\xca\xfe\xba\xbe", prefix + "/Runtime.class": b"class"}
                self.write_package()
                with self.assertRaises(ValueError):
                    check_package(self.path)

    def test_rejects_missing_or_changed_metadata(self):
        for name in ("metadata.lua", "corona.gradle"):
            original = self.files[name]
            for changed in (False, True):
                with self.subTest(name=name, changed=changed):
                    self.files.pop(name, None)
                    if changed:
                        self.files[name] = b"wrong source"
                    self.write_package()
                    with self.assertRaises(ValueError):
                        check_package(self.path)
            self.files[name] = original

    def test_rejects_unexpected_duplicate_and_unsafe_members(self):
        for name in ("./metadata.lua", "../metadata.lua", "/metadata.lua", "extra.txt"):
            with self.subTest(name=name):
                self.write_package(extra_member=tarfile.TarInfo(name))
                with self.assertRaises(ValueError):
                    check_package(self.path)
        link = tarfile.TarInfo("./metadata.lua")
        link.type = tarfile.SYMTYPE
        link.linkname = "../metadata.lua"
        self.write_package(extra_member=link)
        with self.assertRaises(ValueError):
            check_package(self.path)

    def test_rejects_corrupt_aar(self):
        self.files["plugin-release.aar"] = b"not an AAR"
        self.write_package()
        with self.assertRaises(zipfile.BadZipFile):
            check_package(self.path)


class WorkflowContractTests(unittest.TestCase):
    def setUp(self):
        self.workflow = (ROOT / ".github/workflows/build-android.yml").read_text()

    def test_admits_pr_and_merge_group_without_path_filters(self):
        self.assertIn("  pull_request:\n", self.workflow)
        self.assertIn("  merge_group:\n    types: [checks_requested]\n", self.workflow)
        self.assertNotRegex(self.workflow, r"(?m)^\s+(paths|paths-ignore):")
        self.assertIn("  workflow_call:\n", self.workflow)
        self.assertIn("  workflow_dispatch:\n", self.workflow)
        self.assertIn("  push:\n    branches: [main]\n", self.workflow)

    def test_fan_in_requires_build_and_runs_even_after_failure(self):
        gate = self.workflow.split("\n  ci-ok:\n", 1)[1]
        self.assertIn("    if: ${{ always() }}\n", gate)
        self.assertIn("    needs: [build]\n", gate)
        self.assertIn("BUILD_RESULT: ${{ needs.build.result }}", gate)
        self.assertNotIn("continue-on-error", self.workflow)
        self.assertNotRegex(self.workflow, r"runs-on:.*(?:ubuntu|windows|macos)-")

    def test_actual_gate_command_fails_closed(self):
        command = re.search(r'(?m)^        run: (test "\$BUILD_RESULT".*)$', self.workflow).group(1)
        for result in ("success", "failure", "cancelled", "skipped", "", "not-run", "unknown"):
            with self.subTest(result=result):
                process = subprocess.run(["sh", "-c", command], env={**os.environ, "BUILD_RESULT": result})
                self.assertEqual(process.returncode == 0, result == "success")


if __name__ == "__main__":
    unittest.main()
