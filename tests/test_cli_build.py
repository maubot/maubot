from pathlib import Path
import os
import subprocess
import sys
import zipfile


def test_build_omits_bytecode_from_module_packages(tmp_path):
    sources_and_resources = {
        "plugin/__init__.py": b"from .nested import Plugin\n",
        "plugin/nested/__init__.py": b"from maubot import Plugin\n",
        "plugin/nested/template.txt": b"{{ message }}\n",
        "plugin/example.pyc.txt": b"This is a text resource.\n",
        "helper.py": b"VALUE = 42\n",
        "assets/default.yaml": b"enabled: true\n",
        "assets/explicit.pyc": b"Explicitly selected resource\n",
    }
    caches = {
        "plugin/__pycache__/__init__.cpython-311.pyc": b"cached bytecode",
        "plugin/nested/__pycache__/data.txt": b"ignored cache content",
        "plugin/nested/legacy.pyc": b"legacy bytecode",
        "plugin/optimized.pyo": b"optimized bytecode",
    }
    for name, content in (sources_and_resources | caches).items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    (tmp_path / "maubot.yaml").write_text(
        "id: com.example.plugin\n"
        "version: 1.0.0\n"
        "modules: [helper, plugin]\n"
        "main_class: plugin/Plugin\n"
        "extra_files: ['assets/*']\n",
        encoding="utf-8",
    )

    env = {**os.environ, "XDG_CONFIG_HOME": str(tmp_path)}
    env.setdefault("HOME", str(Path.home()))
    result = subprocess.run(
        [sys.executable, "-m", "maubot.cli", "build"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    with zipfile.ZipFile(tmp_path / "com.example.plugin-v1.0.0.mbp") as archive:
        assert set(archive.namelist()) == {*sources_and_resources, "maubot.yaml"}
        for name, content in sources_and_resources.items():
            assert archive.read(name) == content
