# SPDX-FileCopyrightText: 2026 Özgür ÇEKİÇ
# SPDX-License-Identifier: GPL-3.0-or-later

import os, gettext, logging

logger = logging.getLogger(__name__)

LOCALE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "locales")

def setup_i18n(lang="en"):
    """Initialize internationalization."""
    if lang == "en":
        return lambda x: x  # English = no translation
    
    try:
        trans = gettext.translation("mirza", LOCALE_DIR, languages=[lang], fallback=True)
        return trans.gettext
    except Exception as e:
        logger.debug("i18n setup failed: %s", e)
        return lambda x: x
