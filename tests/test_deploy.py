from georeset_viz import config
from tools.deploy import operations


def test_space_root_is_the_web_folder_plus_its_card(tmp_path, monkeypatch):
    for name in ["index.html", "js/app.js", "data/meta.json", "tests/search.test.js"]:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text("x")
    monkeypatch.setattr(config, "WEB_DIR", tmp_path)
    files = {op.path_in_repo: op for op in operations()}
    assert set(files) == {"index.html", "js/app.js", "data/meta.json", "README.md"}
    assert str(files["README.md"].path_or_fileobj).endswith("space/README.md")
