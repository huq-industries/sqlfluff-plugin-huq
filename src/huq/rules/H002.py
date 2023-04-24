"""Implementation of Rule H002."""
from typing import Optional

from sqlfluff.core.rules import BaseRule, LintFix, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler
from sqlfluff.utils.reflow.reindent import construct_single_indent
from sqlfluff.core.parser.segments.raw import KeywordSegment, NewlineSegment, WhitespaceSegment


class Rule_H002(BaseRule):
    """The ON keyword must be isolated by itself in a signle line.

    **Anti-pattern**


    .. code-block:: sql
       :force:

        SELECT
            a
        FROM
            foo
        JOIN
            blah
        ON foo.a = blah.a

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
    name = "huq.isolated_on"
    aliases = ()
    groups = ("all", "layout")
    targets_templated = True
    crawl_behaviour = SegmentSeekerCrawler({"join_on_condition"})
    lint_phase = "main"
    is_fix_compatible = True

    def _eval(self, context: RuleContext) -> Optional[LintResult]:
        tab_space_size: int = context.config.get("tab_space_size", ["indentation"])
        indent_unit: str = context.config.get("indent_unit", ["indentation"])
        single_indent = construct_single_indent(indent_unit, tab_space_size)

        start_line = context.segment.get_start_loc()[0]

        on_segment = None
        whitespace_segment = None
        for segment in context.segment.recursive_crawl_all():
            if isinstance(segment, KeywordSegment) and segment.raw.upper() == 'ON':
                on_segment = segment

            if on_segment is not None and isinstance(segment, WhitespaceSegment):
                whitespace_segment = segment
                break
        else:
            raise RuntimeError()

        for element in context.segment.recursive_crawl("expression"):
            element_line = element.get_start_loc()[0]
            if start_line == element_line:
                return LintResult(
                    anchor=context.segment,
                    fixes=[
                        LintFix.delete(anchor_segment=whitespace_segment),
                        LintFix.create_after(
                            anchor_segment=on_segment,
                            edit_segments=[
                                NewlineSegment(),
                                WhitespaceSegment(single_indent)
                            ]
                        ),
                    ],
                )
            break
