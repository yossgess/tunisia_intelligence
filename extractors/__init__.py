"""
Extractors package

Provides registries that map specific feed URLs and domains to the
corresponding extractor functions. This allows a centralized dispatcher
to route any given RSS URL to the right extractor implementation.
"""

from typing import Callable, Dict

# Import extract() functions from each extractor module
from .nawaat_extractor import extract as extract_nawaat
from .assarih_extractor import extract as extract_assarih
from .webmanagercenter_extractor import extract as extract_wmc
from .radioexpressfm_extractor import extract as extract_radioexpress
from .realites_extractor import extract as extract_realites
from .radiotunisienne_extractor import extract as extract_radiotunisienne
from .leaders_extractor import extract as extract_leaders
from .africanmanager_extractor import extract as extract_africanmanager
from .leconomistemaghrebin_extractor import extract as extract_leconomiste
from .alchourouk_extractor import extract as extract_alchourouk
from .webdo_extractor import extract as extract_webdo
from .babnet_extractor import extract as extract_babnet
from .nessma_extractor import extract as extract_nessma
from .tunisienumerique_extractor import extract as extract_tunisienumerique
from .essahafa_extractor import extract as extract_essahafa
from .radiotataouine_extractor import extract as extract_radiotataouine
from .radiogafsa_extractor import extract as extract_radiogafsa
from .radiokef_extractor import extract as extract_radiokef
from .rtci_extractor import extract as extract_rtci
from .radiomonastir_extractor import extract as extract_radiomonastir
from .radionationale_extractor import extract as extract_radionationale
from .radiosfax_extractor import extract as extract_radiosfax
from .radiomedtunisie_extractor import extract as extract_radiomed
from .inkyfada_extractor import extract as extract_inkyfada
from .ftdes_extractor import extract as extract_ftdes
from .lapresse_extractor import extract as extract_lapresse
from .oasis_extractor import extract as extract_oasis
from .businessnews_extractor import extract as extract_businessnews
from .jawharafm_extractor import extract as extract_jawharafm
from .jawharafm_politics_extractor import extract as extract_jawharafm_politics
from .jawharafm_cat_88_1_2_extractor import extract as extract_jawharafm_cat_88_1_2


# Exact feed URL registry
EXTRACTOR_REGISTRY: Dict[str, Callable[..., list]] = {
    # Newspapers / portals
    "https://nawaat.org/feed/": extract_nawaat,
    "http://assarih.com/feed/": extract_assarih,
    "https://www.webmanagercenter.com/feed/": extract_wmc,
    "https://realites.com.tn/feed/": extract_realites,
    "https://www.leaders.com.tn/rss": extract_leaders,
    "https://africanmanager.com/feed/": extract_africanmanager,
    "https://www.leconomistemaghrebin.com/feed/": extract_leconomiste,
    "https://www.alchourouk.com/rss": extract_alchourouk,
    "https://www.webdo.tn/fr/feed/": extract_webdo,
    "https://www.babnet.net/feed.php": extract_babnet,
    "http://www.businessnews.com.tn/rss.xml": extract_businessnews,
    "https://www.tunisienumerique.com/feed-actualites-tunisie.xml": extract_tunisienumerique,
    "https://essahafa.tn/feed/": extract_essahafa,
    "https://lapresse.tn/feed/": extract_lapresse,
    "https://inkyfada.com/en/feed/": extract_inkyfada,
    "https://ftdes.net/feed/": extract_ftdes,

    # Radios / media
    "https://radioexpressfm.com/fr/feed/": extract_radioexpress,
    "https://www.radiotunisienne.tn/articles/rss": extract_radiotunisienne,
    "https://www.radiotataouine.tn/articles/rss": extract_radiotataouine,
    "https://www.radiogafsa.tn/articles/rss": extract_radiogafsa,
    "https://www.radiokef.tn/articles/rss": extract_radiokef,
    "https://www.rtci.tn/articles/rss": extract_rtci,
    "https://www.radiomonastir.tn/articles/rss": extract_radiomonastir,
    "https://www.radionationale.tn/articles/rss": extract_radionationale,
    "https://www.radiosfax.tn/articles/rss": extract_radiosfax,
    "https://radiomedtunisie.com/feed/": extract_radiomed,
    "https://www.nessma.tv/fr/rss/news/7": extract_nessma,
    "https://oasis-fm.net/feed/": extract_oasis,
    # Jawhara FM variants
    "https://www.jawharafm.net/ar/rss/showRss/88/1/1": extract_jawharafm,
    "https://www.jawharafm.net/ar/rss/showRss/88/1/4": extract_jawharafm_politics,
    "https://www.jawharafm.net/ar/rss/showRss/88/1/2": extract_jawharafm_cat_88_1_2,
}


# Fallback by domain (use when an exact URL key isn't present)
DOMAIN_REGISTRY: Dict[str, Callable[..., list]] = {
    "nawaat.org": extract_nawaat,
    "assarih.com": extract_assarih,
    "webmanagercenter.com": extract_wmc,
    "realites.com.tn": extract_realites,
    "leaders.com.tn": extract_leaders,
    "africanmanager.com": extract_africanmanager,
    "leconomistemaghrebin.com": extract_leconomiste,
    "alchourouk.com": extract_alchourouk,
    "webdo.tn": extract_webdo,
    "babnet.net": extract_babnet,
    "businessnews.com.tn": extract_businessnews,
    "tunisienumerique.com": extract_tunisienumerique,
    "essahafa.tn": extract_essahafa,
    "lapresse.tn": extract_lapresse,
    "inkyfada.com": extract_inkyfada,
    "ftdes.net": extract_ftdes,
    "radioexpressfm.com": extract_radioexpress,
    "radiotunisienne.tn": extract_radiotunisienne,
    "radiotataouine.tn": extract_radiotataouine,
    "radiogafsa.tn": extract_radiogafsa,
    "radiokef.tn": extract_radiokef,
    "rtci.tn": extract_rtci,
    "radiomonastir.tn": extract_radiomonastir,
    "radionationale.tn": extract_radionationale,
    "radiosfax.tn": extract_radiosfax,
    "radiomedtunisie.com": extract_radiomed,
    "nessma.tv": extract_nessma,
    "oasis-fm.net": extract_oasis,
    "jawharafm.net": extract_jawharafm,
}
