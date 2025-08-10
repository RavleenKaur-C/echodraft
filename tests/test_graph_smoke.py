def test_imports():
    import echodraft
    from echodraft.ui.cli import app
    assert app is not None
