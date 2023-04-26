"""Implementation of Rule H006."""
from typing import Optional

from sqlfluff.core.rules import BaseRule, LintFix, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler
from sqlfluff.dialects.dialect_ansi import SelectClauseElementSegment
from sqlfluff.utils.reflow.reindent import construct_single_indent
from sqlfluff.core.parser.segments.raw import NewlineSegment, WhitespaceSegment


class Rule_H006(BaseRule):
    """The SELECT keyword must be isolated by itself in a signle line.

    **Anti-pattern**


    .. code-block:: sql
       :force:

        SELECT a
        FROM
            foo
        WHERE
            a.bar = 42
        GROUP BY
            1

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

    """
    name = "huq.isolated_select"
    aliases = ()
    groups = ("all", "layout")
    targets_templated = True
    crawl_behaviour = SegmentSeekerCrawler({"select_clause"})
    lint_phase = "main"
    is_fix_compatible = True

    def _eval(self, context: RuleContext) -> Optional[LintResult]:
        tab_space_size: int = context.config.get("tab_space_size", ["indentation"])
        indent_unit: str = context.config.get("indent_unit", ["indentation"])
        single_indent = construct_single_indent(indent_unit, tab_space_size)

        start_line = context.segment.get_start_loc()[0]
        last_whitespace_segment = None
        for segment in context.segment.recursive_crawl_all():

            if isinstance(segment, WhitespaceSegment):
                last_whitespace_segment = segment

            if isinstance(segment, SelectClauseElementSegment):
                segment_line = segment.get_start_loc()[0]
                if start_line == segment_line:
                    return LintResult(
                        anchor=context.segment,
                        fixes=[
                            LintFix.delete(last_whitespace_segment),
                            LintFix.create_before(
                                anchor_segment=segment,
                                edit_segments=[
                                    NewlineSegment(),
                                    WhitespaceSegment(single_indent)
                                ]
                            )
                        ],
                    )
                break
