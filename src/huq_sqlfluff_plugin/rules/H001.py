"""Implementation of Rule H001."""
from typing import Optional

from sqlfluff.core.rules import BaseRule, LintFix, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler
from sqlfluff.utils.reflow.reindent import construct_single_indent
from sqlfluff.core.parser.segments.raw import NewlineSegment, WhitespaceSegment


class Rule_H001(BaseRule):
    """The JOIN keyword must be isolated by itself in a signle line.

    **Anti-pattern**


    .. code-block:: sql
       :force:

        SELECT
            a
        FROM
            foo
        JOIN blah
        ON
            foo.a = blah.a

    **Best practice**

    .. code-block:: sql
       :force:

        SELECT
            a
        FROM
            foo
        JOIN
            blah
        ON
            foo.a = blah.a

    """
    name = "huq.isolated_join"
    aliases = ()
    groups = ("all", "layout")
    targets_templated = True
    crawl_behaviour = SegmentSeekerCrawler({"join_clause"})
    lint_phase = "main"
    is_fix_compatible = True

    def _eval(self, context: RuleContext) -> Optional[LintResult]:
        tab_space_size: int = context.config.get("tab_space_size", ["indentation"])
        indent_unit: str = context.config.get("indent_unit", ["indentation"])
        single_indent = construct_single_indent(indent_unit, tab_space_size)

        start_line = context.segment.get_start_loc()[0]
        for element in context.segment.recursive_crawl("from_expression_element"):
            element_line = element.get_start_loc()[0]
            if start_line == element_line:
                return LintResult(
                    anchor=context.segment,
                    fixes=[
                        LintFix.create_before(
                            anchor_segment=element,
                            edit_segments=[
                                NewlineSegment(),
                                WhitespaceSegment(single_indent)
                            ]
                        )
                    ],
                )
            break
