"""An example of a custom rule implemented through the plugin system.

This uses the rules API supported from 0.4.0 onwards.
"""

from sqlfluff.core.plugin import hookimpl
from sqlfluff.core.rules import (
    BaseRule,
)
from typing import List, Type

from .H001 import Rule_H001
from .H002 import Rule_H002
from .H003 import Rule_H003
from .H004 import Rule_H004
from .H005 import Rule_H005
from .H006 import Rule_H006
from .H007 import Rule_H007
from .H008 import Rule_H008


@hookimpl
def get_rules() -> List[Type[BaseRule]]:
    """Get plugin rules."""
    return [
        Rule_H001
        , Rule_H002
        , Rule_H003
        , Rule_H004
        , Rule_H005
        , Rule_H006
        , Rule_H007
        , Rule_H008
    ]
