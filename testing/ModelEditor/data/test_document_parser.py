import data.yaml.document_parser as dp


def test_remove_diff_block():
    document_parser = dp.DocumentParser()
    document_parser.current_doc = '\n'.join([
        "a:",
        "  - 0",
        "  - 1",
        "  - 2",
        "b:",
        "  - b0",
        "  - b2",
        "c:& 3",
        "d: 5",
        "e: 5"
    ])
    document_parser.parsed_doc = '\n'.join([
        "a:",
        "  - 0",
        "  - 1",
        "b:",
        "  - b0",
        "  - b1",
        "  - b2",
        "c: 3",
        "d: 4",
        "e: 5"
    ])
    document_parser._error_line = 7
    diffed_doc = document_parser._remove_diff_block_at_error_line()
    assert diffed_doc[7] == '#c:& 3\n'
    assert diffed_doc[8] == '#d: 5\n'


if __name__ == '__main__':
    test_remove_diff_block()
