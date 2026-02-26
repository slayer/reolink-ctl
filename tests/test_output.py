"""Tests for reolink_ctl.output."""

import json
from reolink_ctl.output import print_result, print_error, print_success


def test_print_result_dict(capsys):
    print_result({"model": "RLC-811A", "firmware": "v3.0"})
    out = capsys.readouterr().out
    assert "model" in out
    assert "RLC-811A" in out


def test_print_result_dict_json(capsys):
    print_result({"model": "RLC-811A"}, json_mode=True)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["model"] == "RLC-811A"


def test_print_result_list(capsys):
    print_result([{"name": "cam1", "online": True}])
    out = capsys.readouterr().out
    assert "cam1" in out
    assert "name" in out


def test_print_result_list_json(capsys):
    print_result([{"name": "cam1"}], json_mode=True)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data[0]["name"] == "cam1"


def test_print_result_empty_dict(capsys):
    print_result({})
    out = capsys.readouterr().out
    assert out == ""


def test_print_result_empty_list(capsys):
    print_result([])
    out = capsys.readouterr().out
    assert out == ""


def test_print_error(capsys):
    print_error("something broke")
    err = capsys.readouterr().err
    assert "something broke" in err


def test_print_error_json(capsys):
    print_error("something broke", json_mode=True)
    err = capsys.readouterr().err
    data = json.loads(err)
    assert data["error"] == "something broke"


def test_print_success(capsys):
    print_success("Done!")
    out = capsys.readouterr().out
    assert "Done!" in out


def test_print_success_json(capsys):
    print_success("Done!", json_mode=True)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "ok"
