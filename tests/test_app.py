# -*- coding: utf-8 -*-
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as learnmap  # noqa: E402


import pytest  # noqa: E402


@pytest.fixture()
def client():
    learnmap.app.config.update(TESTING=True)
    return learnmap.app.test_client()


def test_index_ok(client):
    rv = client.get("/")
    assert rv.status_code == 200
    html = rv.get_data(as_text=True)
    assert "learnmap" in html
    assert "Python" in html  # 収録テーマのチップが出ている
    assert "/go" in html     # 検索フォーム


def test_registered_topic_map(client):
    rv = client.get("/map/Python")
    assert rv.status_code == 200
    html = rv.get_data(as_text=True)
    assert "<svg" in html
    for stage in ["前提", "基礎", "核心", "応用", "実践"]:
        assert stage in html
    assert "変数とデータ型" in html
    assert "クラスとオブジェクト指向" in html
    assert "汎用マップ" not in html  # 登録テーマでは汎用表示にならない


def test_registered_topics_have_enough_nodes():
    assert len(learnmap.KB) == 24
    for topic, nodes in learnmap.KB.items():
        assert 8 <= len(nodes) <= 10, topic
        stages = {n["stage"] for n in nodes}
        assert stages <= set(learnmap.STAGES), topic


def test_build_map_registered():
    m = learnmap.build_map("統計学")
    assert m["generic"] is False
    assert m["topic"] == "統計学"
    assert len(m["nodes"]) >= 8
    assert len(m["edges"]) == len(m["nodes"]) - 1


def test_unregistered_topic_uses_template(client):
    m = learnmap.build_map("量子ダンス")
    assert m["generic"] is True
    assert len(m["nodes"]) == 5
    assert [n["stage"] for n in m["nodes"]] == learnmap.STAGES
    rv = client.get("/map/量子ダンス")
    assert rv.status_code == 200
    html = rv.get_data(as_text=True)
    assert "登録外テーマ向けの汎用マップ" in html
    rv = client.get("/map/量子ダンス?node=n0")
    assert "Wikipediaで「量子ダンス」を調べる" in rv.get_data(as_text=True)


def test_node_detail(client):
    rv = client.get("/map/Python?node=n0")
    assert rv.status_code == 200
    html = rv.get_data(as_text=True)
    assert "プログラミングとは" in html
    assert "学習リソース" in html
    assert "学習済みにする" in html


def test_all_links_are_https():
    for topic in learnmap.KB:
        m = learnmap.build_map(topic)
        for n in m["nodes"]:
            assert n["links"], (topic, n["title"])
            for _label, url in n["links"]:
                assert url.startswith("https://"), (topic, n["title"], url)
    m = learnmap.build_map("未登録の何か")
    for n in m["nodes"]:
        for _label, url in n["links"]:
            assert url.startswith("https://"), url


def test_rendered_external_links_https(client):
    html = client.get("/map/機械学習?node=n2").get_data(as_text=True)
    ext = re.findall(r'href="(http[^"]+)"', html)
    assert ext, "外部リンクが描画されていること"
    assert all(u.startswith("https://") for u in ext)


def test_go_redirect(client):
    rv = client.get("/go?q=写真")
    assert rv.status_code in (301, 302)
    assert "/map/" in rv.headers["Location"]


def test_healthz(client):
    rv = client.get("/healthz")
    assert rv.status_code == 200
    assert rv.get_data(as_text=True) == "ok"
