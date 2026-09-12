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
        'q34-algorithm-flow',
        'q34-coverage-directional-proof',
        'q34-practice-summary',
        'q2-parameter-sensitivity',
        'q34-strategy-ablation',
        'q4-directional-stress',
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
        svg_lines = paths[2].read_text(encoding='utf-8').splitlines()
        assert not any(line.endswith((' ', '\t')) for line in svg_lines)
