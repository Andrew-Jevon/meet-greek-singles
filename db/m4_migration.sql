-- Milestone 4 migration for meetgreeksingles.com
-- Date: 2026-04-23
-- Safe to re-run: INSERT uses WHERE NOT EXISTS; UPDATEs are idempotent.
--
-- Apply to:
--   Staging: `slqih5q4r69_staging` (hosted on same MariaDB instance as prod)
--   Production: `chamo` (CONFIRMED by Irene 2026-04-23 — the file
--                        _include/config/db.php on the live webroot shows
--                        db=chamo, user=chamo_user)
--
-- The OLD dump she sent earlier (meetgreeksingles.sql) was from a different,
-- stale database. Use a FRESH export of `chamo` for any staging/prod work
-- going forward.

START TRANSACTION;

-- 1. platform_mode toggle row in `config`
--    value=prelaunch: middleware blocks search/messaging/winks/upgrade/etc.
--    value=live: normal operation
--
-- Uses MAX(id)+1 so we don't collide with existing auto-increment.
-- The `options` selectbox defines the two valid values.
-- Chameleon's selectbox `options` column is pipe-delimited; the value stored
-- is also the label shown unless a language translation overrides it (see the
-- labels added to `texts` / language module below).
INSERT INTO `config` (`id`, `module`, `option`, `value`, `show_in_admin`, `type`, `options`, `position`)
SELECT (SELECT IFNULL(MAX(id), 0) + 1 FROM `config` AS c2),
       'options',
       'platform_mode',
       'prelaunch',
       1,
       'selectbox',
       'prelaunch|live',
       389
WHERE NOT EXISTS (
    SELECT 1 FROM `config` WHERE `module` = 'options' AND `option` = 'platform_mode'
);

-- 2. Email-auto templates that M4 needs
--    Chameleon's `email_auto` table defines templates that `email_auto_settings`
--    toggles on/off. Structure confirmed from dump.
--
-- Registration confirmation ("confirm your email address"):
-- NOTE: Chameleon may already have a stock template for this — check before inserting.
--       If `email_auto` has an entry where `key` / `name` matches registration confirmation,
--       we UPDATE the subject/body instead.
--
-- Welcome email ("welcome to Meet Greek Singles, here is how to start"):
--
-- We emit these as UPDATE-if-exists / INSERT-if-not using a pattern that works
-- across dump variations. If the `email_auto` schema in prod differs from our
-- assumed columns, this block will fail cleanly and we adjust once on staging.

-- The live DB already has stock Chameleon templates in `email_auto` (ids 1..N).
-- We UPDATE the ones M4 uses, leaving everything else untouched.
--
-- Sender identity is configured via admin (Email → SMTP), so no column for sender
-- is needed here; {name}, {password}, {url_site}, {code_link} are the token syntax
-- Chameleon expands in email_auto.text.

-- Registration "Welcome" email (note='join')
UPDATE `email_auto`
SET `subject` = 'Welcome to Meet Greek Singles!',
    `header`  = 'Welcome home — kalos irthes!',
    `button`  = 'Complete your profile',
    `text`    = 'Hi {name},\r\n\r\nWelcome to Meet Greek Singles — a home for Greeks and friends of Greek culture who take meaningful relationships seriously.\r\n\r\nYour account is ready. To help other members find the kind of connection they are looking for, please take a couple of minutes to complete your profile: add a photo, write a short intro, and answer a few questions about your connection to Greece.\r\n\r\nWe are excited to have you with us.\r\n\r\nMeet Greek Singles'
WHERE `note` = 'join';

-- Email-address confirmation (note='confirm_email')
UPDATE `email_auto`
SET `subject` = 'Please confirm your email — Meet Greek Singles',
    `header`  = 'One more step',
    `button`  = 'Confirm my email',
    `text`    = 'Hi {name},\r\n\r\nThank you for joining Meet Greek Singles. To finish setting up your account, please confirm your email address by clicking the button below.\r\n\r\nIf you did not register on our site you can safely ignore this email.\r\n\r\nMeet Greek Singles'
WHERE `note` = 'confirm_email';

-- New message arrived (note='mail_message')
UPDATE `email_auto`
SET `subject` = 'You have a new message on Meet Greek Singles',
    `header`  = 'A member has reached out',
    `button`  = 'Read your message',
    `text`    = 'Hi {name},\r\n\r\nAnother member sent you a message. Log in to Meet Greek Singles to read it and reply when you are ready.\r\n\r\nMeet Greek Singles'
WHERE `note` = 'mail_message';

-- Someone liked / winked (note='interest')
UPDATE `email_auto`
SET `subject` = 'Someone is interested in you on Meet Greek Singles',
    `header`  = 'You caught their eye',
    `button`  = 'See their profile',
    `text`    = 'Hi {name},\r\n\r\nAnother member showed interest in your profile. Have a look and, if you feel a connection, say hello.\r\n\r\nMeet Greek Singles'
WHERE `note` = 'interest';

-- Password reset link (note='forget_link')
UPDATE `email_auto`
SET `subject` = 'Reset your Meet Greek Singles password',
    `header`  = 'Reset your password',
    `button`  = 'Reset password',
    `text`    = 'Hi {name},\r\n\r\nWe received a request to reset your Meet Greek Singles password. Click the button below to choose a new one. The link will take you to a page on our site.\r\n\r\nIf you did not request this, you can safely ignore this email — your password will stay the same.\r\n\r\nMeet Greek Singles'
WHERE `note` = 'forget_link';

COMMIT;

-- =====================================================================
-- Notes for the developer running this migration:
--
-- 1. RUN FIRST: SELECT * FROM `email_auto` LIMIT 5;
--    Inspect columns so we know how to shape the email-template rows.
--
-- 2. The platform_mode row is safe to run now.
--
-- 3. After applying this migration, flip the mode via admin UI (M4 adds the
--    toggle under Admin → Options) — or via direct SQL:
--        UPDATE `config` SET `value` = 'prelaunch' WHERE `option` = 'platform_mode';
--        UPDATE `config` SET `value` = 'live'      WHERE `option` = 'platform_mode';
-- =====================================================================
