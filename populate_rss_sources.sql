-- Populate RSS sources for Tunisia Intelligence system
-- This script inserts all RSS feed sources into the sources table

INSERT INTO sources (name, url, source_type, is_active, description, created_at, updated_at) VALUES
-- News and Media Sources
('Nawaat', 'https://nawaat.org/feed/', 'rss', true, 'Independent Tunisian news platform', NOW(), NOW()),
('Assarih', 'https://assarih.com/feed/', 'rss', true, 'Tunisian news website', NOW(), NOW()),
('Web Manager Center', 'https://webmanagercenter.com/feed/', 'rss', true, 'Business and technology news', NOW(), NOW()),
('L''Economiste Maghrébin', 'https://leconomistemaghrebin.com/feed/', 'rss', true, 'Economic news for Maghreb region', NOW(), NOW()),
('Radio Express FM', 'https://radioexpressfm.com/fr/feed/', 'rss', true, 'Tunisian radio station news', NOW(), NOW()),
('Réalités', 'https://realites.com.tn/feed/', 'rss', true, 'Tunisian news magazine', NOW(), NOW()),
('Leaders', 'https://www.leaders.com.tn/rss', 'rss', true, 'Business and economic news', NOW(), NOW()),
('African Manager', 'https://africanmanager.com/feed/', 'rss', true, 'African business and economic news', NOW(), NOW()),
('Al Chourouk', 'https://www.alchourouk.com/rss', 'rss', true, 'Tunisian Arabic newspaper', NOW(), NOW()),
('Webdo', 'https://www.webdo.tn/fr/feed/', 'rss', true, 'Tunisian online news portal', NOW(), NOW()),
('Babnet', 'https://www.babnet.net/feed.php', 'rss', true, 'Tunisian news aggregator', NOW(), NOW()),
('Nessma TV', 'https://www.nessma.tv/fr/rss/news/7', 'rss', true, 'Tunisian television news', NOW(), NOW()),
('Tunisie Numérique', 'https://www.tunisienumerique.com/feed-actualites-tunisie.xml', 'rss', true, 'Digital news platform', NOW(), NOW()),
('Business News', 'https://www.businessnews.com.tn/rss.xml', 'rss', true, 'Tunisian business news', NOW(), NOW()),
('Essahafa', 'https://essahafa.tn/feed/', 'rss', true, 'Tunisian news website', NOW(), NOW()),
('La Presse', 'https://lapresse.tn/feed/', 'rss', true, 'Tunisian French-language newspaper', NOW(), NOW()),
('Radio Med Tunisie', 'https://radiomedtunisie.com/feed/', 'rss', true, 'Tunisian radio station', NOW(), NOW()),
('Oasis FM', 'https://oasis-fm.net/feed/', 'rss', true, 'Tunisian radio station', NOW(), NOW()),
('Inkyfada', 'https://inkyfada.com/en/feed/', 'rss', true, 'Independent media platform', NOW(), NOW()),
('FTDES', 'https://ftdes.net/feed/', 'rss', true, 'Tunisian Forum for Economic and Social Rights', NOW(), NOW()),

-- Regional Radio Stations
('Radio Tunisienne', 'https://www.radiotunisienne.tn/articles/rss', 'rss', true, 'National radio station', NOW(), NOW()),
('Radio Tataouine', 'https://www.radiotataouine.tn/articles/rss', 'rss', true, 'Regional radio - Tataouine', NOW(), NOW()),
('Radio Gafsa', 'https://www.radiogafsa.tn/articles/rss', 'rss', true, 'Regional radio - Gafsa', NOW(), NOW()),
('Radio Kef', 'https://www.radiokef.tn/articles/rss', 'rss', true, 'Regional radio - Kef', NOW(), NOW()),
('RTCI', 'https://www.rtci.tn/articles/rss', 'rss', true, 'Regional radio station', NOW(), NOW()),
('Radio Monastir', 'https://www.radiomonastir.tn/articles/rss', 'rss', true, 'Regional radio - Monastir', NOW(), NOW()),
('Radio Jeunes', 'https://www.radiojeunes.tn/articles/rss', 'rss', true, 'Youth-focused radio station', NOW(), NOW()),
('Radio Nationale', 'https://www.radionationale.tn/articles/rss', 'rss', true, 'National radio station', NOW(), NOW()),
('Radio Sfax', 'https://www.radiosfax.tn/articles/rss', 'rss', true, 'Regional radio - Sfax', NOW(), NOW()),

-- Specialized Radio Feeds
('Mosaique FM', 'https://www.mosaiquefm.net/ar/rss', 'rss', true, 'Popular Tunisian radio station', NOW(), NOW()),
('Jawhara FM - General', 'https://www.jawharafm.net/ar/rss/showRss/88/1/1', 'rss', true, 'Jawhara FM general news', NOW(), NOW()),
('Jawhara FM - Politics', 'https://www.jawharafm.net/ar/rss/showRss/88/1/4', 'rss', true, 'Jawhara FM political news', NOW(), NOW()),
('Jawhara FM - Economy', 'https://www.jawharafm.net/ar/rss/showRss/88/1/2', 'rss', true, 'Jawhara FM economic news', NOW(), NOW())

ON CONFLICT (url) DO UPDATE SET
    name = EXCLUDED.name,
    is_active = EXCLUDED.is_active,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Verify the insertion
SELECT COUNT(*) as total_rss_sources FROM sources WHERE source_type = 'rss';
SELECT name, url FROM sources WHERE source_type = 'rss' ORDER BY name;
