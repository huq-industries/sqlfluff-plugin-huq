"""Implementation of Rule H008."""
from typing import Optional

from sqlfluff.core.rules import BaseRule, LintFix, LintResult, RuleContext
from sqlfluff.core.rules.crawlers import SegmentSeekerCrawler
from sqlfluff.dialects.dialect_ansi import ComparisonOperatorSegment, CompositeComparisonOperatorSegment
from sqlfluff.core.parser.segments.raw import NewlineSegment, RawSegment


class Rule_H008(BaseRule):
    """

    **Anti-pattern**


    .. code-block:: sql
       :force:

        SELECT
            a
        FROM
            foo
        WHERE
            extremely_long_line_here + extremely_long_line_here + extremely_long_line_here
            = 1
        GROUP BY 1

    **Best practice**

    .. code-block:: sql
       :force:

        SELECT
            a
        FROM
            foo
        WHERE
            (
                extremely_long_line_here + extremely_long_line_here + extremely_long_line_here
            ) = 1
        GROUP BY
            1

    """
    name = "huq.isolated_groupby"
    aliases = ()
    groups = ("all", "layout")
    targets_templated = True
    crawl_behaviour = SegmentSeekerCrawler({"where_clause", "join_on_condition"})
    lint_phase = "main"
    is_fix_compatible = True

    def _eval(self, context: RuleContext) -> Optional[LintResult]:
        # Look for comparison operator and the previous non-whitespace/indent segment,
        # if they are on different lines, then enforce there is a bracket.
        # To enforce there is a bracket, we need to detect when does the expression start
        # as well, this is either the start of the expression or any segment after a
        # AND/OR/||/XOR
        # . (Remember: By definition the expression ends before the comparison operator)

        operators = {
            "AND",
            "&&",
            "OR",
            "||",
            "XOR",
        }

        # Go through all expressions
        for expression in context.segment.recursive_crawl('expression'):
            first_segment = None
            previous_non_space_segment = None
            # Go through component in the expression
            for segment in expression.recursive_crawl_all():
                # Store first segment
                if first_segment is None and not segment.is_whitespace:
                    first_segment = segment

                # Upon comparison operator, check if it's naked, yell if so.
                if isinstance(segment, (ComparisonOperatorSegment, CompositeComparisonOperatorSegment)):
                    comparison_operator_start = segment.get_start_loc()[0]
                    previous_non_space_segment_start = previous_non_space_segment.get_start_loc()[0]
                    if comparison_operator_start != previous_non_space_segment_start:
                        return LintResult(
                            anchor=context.segment,
                            fixes=[
                                LintFix.create_before(
                                    anchor_segment=first_segment,
                                    edit_segments=[
                                        RawSegment('('),
                                        NewlineSegment(),
                                        # NOTE: Specifically NOT including an indent here
                                        #       we will just rely on other rules to help us add this properly.
                                        #       I can't work out why two passes is needed even with ident added here
                                        #       so just roll with making two passes with sqlfluff and doing minimal work
                                        #       for now (i.e. not adding indent here at all).
                                    ]
                                ),
                                LintFix.create_before(
                                    anchor_segment=segment,
                                    edit_segments=[
                                        RawSegment(') ')
                                    ]
                                ),
                            ],
                        )

                if not segment.is_whitespace:
                    previous_non_space_segment = segment

                # Unset first_segment so we can move the first_segment to the first segment after an binary operator
                if segment.raw.upper() in operators:
                    first_segment = None
