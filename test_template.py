from pathlib import Path
from modsmith.generator.project import render_project

blueprint = {
    "mod_id": "test-mod",
    "mod_name": "Test Mod",
    "package_name": "com.testmod",
    "minecraft_version": "26.2",
    "fabric_loader_version": "0.19.5",
    "fabric_api_version": "0.161.0+26.2",
    "loom_version": "1.17-SNAPSHOT",
}

render_project(blueprint, Path("./test_output"))