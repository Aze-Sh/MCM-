import importlib.util


def figures_module():
    assert importlib.util.find_spec('b_figures'), 'B paper figures are not implemented'
    import b_figures
    return b_figures


def test_all_paper_figures_export_png_pdf_and_svg(tmp_path):
    module = figures_module()
    outputs = module.build_all(tmp_path)
    expected_stems = {
        'q1-region-counterexample',
        'q2-second-detector-region',
        'q34-practice-summary',
    }
    assert set(outputs) == expected_stems
    for stem, paths in outputs.items():
        assert stem in expected_stems
        assert {path.suffix for path in paths} == {'.png', '.pdf', '.svg'}
        for path in paths:
            assert path.exists()
            assert path.stat().st_size > 500
            assert path.stat().st_size < 2 * 1024 * 1024
        assert paths[1].read_bytes().startswith(b'%PDF')
