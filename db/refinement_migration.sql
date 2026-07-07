-- Refinement phase migration — staging first, production after Irene's sign-off.
-- Adds:
--   1. `public_visible` flag on help_topic so admin can mark which Q&A topics show to guests.
--   2. `position` column on help_topic so admin-defined order replaces id-ASC fallback.
--
-- Safe to re-run: uses information_schema guard.

START TRANSACTION;

-- 1. help_topic.public_visible
SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name   = 'help_topic'
      AND column_name  = 'public_visible'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE `help_topic` ADD COLUMN `public_visible` TINYINT(1) NOT NULL DEFAULT 0 AFTER `name`',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2. help_topic.position
SET @col_exists := (
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name   = 'help_topic'
      AND column_name  = 'position'
);
SET @sql := IF(@col_exists = 0,
    'ALTER TABLE `help_topic` ADD COLUMN `position` INT NOT NULL DEFAULT 0 AFTER `public_visible`',
    'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 3. Seed position from id so existing topics keep current order
UPDATE `help_topic` SET `position` = `id` WHERE `position` = 0;

-- 4. Enable the help feature (needed for /help.php to render).
--    If the row doesn't exist (some installs skip it), insert it.
INSERT INTO `config` (`module`, `option`, `value`, `show_in_admin`, `type`, `position`)
SELECT 'options', 'help', 'Y', 1, 'checkbox', 400
WHERE NOT EXISTS (SELECT 1 FROM `config` WHERE `module` = 'options' AND `option` = 'help');

UPDATE `config` SET `value` = 'Y'
WHERE `module` = 'options' AND `option` = 'help';

-- 5. Seed 4 sample public Q&A topics so Irene can see the public-vs-member split working.
--    She can rename / replace these from Admin → Help → Topics.
SET @lang := COALESCE(
    (SELECT `value` FROM `config` WHERE `module` = 'main' AND `option` = 'lang_loaded' LIMIT 1),
    'default'
);

INSERT INTO `help_topic` (`name`, `public_visible`, `position`, `lang`)
SELECT 'How is Meet Greek Singles different from other dating sites?', 1, 10, @lang
WHERE NOT EXISTS (SELECT 1 FROM `help_topic` WHERE `name` LIKE 'How is Meet Greek Singles%');

INSERT INTO `help_topic` (`name`, `public_visible`, `position`, `lang`)
SELECT 'Is the platform open to non-Greeks?', 1, 20, @lang
WHERE NOT EXISTS (SELECT 1 FROM `help_topic` WHERE `name` LIKE 'Is the platform open to non-Greeks%');

INSERT INTO `help_topic` (`name`, `public_visible`, `position`, `lang`)
SELECT 'How do you keep the community safe and respectful?', 1, 30, @lang
WHERE NOT EXISTS (SELECT 1 FROM `help_topic` WHERE `name` LIKE 'How do you keep the community safe%');

INSERT INTO `help_topic` (`name`, `public_visible`, `position`, `lang`)
SELECT 'What is included in a free account?', 1, 40, @lang
WHERE NOT EXISTS (SELECT 1 FROM `help_topic` WHERE `name` LIKE 'What is included in a free account%');

-- 4. Footer extras — currently hardcoded in _footer.html, lift into pages table
-- COMMENTED OUT: awaits Irene's confirmation on order + visibility.
-- Once approved, replace the hardcoded <li>s in _footer.html with the standard
-- bottom_visitor_menu loop (already present), and these rows render automatically.
--
-- INSERT INTO `pages` (`alias`, `place`, `title`, `url`, `position`, `visibility`)
-- SELECT 'menu_bottom_events', 'bottom', 'Events', '/events.php', 90, 'all'
-- WHERE NOT EXISTS (SELECT 1 FROM `pages` WHERE `alias` = 'menu_bottom_events');
--
-- INSERT INTO `pages` (`alias`, `place`, `title`, `url`, `position`, `visibility`)
-- SELECT 'menu_bottom_community', 'bottom', 'Community Ambassadors', '/community', 95, 'all'
-- WHERE NOT EXISTS (SELECT 1 FROM `pages` WHERE `alias` = 'menu_bottom_community');

COMMIT;

-- Verify:
--   DESCRIBE help_topic;
--   SELECT id, name, public_visible, position FROM help_topic ORDER BY position, id;
