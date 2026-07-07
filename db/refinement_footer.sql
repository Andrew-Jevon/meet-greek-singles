-- Footer reorder per Irene 2026-04-25:
--   ABOUT | TERMS & CONDITIONS | PRIVACY POLICY | QUESTIONS & ANSWERS | CONTACT
-- Targets the English (default) lang rows on the bottom menu.

START TRANSACTION;

-- Set the 5 keepers in the right order
UPDATE pages SET position = 1, status = 1 WHERE id = 12;  -- About Meet Greek Singles
UPDATE pages SET position = 2, status = 1 WHERE id = 55;  -- Terms & Conditions
UPDATE pages SET position = 3, status = 1 WHERE id = 56;  -- Privacy Policy
UPDATE pages SET position = 4, status = 1 WHERE id = 57;  -- Questions & Answers
UPDATE pages SET position = 5, status = 1 WHERE id = 15;  -- Contact us

-- Disable items not in Irene's list (browse matches, edges variants, affiliates, photos/videos/people)
UPDATE pages SET status = 0 WHERE id IN (
    16,  -- menu_bottom_affiliates
    36,  -- menu_people_edge
    37,  -- menu_photos_edge
    38,  -- menu_videos_edge
    39,  -- menu_bottom_about_us (duplicate "edge" variant)
    40,  -- menu_terms_edge      (edge variant — we keep #55 instead)
    41,  -- menu_privacy_policy_edge (edge variant — we keep #56 instead)
    42,  -- menu_bottom_affiliates (duplicate)
    53   -- menu_bottom_search_results (Browse matches — out of guest scope in pre-launch anyway)
);

COMMIT;

-- Verify:
--   SELECT id, menu_title, title, section, position, status FROM pages WHERE section='bottom' AND status=1 ORDER BY position;
