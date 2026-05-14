"""Tests for ``bsp2stk.paths``."""

from __future__ import annotations

from pathlib import Path

import pytest

from bsp2stk.paths import (
    bsp_open_dialog_start,
    default_bsp_dir,
    default_stk_dir,
)


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure env vars don't leak between tests."""
    monkeypatch.delenv("BSP2STK_BSP_DIR", raising=False)
    monkeypatch.delenv("BSP2STK_STK_DIR", raising=False)


class TestDefaultBspDir:
    def test_env_var_pointing_to_existing_dir_wins(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("BSP2STK_BSP_DIR", str(tmp_path))
        assert default_bsp_dir() == tmp_path

    def test_env_var_pointing_to_missing_dir_falls_through(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        missing = tmp_path / "does-not-exist"
        monkeypatch.setenv("BSP2STK_BSP_DIR", str(missing))
        monkeypatch.chdir(tmp_path)
        # No cwd/bsp either → None
        assert default_bsp_dir() is None

    def test_falls_back_to_cwd_bsp_when_it_exists(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        (tmp_path / "bsp").mkdir()
        monkeypatch.chdir(tmp_path)
        assert default_bsp_dir() == tmp_path / "bsp"

    def test_returns_none_when_nothing_resolves(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert default_bsp_dir() is None


class TestDefaultStkDir:
    def test_env_var_returned_as_is(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        target = tmp_path / "custom-stk"  # does not exist yet
        monkeypatch.setenv("BSP2STK_STK_DIR", str(target))
        assert default_stk_dir() == target

    def test_existing_env_var_dir_returned(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        target = tmp_path / "custom-stk"
        target.mkdir()
        monkeypatch.setenv("BSP2STK_STK_DIR", str(target))
        assert default_stk_dir() == target

    def test_falls_back_to_cwd_stk_when_it_exists(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        (tmp_path / "stk").mkdir()
        monkeypatch.chdir(tmp_path)
        assert default_stk_dir() == tmp_path / "stk"

    def test_returns_cwd_stk_even_when_missing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert default_stk_dir() == tmp_path / "stk"


class TestBspOpenDialogStart:
    def test_returns_resolved_bsp_dir_when_available(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("BSP2STK_BSP_DIR", str(tmp_path))
        assert bsp_open_dialog_start() == str(tmp_path)

    def test_returns_home_when_no_bsp_dir_resolvable(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert bsp_open_dialog_start() == str(Path.home())
