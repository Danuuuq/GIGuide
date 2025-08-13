from typing import Any, Dict
from guide.selectors.nav import menu_links_qs

def common_context(**extra: Any) -> Dict[str, Any]:
    return {
        'menu_links': menu_links_qs(),
        **extra,
    }
