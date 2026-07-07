-- Staging-specific post-deploy tweaks.
-- Apply to database `slqih5q4r69_staging` AFTER m4_migration.sql.
-- Not intended for production — the SMTP config here is Meet Greek Singles' real
-- Microsoft 365 account and shouldn't be duplicated to prod unless verified.

START TRANSACTION;

-- 1. Point Chameleon SMTP at Microsoft 365 (Outlook.com / Office 365 via GoDaddy)
UPDATE `config` SET `value` = 'Y'                            WHERE `module` = 'smtp' AND `option` = 'active';
UPDATE `config` SET `value` = 'smtp.office365.com'           WHERE `module` = 'smtp' AND `option` = 'server';
UPDATE `config` SET `value` = '587'                          WHERE `module` = 'smtp' AND `option` = 'port';
UPDATE `config` SET `value` = 'info@meetgreeksingles.com'    WHERE `module` = 'smtp' AND `option` = 'user';
UPDATE `config` SET `value` = 'Meetgreek631@'                WHERE `module` = 'smtp' AND `option` = 'password';
UPDATE `config` SET `value` = 'Meetgreek631@'                WHERE `module` = 'smtp' AND `option` = 'password2';

-- 2. Start staging in prelaunch mode (explicit, matches the M4 migration default)
UPDATE `config` SET `value` = 'prelaunch'                    WHERE `module` = 'options' AND `option` = 'platform_mode';

-- 3. Turn on email verification on registration (Chameleon already had it enabled by default,
--    but make it explicit here)
UPDATE `config` SET `value` = 'Y'                            WHERE `module` = 'options' AND `option` = 'send_emails_only_to_confirmed_emails';

-- 4. Turn on the built-in captcha on registration (using securimage by default)
--    reCAPTCHA stays disabled until Irene provides Google keys.
-- (No captcha-on-join toggle exists as a single flag in Chameleon's config — captcha
--  rendering is driven by the join flow itself. Leaving this as a reminder comment.)

COMMIT;

-- Verify after apply:
--   SELECT module, option, value FROM config WHERE module = 'smtp';
--   SELECT module, option, value FROM config WHERE option = 'platform_mode';
