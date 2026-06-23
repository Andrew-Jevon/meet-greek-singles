/**
 * MGS custom UI translations — supplements Chameleon's lang layer for
 * hardcoded English copy in impact theme templates (nav, homepage hero, etc.).
 * Driven by window.MGS_LANG set in _header.html from {lang_loaded}.
 */
(function (global) {
    'use strict';

    var STRINGS = {
        nav_home: { default: 'Home', greek: 'Αρχική' },
        nav_about: { default: 'About Us', greek: 'Σχετικά' },
        nav_search: { default: 'Search', greek: 'Αναζήτηση' },
        nav_events: { default: 'Events', greek: 'Εκδηλώσεις' },
        nav_advice: { default: 'Advice', greek: 'Συμβουλές' },
        nav_upgrade: { default: 'Upgrade', greek: 'Αναβάθμιση' },
        nav_contact: { default: 'Contact', greek: 'Επικοινωνία' },
        nav_tagline: { default: 'Where Greek Hearts Meet', greek: 'Όπου συναντιούνται Ελληνικές καρδιές' },
        btn_login: { default: 'Log In', greek: 'Σύνδεση' },
        btn_join: { default: 'Join Now', greek: 'Εγγραφή' },
        hero_title: { default: 'Where Greek Hearts Meet', greek: 'Όπου συναντιούνται Ελληνικές καρδιές' },
        hero_emotional: {
            default: 'Find your Greek connection and build meaningful relationships based on shared heritage, values, and culture.',
            greek: 'Βρείτε τη δική σας Ελληνική σύνδεση και χτίστε ουσιαστικές σχέσεις με βάση την κοινή κληρονομιά, τις αξίες και τον πολιτισμό.'
        },
        hero_cta: { default: 'Join Now – It\u2019s Free \u203a', greek: 'Εγγραφή – Δωρεάν \u203a' },
        hero_trust: {
            default: 'Private, secure, and built for meaningful connections.',
            greek: 'Ιδιωτικό, ασφαλές και φτιαγμένο για ουσιαστικές συνδέσεις.'
        },
        features_heading: { default: 'Find Your Greek Connection', greek: 'Βρείτε τη δική σας Ελληνική σύνδεση' },
        features_tagline: {
            default: 'Because the right connection can change everything.',
            greek: 'Γιατί η σωστή σύνδεση μπορεί να αλλάξει τα πάντα.'
        },
        feature1_title: { default: 'Meaningful Connections', greek: 'Ουσιαστικές Συνδέσεις' },
        feature1_body: {
            default: 'We bring together Greek singles who are looking for authentic, long-term relationships.',
            greek: 'Φέρνουμε κοντά Έλληνες singles που αναζητούν αυθεντικές, μακροχρόνιες σχέσεις.'
        },
        feature2_title: { default: 'Built on Shared Values', greek: 'Βασισμένο σε κοινές αξίες' },
        feature2_body: {
            default: 'Faith, family, culture and tradition are at the heart of our community.',
            greek: 'Η πίστη, η οικογένεια, ο πολιτισμός και η παράδοση είναι στην καρδιά της κοινότητάς μας.'
        },
        feature3_title: { default: 'Safe & Private', greek: 'Ασφαλές & Ιδιωτικό' },
        feature3_body: {
            default: 'Your privacy and security are our top priority.',
            greek: 'Η ιδιωτικότητα και η ασφάλειά σας είναι η πρώτη μας προτεραιότητα.'
        },
        feature4_title: { default: 'Worldwide Community', greek: 'Παγκόσμια κοινότητα' },
        feature4_body: {
            default: 'Connect with Greek singles across Greece and around the world.',
            greek: 'Συνδεθείτε με Έλληνες singles σε όλη την Ελλάδα και τον κόσμο.'
        },
        early_title: { default: 'Join Early. Connect Sooner.', greek: 'Εγγραφείτε νωρίς. Συνδεθείτε νωρίτερα.' },
        early_sub: { default: 'Sign up now to be ready when we launch.', greek: 'Εγγραφείτε τώρα για να είστε έτοιμοι όταν ξεκινήσουμε.' },
        early_item1: { default: 'Create your profile before launch', greek: 'Δημιουργήστε το προφίλ σας πριν την έναρξη' },
        early_item2: { default: 'Be the first to know when we go live', greek: 'Μάθετε πρώτοι όταν ξεκινήσουμε' },
        early_item3: { default: 'Get updates on news, events & early access', greek: 'Λάβετε ενημερώσεις για νέα, εκδηλώσεις & πρώιμη πρόσβαση' },
        early_item4: { default: 'Increase your visibility from day one', greek: 'Αυξήστε την ορατότητά σας από την πρώτη μέρα' },
        early_btn: { default: 'Join Now – It\u2019s Free \u203a', greek: 'Εγγραφή – Δωρεάν \u203a' },
        prelaunch_strip: {
            default: 'Registration is now open &mdash; create your <strong class="mgs_prelaunch_free">FREE</strong> account and be among the first to join Meet Greek Singles.',
            greek: 'Η εγγραφή είναι ανοιχτή &mdash; δημιουργήστε <strong class="mgs_prelaunch_free">ΔΩΡΕΑΝ</strong> λογαριασμό και γίνετε από τους πρώτους στο Meet Greek Singles.'
        }
    };

    function detectLang() {
        var meta = document.querySelector('meta[name="mgs-lang"]');
        if (meta && meta.content === 'greek') return 'greek';

        try {
            if (sessionStorage.getItem('mgs_lang') === 'greek') return 'greek';
        } catch (e) {}

        var qs = global.location && global.location.search ? global.location.search : '';
        if (qs.indexOf('set_language=greek') !== -1) return 'greek';
        if (qs.indexOf('set_language=default') !== -1) return 'default';

        var lang = (global.MGS_LANG || 'default').toLowerCase();
        return lang === 'greek' ? 'greek' : 'default';
    }

    function currentLang() {
        return detectLang();
    }

    function t(key) {
        var pack = STRINGS[key];
        if (!pack) return null;
        var lang = currentLang();
        return pack[lang] || pack.default || null;
    }

    function apply() {
        var lang = currentLang();
        global.MGS_LANG = lang === 'greek' ? 'greek' : 'default';
        try {
            if (lang === 'greek') sessionStorage.setItem('mgs_lang', 'greek');
            else sessionStorage.removeItem('mgs_lang');
        } catch (e) {}
        document.documentElement.setAttribute('lang', lang === 'greek' ? 'el' : 'en');
        document.documentElement.classList.toggle('mgs-lang-greek', lang === 'greek');
        document.documentElement.classList.toggle('mgs-lang-english', lang !== 'greek');
        if (document.body) {
            document.body.classList.toggle('mgs-lang-greek', lang === 'greek');
            document.body.classList.toggle('mgs-lang-english', lang !== 'greek');
        }

        document.querySelectorAll('[data-mgs-i18n]').forEach(function (el) {
            var key = el.getAttribute('data-mgs-i18n');
            var text = t(key);
            if (text !== null) el.textContent = text;
        });

        document.querySelectorAll('[data-mgs-i18n-html]').forEach(function (el) {
            var key = el.getAttribute('data-mgs-i18n-html');
            var text = t(key);
            if (text !== null) el.innerHTML = text;
        });

        var enBtn = document.querySelector('.mgs_lang_en');
        var grBtn = document.querySelector('.mgs_lang_gr');
        if (enBtn && grBtn) {
            enBtn.classList.toggle('mgs_lang_active', lang === 'default');
            grBtn.classList.toggle('mgs_lang_active', lang === 'greek');
        }
    }

    global.MgsI18n = { apply: apply, t: t, lang: currentLang };

    function wrapSiteSetLanguage() {
        var orig = global.siteSetLanguage;
        global.siteSetLanguage = function (lang) {
            global.MGS_LANG = lang;
            try {
                if (lang === 'greek') sessionStorage.setItem('mgs_lang', 'greek');
                else sessionStorage.removeItem('mgs_lang');
            } catch (e) {}
            apply();
            if (typeof global.MGS_TranslateNow === 'function') global.MGS_TranslateNow();
            if (typeof orig === 'function') return orig(lang);
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            apply();
            wrapSiteSetLanguage();
        });
    } else {
        apply();
        wrapSiteSetLanguage();
    }
})(window);
