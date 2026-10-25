from tools.deploy import operations


def test_space_gets_its_own_card_and_the_app_files():
    files = {op.path_in_repo: op for op in operations()}
    assert str(files["README.md"].path_or_fileobj).endswith("space/README.md")
    assert {
        "Dockerfile",
        "uv.lock",
        "src/georeset_viz/app.py",
        "src/georeset_viz/static/app.js",
    } <= set(files)
    assert not any(p.startswith(("tests/", "tools/")) or "__pycache__" in p for p in files)
