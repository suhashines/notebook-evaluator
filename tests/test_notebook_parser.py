import json
from notebook_evaluator.notebook_parser import parse_notebook


def test_extracts_identity_and_outputs(tmp_path):
    path = tmp_path / "student.ipynb"
    nb = {
        "nbformat": 4,
        "cells": [
            {"cell_type": "markdown", "source": ["header"]},
            {"cell_type": "code", "source": ['NAME = "Test Student"\nID = "24101251"'], "outputs": [], "execution_count": 1},
            {"cell_type": "code", "source": ["print('hello')"], "outputs": [{"output_type": "stream", "text": ["hello\\n"]}], "execution_count": 2},
        ],
    }
    path.write_text(json.dumps(nb), encoding="utf-8")
    parsed = parse_notebook(path)
    assert parsed["id"] == "24101251"
    assert parsed["name"] == "Test Student"
    assert "hello" in parsed["cells"][2]["outputs"][0]
