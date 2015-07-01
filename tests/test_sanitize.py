import unittest
from nose.tools import *  # flake8: noqa
from website.util import sanitize


class TestSanitize(unittest.TestCase):
    def test_escape_html(self):
        assert_equal(
            sanitize.clean_tag('<script> evil code </script>'),
            '&lt;script&gt; evil code &lt;/script&gt;',
        )
        assert_equal(
            sanitize.clean_tag('<img src=javascript:moreevil><img>'),
            '&lt;img src=&quot;javascript:moreevil&quot;&gt;&lt;img&gt;',
        )
        assert_equal(
            sanitize.clean_tag('<iframe src=evilsite>'),
            '&lt;iframe src=&quot;evilsite&quot;&gt;',
        )
        assert_equal(
            sanitize.clean_tag(');</span><script></script><span>'),
            ');&lt;/span&gt;&lt;script&gt;&lt;/script&gt;&lt;span&gt;',
        )

    def test_clean_tag(self):
        assert_equal(
            sanitize.clean_tag('\'\'\'\'\'"""""""<script></script>'),
            '&#39&#39&#39&#39&#39&quot;&quot;&quot;&quot;&quot;&quot;&quot;&lt;script&gt;&lt;/script&gt;',
        )

    def test_strip_html(self):
        assert_equal(
            sanitize.strip_html('<foo>bar</foo>'),
            'bar'
        )

    def test_unescape_html(self):
        assert_equal(
            sanitize.safe_unescape_html('&lt;&gt; diamonds &amp; diamonds &lt;&gt;'),
            '<> diamonds & diamonds <>'
        )
        assert_equal(
            sanitize.safe_unescape_html(['&lt;&gt;&amp;'])[0],
            '<>&'
        )
        assert_equal(
            sanitize.safe_unescape_html(('&lt;&gt;&amp;', ))[0],
            '<>&'
        )
        assert_equal(
            sanitize.safe_unescape_html({'key': '&lt;&gt;&amp;'})['key'],
            '<>&'
        )
