from scripts.fetch_articles import (
    LAWS,
    article_dir_name,
    parse_article_list_response,
)


def test_laws_has_all_eight():
    expected = {"BV", "ZGB", "OR", "ZPO", "StGB", "StPO", "SchKG", "VwVG"}
    assert set(LAWS) == expected


def test_article_dir_name():
    assert article_dir_name(1) == "art-001"
    assert article_dir_name(41) == "art-041"
    assert article_dir_name(1186) == "art-1186"


def test_article_dir_name_with_suffix():
    assert article_dir_name(6, suffix="a") == "art-006a"
    assert article_dir_name(319, suffix="bis") == "art-319bis"


def test_parse_article_list_response():
    sample = (
        "# VwVG — SR 172.021\n"
        "**Bundesgesetz vom 20. Dezember 1968**\n"
        "Consolidation date: 2022-07-01\n\n"
        "**88 articles**\n\n"
        "- Art. 1\n"
        "- Art. 2\n"
        "- Art. 5\n"
        "- Art. 11 a Eingefuegt durch Anhang...\n"
        "- Art. 11 b Eingefuegt durch Anhang...\n"
        "- Art. 25 a Eingefuegt durch Anhang...\n"
        "- Art. 46 a Eingefuegt durch Anhang...\n"
    )
    articles = parse_article_list_response(sample)
    assert len(articles) == 7
    assert articles[0] == {"number": 1, "suffix": "", "raw": "1"}
    assert articles[3] == {"number": 11, "suffix": "a", "raw": "11a"}
    assert articles[4] == {"number": 11, "suffix": "b", "raw": "11b"}


def test_parse_article_list_deduplicates():
    sample = (
        "# OR — SR 220\n**OR**\n\n**1613 articles**\n\n"
        "- Art. 1\n- Art. 1\n- Art. 1\n"
        "- Art. 2\n- Art. 2\n"
        "- Art. 6 a Eingefuegt...\n"
    )
    articles = parse_article_list_response(sample)
    assert len(articles) == 3
    assert articles[0]["number"] == 1
    assert articles[1]["number"] == 2
    assert articles[2] == {"number": 6, "suffix": "a", "raw": "6a"}


def test_parse_article_range_skipped():
    sample = "# OR\n**OR**\n\n**3 articles**\n\n- Art. 1\n- Art. 2 – 4\n- Art. 5\n"
    articles = parse_article_list_response(sample)
    assert len(articles) == 2
    assert articles[0]["number"] == 1
    assert articles[1]["number"] == 5
