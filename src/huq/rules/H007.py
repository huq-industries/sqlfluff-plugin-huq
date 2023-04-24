"""Implementation of Rule H007."""
from typing import Optional

from sqlfluff.core.rules import BaseRule, LintFix, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler
from sqlfluff.utils.reflow.reindent import construct_single_indent
from sqlfluff.core.parser.segments.raw import KeywordSegment, NewlineSegment, WhitespaceSegment


class Rule_H007(BaseRule):
    """The HAVING keyword must be isolated by itself in a signle line.

    **Anti-pattern**


    .. code-block:: sql
       :force:

        SELECT
            a
        FROM
            foo
        WHERE
            a.bar = 42
        GROUP BY
            1
        HAVING TRUE

    **Best practice**

    .. code-block:: sql
       :force:

        SELECT
            a
        FROM
            foo
        WHERE
            a.bar = 42
        GROUP BY
            1
        HAVING
            TRUE

    """
    name = "huq.isolated_having"
    aliases = ()
    groups = ("all", "layout")
    targets_templated = True
    crawl_behaviour = SegmentSeekerCrawler({"having_clause"})
    lint_phase = "main"
    is_fix_compatible = True

    def _eval(self, context: RuleContext) -> Optional[LintResult]:
        tab_space_size: int = context.config.get("tab_space_size", ["indentation"])
        indent_unit: str = context.config.get("indent_unit", ["indentation"])
        single_indent = construct_single_indent(indent_unit, tab_space_size)

        having_segment = None
        whitespace_segment = None
        for segment in context.segment.recursive_crawl_all():
            if isinstance(segment, KeywordSegment) and segment.raw.upper() == 'HAVING':
                having_segment = segment

            if having_segment is not None and isinstance(segment, WhitespaceSegment):
                whitespace_segment = segment
                break
        else:
            raise RuntimeError()

        start_line = context.segment.get_start_loc()[0]
        for element in context.segment.recursive_crawl("expression"):
            element_line = element.get_start_loc()[0]
            if start_line == element_line:
                return LintResult(
                    anchor=context.segment,
                    fixes=[
                        LintFix.delete(anchor_segment=whitespace_segment),
                        LintFix.create_after(
                            anchor_segment=having_segment,
                            edit_segments=[
                                NewlineSegment(),
                                WhitespaceSegment(single_indent)
                            ]
                        ),
                    ],
                )
            break
