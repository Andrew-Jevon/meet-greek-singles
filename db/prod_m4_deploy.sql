-- Production M4 rollout SQL — target database `chamo`
-- Combines: m4_migration.sql (platform_mode + email_auto copy) + SMTP config + prelaunch activation.

START TRANSACTION;

-- 1. platform_mode config row (skip if already exists — safe re-run)
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

-- Explicit: ensure prod lands in prelaunch regardless of previous state
UPDATE `config` SET `value` = 'prelaunch'
WHERE `module` = 'options' AND `option` = 'platform_mode';

-- 2. email_auto Meet Greek Singles voice (same content as staging)
UPDATE `email_auto`
SET `subject` = 'Welcome to Meet Greek Singles!',
    `header`  = 'Welcome home — kalos irthes!',
    `button`  = 'Complete your profile',
    `text`    = 'Hi {name},\r\n\r\nWelcome to Meet Greek Singles — a home for Greeks and friends of Greek culture who take meaningful relationships seriously.\r\n\r\nYour account is ready. To help other members find the kind of connection they are looking for, please take a couple of minutes to complete your profile: add a photo, write a short intro, and answer a few questions about your connection to Greece.\r\n\r\nWe are excited to have you with us.\r\n\r\nMeet Greek Singles'
WHERE `note` = 'join';

UPDATE `email_auto`
SET `subject` = 'Please confirm your email — Meet Greek Singles',
    `header`  = 'One more step',
    `button`  = 'Confirm my email',
    `text`    = 'Hi {name},\r\n\r\nThank you for joining Meet Greek Singles. To finish setting up your account, please confirm your email address by clicking the button below.\r\n\r\nIf you did not register on our site you can safely ignore this email.\r\n\r\nMeet Greek Singles'
WHERE `note` = 'confirm_email';

UPDATE `email_auto`
SET `subject` = 'You have a new message on Meet Greek Singles',
    `header`  = 'A member has reached out',
    `button`  = 'Read your message',
    `text`    = 'Hi {name},\r\n\r\nAnother member sent you a message. Log in to Meet Greek Singles to read it and reply when you are ready.\r\n\r\nMeet Greek Singles'
WHERE `note` = 'mail_message';

UPDATE `email_auto`
SET `subject` = 'Someone is interested in you on Meet Greek Singles',
    `header`  = 'You caught their eye',
    `button`  = 'See their profile',
    `text`    = 'Hi {name},\r\n\r\nAnother member showed interest in your profile. Have a look and, if you feel a connection, say hello.\r\n\r\nMeet Greek Singles'
WHERE `note` = 'interest';

UPDATE `email_auto`
SET `subject` = 'Reset your Meet Greek Singles password',
    `header`  = 'Reset your password',
    `button`  = 'Reset password',
    `text`    = 'Hi {name},\r\n\r\nWe received a request to reset your Meet Greek Singles password. Click the button below to choose a new one. The link will take you to a page on our site.\r\n\r\nIf you did not request this, you can safely ignore this email — your password will stay the same.\r\n\r\nMeet Greek Singles'
WHERE `note` = 'forget_link';

-- 3. SMTP config — Microsoft 365 via GoDaddy
UPDATE `config` SET `value` = 'Y'                            WHERE `module` = 'smtp' AND `option` = 'active';
UPDATE `config` SET `value` = 'smtp.office365.com'           WHERE `module` = 'smtp' AND `option` = 'server';
UPDATE `config` SET `value` = '587'                          WHERE `module` = 'smtp' AND `option` = 'port';
UPDATE `config` SET `value` = 'info@meetgreeksingles.com'    WHERE `module` = 'smtp' AND `option` = 'user';
UPDATE `config` SET `value` = 'Meetgreek631@'                WHERE `module` = 'smtp' AND `option` = 'password';
UPDATE `config` SET `value` = 'Meetgreek631@'                WHERE `module` = 'smtp' AND `option` = 'password2';

-- 4. Email verification enforcement (should already be Y but be explicit)
UPDATE `config` SET `value` = 'Y'
WHERE `module` = 'options' AND `option` = 'send_emails_only_to_confirmed_emails';

COMMIT;

-- Verify after apply:
--   SELECT module, `option`, value FROM config WHERE module='smtp' OR `option`='platform_mode';
