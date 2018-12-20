from typing import *
def uniq(xs: List[Any]) -> List[Any]:
    result = []
    seen = set()
    for x in xs:
        if x not in seen:
            result.append(x)
        seen.add(x)
    return result