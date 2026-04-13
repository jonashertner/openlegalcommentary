export const LANGS = ['de', 'fr', 'it', 'en'] as const;
export type Lang = (typeof LANGS)[number];

const translations: Record<string, Record<Lang, string>> = {
  // Nav
  'nav.laws': { de: 'Gesetze', fr: 'Lois', it: 'Leggi', en: 'Laws' },
  'nav.support': { de: 'Unterstützen', fr: 'Soutenir', it: 'Sostenere', en: 'Support' },
  'nav.about': { de: 'Über uns', fr: 'À propos', it: 'Chi siamo', en: 'About' },
  'nav.changelog': { de: 'Änderungen', fr: 'Modifications', it: 'Modifiche', en: 'Changelog' },
  'nav.methodology': { de: 'Methodik', fr: 'Méthodologie', it: 'Metodologia', en: 'Methodology' },

  // Breadcrumb
  'breadcrumb.home': { de: 'Startseite', fr: 'Accueil', it: 'Home', en: 'Home' },

  // Article tabs
  'tab.summary': { de: 'Übersicht', fr: 'Aperçu', it: 'Panoramica', en: 'Overview' },
  'tab.doctrine': { de: 'Doktrin', fr: 'Doctrine', it: 'Dottrina', en: 'Doctrine' },
  'tab.caselaw': { de: 'Rechtsprechung', fr: 'Jurisprudence', it: 'Giurisprudenza', en: 'Case Law' },

  // Article page
  'article.in_force_since': { de: 'In Kraft seit', fr: 'En vigueur depuis', it: 'In vigore dal', en: 'In force since' },
  'article.toc': { de: 'Inhaltsverzeichnis', fr: 'Table des matières', it: 'Indice', en: 'Table of Contents' },
  'article.back_to_top': { de: 'Nach oben', fr: 'Haut de page', it: 'Torna su', en: 'Back to top' },
  'article.last_updated': { de: 'Letzte Aktualisierung', fr: 'Dernière mise à jour', it: 'Ultimo aggiornamento', en: 'Last updated' },

  // Pagination
  'pagination.prev': { de: 'Vorheriger Artikel', fr: 'Article précédent', it: 'Articolo precedente', en: 'Previous article' },
  'pagination.next': { de: 'Nächster Artikel', fr: 'Article suivant', it: 'Articolo successivo', en: 'Next article' },

  // Footer
  'footer.commentary': { de: 'Kommentar', fr: 'Commentaire', it: 'Commento', en: 'Commentary' },
  'footer.project': { de: 'Projekt', fr: 'Projet', it: 'Progetto', en: 'Project' },
  'footer.license': { de: 'Lizenz', fr: 'Licence', it: 'Licenza', en: 'License' },
  'footer.all_laws': { de: 'Alle Gesetze', fr: 'Toutes les lois', it: 'Tutte le leggi', en: 'All Laws' },
  'footer.about': { de: 'Über uns', fr: 'À propos', it: 'Chi siamo', en: 'About' },
  'footer.changes': { de: 'Änderungen', fr: 'Modifications', it: 'Modifiche', en: 'Changelog' },
  'footer.content_license': { de: 'Inhalte: CC BY-SA 4.0', fr: 'Contenu : CC BY-SA 4.0', it: 'Contenuti: CC BY-SA 4.0', en: 'Content: CC BY-SA 4.0' },
  'footer.code_license': { de: 'Code: MIT', fr: 'Code : MIT', it: 'Codice: MIT', en: 'Code: MIT' },
  'footer.tagline': {
    de: 'Offener, KI-generierter Kommentar zum Schweizer Bundesrecht.',
    fr: 'Commentaire ouvert généré par IA sur le droit fédéral suisse.',
    it: "Commento aperto generato dall'IA sul diritto federale svizzero.",
    en: 'Open, AI-generated commentary on Swiss federal law.',
  },

  // Home page
  'home.eyebrow': { de: 'Schweizer Bundesrecht', fr: 'Droit fédéral suisse', it: 'Diritto federale svizzero', en: 'Swiss Federal Law' },
  'home.title': { de: 'Open Legal Commentary', fr: 'Open Legal Commentary', it: 'Open Legal Commentary', en: 'Open Legal Commentary' },
  'home.subtitle': {
    de: 'Offener, KI-generierter, täglich aktualisierter Kommentar zum Schweizer Bundesrecht.',
    fr: 'Commentaire ouvert, généré par IA, mis à jour quotidiennement sur le droit fédéral suisse.',
    it: "Commento aperto, generato dall'IA, aggiornato quotidianamente sul diritto federale svizzero.",
    en: 'Open, AI-generated, daily-updated commentary on Swiss federal law.',
  },
  'home.stat.laws': { de: 'Gesetze', fr: 'Lois', it: 'Leggi', en: 'Laws' },
  'home.stat.articles': { de: 'Artikel', fr: 'Articles', it: 'Articoli', en: 'Articles' },
  'home.stat.layers': { de: 'Ebenen', fr: 'Niveaux', it: 'Livelli', en: 'Layers' },
  'home.stat.decisions': { de: 'Entscheide', fr: 'Décisions', it: 'Decisioni', en: 'Decisions' },
  'home.stat.languages': { de: 'Sprachen', fr: 'Langues', it: 'Lingue', en: 'Languages' },
  'home.stat.updated': { de: 'Täglich aktualisiert', fr: 'Mise à jour quotidienne', it: 'Aggiornamento quotidiano', en: 'Updated daily' },
  'home.laws_heading': { de: 'Kommentierte Gesetze', fr: 'Lois commentées', it: 'Leggi commentate', en: 'Annotated Laws' },
  'home.layers_heading': { de: 'Drei Ebenen der Analyse', fr: "Trois niveaux d'analyse", it: 'Tre livelli di analisi', en: 'Three Layers of Analysis' },
  'home.layer1.title': { de: 'Übersicht', fr: 'Aperçu', it: 'Panoramica', en: 'Overview' },
  'home.layer1.desc': {
    de: 'Verständliche Zusammenfassung auf B1-Niveau. Was regelt der Artikel? Wer ist betroffen?',
    fr: "Résumé accessible au niveau B1. Que règle l'article ? Qui est concerné ?",
    it: "Riassunto comprensibile a livello B1. Cosa regola l'articolo? Chi è interessato?",
    en: 'Accessible summary at B1 level. What does the article regulate? Who is affected?',
  },
  'home.layer2.title': { de: 'Doktrin', fr: 'Doctrine', it: 'Dottrina', en: 'Doctrine' },
  'home.layer2.desc': {
    de: 'Akademische Analyse mit Randziffern, Streitständen und Literaturverweisen.',
    fr: 'Analyse académique avec numéros marginaux, controverses et références bibliographiques.',
    it: 'Analisi accademica con numeri marginali, controversie e riferimenti bibliografici.',
    en: 'Academic analysis with marginal numbers, doctrinal debates, and literature references.',
  },
  'home.layer3.title': { de: 'Rechtsprechung', fr: 'Jurisprudence', it: 'Giurisprudenza', en: 'Case Law' },
  'home.layer3.desc': {
    de: 'Leitentscheide des Bundesgerichts, thematisch geordnet und täglich aktualisiert.',
    fr: "Arrêts de principe du Tribunal fédéral, classés par thème et mis à jour quotidiennement.",
    it: 'Sentenze principali del Tribunale federale, ordinate per tema e aggiornate quotidianamente.',
    en: 'Leading Federal Supreme Court decisions, organized by topic and updated daily.',
  },
  'home.cantons_heading': { de: 'Kantonsverfassungen', fr: 'Constitutions cantonales', it: 'Costituzioni cantonali', en: 'Cantonal Constitutions' },
  'home.cantons_subtitle': { de: '26 Kantone', fr: '26 cantons', it: '26 cantoni', en: '26 cantons' },
  'home.open_heading': { de: 'Offen und frei', fr: 'Ouvert et libre', it: 'Aperto e libero', en: 'Open and Free' },
  'home.open_desc': {
    de: 'Alle Inhalte stehen unter CC BY-SA 4.0. Der Code ist MIT-lizenziert. Beitragen auf GitHub.',
    fr: 'Tout le contenu est sous CC BY-SA 4.0. Le code est sous licence MIT. Contribuez sur GitHub.',
    it: 'Tutti i contenuti sono sotto CC BY-SA 4.0. Il codice è sotto licenza MIT. Contribuisci su GitHub.',
    en: 'All content is CC BY-SA 4.0. Code is MIT licensed. Contribute on GitHub.',
  },

  // Law page
  'law.progress': { de: 'Fortschritt', fr: 'Progression', it: 'Progresso', en: 'Progress' },
  'law.articles_with_commentary': { de: 'Artikel mit Kommentar', fr: 'Articles commentés', it: 'Articoli commentati', en: 'Articles with commentary' },
  'law.coming_soon': { de: 'In Vorbereitung', fr: 'En préparation', it: 'In preparazione', en: 'Coming soon' },
  'law.explore': { de: 'Kommentar lesen', fr: 'Lire le commentaire', it: 'Leggi il commento', en: 'Read commentary' },
  'law.featured': { de: 'Jetzt verfügbar', fr: 'Disponible maintenant', it: 'Disponibile ora', en: 'Available now' },
  'law.forthcoming': { de: 'Weitere Gesetze', fr: 'Autres lois', it: 'Altre leggi', en: 'More laws' },
  'law.forthcoming_desc': { de: 'In Vorbereitung — demnächst verfügbar', fr: 'En préparation — bientôt disponible', it: 'In preparazione — presto disponibile', en: 'In preparation — coming soon' },
  'law.titel': { de: 'Titel', fr: 'Titre', it: 'Titolo', en: 'Title' },
  'law.kapitel': { de: 'Kapitel', fr: 'Chapitre', it: 'Capitolo', en: 'Chapter' },
  'law.abschnitt': { de: 'Abschnitt', fr: 'Section', it: 'Sezione', en: 'Section' },
  'law.commented': { de: 'Kommentiert', fr: 'Commenté', it: 'Commentato', en: 'Commented' },

  // Search
  'search.placeholder': { de: 'Artikel, Zitate oder Rechtsbegriffe suchen...', fr: 'Rechercher des articles, citations ou concepts juridiques...', it: 'Cerca articoli, citazioni o concetti giuridici...', en: 'Search articles, citations, or legal concepts...' },
  'search.no_results': { de: 'Keine Ergebnisse', fr: 'Aucun résultat', it: 'Nessun risultato', en: 'No results' },
  'search.dev_unavailable': { de: 'Suche nach Build verfügbar', fr: 'Recherche disponible après build', it: 'Ricerca disponibile dopo build', en: 'Search available after build' },

  // Gesetzestext
  'gesetzestext.label': { de: 'Gesetzestext', fr: 'Texte de loi', it: 'Testo di legge', en: 'Statute Text' },

  // Changelog
  'changelog.title': { de: 'Änderungen', fr: 'Modifications', it: 'Modifiche', en: 'Changelog' },
  'changelog.empty': { de: 'Noch keine Änderungen vorhanden.', fr: 'Aucune modification pour le moment.', it: 'Nessuna modifica al momento.', en: 'No changes yet.' },

  // About
  'about.title': { de: 'Über Open Legal Commentary', fr: "À propos d'Open Legal Commentary", it: 'Informazioni su Open Legal Commentary', en: 'About Open Legal Commentary' },

  // Meta
  'meta.description': {
    de: 'Offener, KI-generierter Kommentar zum Schweizer Bundesrecht. Täglich aktualisiert.',
    fr: 'Commentaire ouvert généré par IA sur le droit fédéral suisse. Mis à jour quotidiennement.',
    it: "Commento aperto generato dall'IA sul diritto federale svizzero. Aggiornato quotidianamente.",
    en: 'Open, AI-generated commentary on Swiss federal law. Updated daily.',
  },

  // Header aria
  'header.nav_label': { de: 'Hauptnavigation', fr: 'Navigation principale', it: 'Navigazione principale', en: 'Main navigation' },
  'header.menu_open': { de: 'Menü öffnen', fr: 'Ouvrir le menu', it: 'Apri menu', en: 'Open menu' },
  'header.theme_toggle': { de: 'Farbschema wechseln', fr: 'Changer le thème', it: 'Cambia tema', en: 'Toggle theme' },
  'header.search': { de: 'Suche', fr: 'Recherche', it: 'Ricerca', en: 'Search' },
  'header.beta_notice': {
    de: 'openlegalcommentary befindet sich in aktiver Entwicklung.',
    fr: 'openlegalcommentary est en développement actif.',
    it: 'openlegalcommentary è in sviluppo attivo.',
    en: 'openlegalcommentary is in active development.',
  },

  // Beta first-visit overlay
  'overlay.tag': {
    de: 'BETA · IN ENTWICKLUNG',
    fr: 'BÊTA · EN DÉVELOPPEMENT',
    it: 'BETA · IN SVILUPPO',
    en: 'BETA · IN DEVELOPMENT',
  },
  'overlay.title': {
    de: 'Willkommen bei openlegalcommentary',
    fr: 'Bienvenue sur openlegalcommentary',
    it: 'Benvenuti su openlegalcommentary',
    en: 'Welcome to openlegalcommentary',
  },
  'overlay.body1': {
    de: 'Dies ist eine öffentliche Pilotversion. Die Plattform befindet sich in aktiver Entwicklung — Inhalte, Funktionen und Abdeckung ändern sich laufend.',
    fr: 'Ceci est une version pilote publique. La plateforme est en développement actif — contenus, fonctionnalités et couverture évoluent en permanence.',
    it: 'Questa è una versione pilota pubblica. La piattaforma è in sviluppo attivo — contenuti, funzionalità e copertura cambiano continuamente.',
    en: 'This is a public pilot version. The platform is in active development — content, features, and coverage are changing continuously.',
  },
  'overlay.body2': {
    de: 'Die Kommentare werden von KI-Modellen aus öffentlichen Rechtsquellen generiert und automatisch auf Qualität geprüft. Inhalte können Fehler enthalten und sind gegen die Primärquellen zu prüfen.',
    fr: "Les commentaires sont générés par des modèles d'IA à partir de sources juridiques publiques et évalués automatiquement. Les contenus peuvent contenir des erreurs et sont à vérifier contre les sources primaires.",
    it: 'I commenti sono generati da modelli di IA a partire da fonti giuridiche pubbliche e valutati automaticamente. I contenuti possono contenere errori e vanno verificati rispetto alle fonti primarie.',
    en: 'Commentaries are generated by AI models from public legal sources and automatically quality-checked. Content may contain errors and should be verified against primary sources.',
  },
  'overlay.body3': {
    de: 'Feedback ist willkommen.',
    fr: 'Vos commentaires sont les bienvenus.',
    it: 'I vostri commenti sono benvenuti.',
    en: 'Feedback is welcome.',
  },
  'overlay.button': {
    de: 'Verstanden',
    fr: 'Compris',
    it: 'Ho capito',
    en: 'Got it',
  },

  // Support / fundraising page
  'support.title': { de: 'Unterstützen', fr: 'Soutenir', it: 'Sostenere', en: 'Support' },
  'support.meta': {
    de: 'Unterstützen Sie den ersten offenen Rechtskommentar der Schweiz.',
    fr: "Soutenez le premier commentaire juridique ouvert de Suisse.",
    it: 'Sostenete il primo commento giuridico aperto della Svizzera.',
    en: "Support Switzerland's first open legal commentary.",
  },
  'support.tag': {
    de: 'OFFENER RECHTSKOMMENTAR',
    fr: 'COMMENTAIRE JURIDIQUE OUVERT',
    it: 'COMMENTO GIURIDICO APERTO',
    en: 'OPEN LEGAL COMMENTARY',
  },
  'support.headline': {
    de: 'openlegalcommentary unterstützen',
    fr: 'Soutenir openlegalcommentary',
    it: 'Sostenere openlegalcommentary',
    en: 'Support openlegalcommentary',
  },
  'support.lead': {
    de: 'Offener, KI-generierter Rechtskommentar zum Schweizer Bundesrecht. 9 Gesetze, 4 Sprachen, täglich aktualisiert. Frei zugänglich unter CC BY-SA 4.0, finanziert durch individuelle Spenden.',
    fr: "Commentaire juridique ouvert et généré par IA sur le droit fédéral suisse. 9 lois, 4 langues, mis à jour quotidiennement. Librement accessible sous CC BY-SA 4.0, financé par des dons individuels.",
    it: "Commento giuridico aperto e generato dall'IA sul diritto federale svizzero. 9 leggi, 4 lingue, aggiornamento quotidiano. Liberamente accessibile sotto CC BY-SA 4.0, finanziato da donazioni individuali.",
    en: 'Open, AI-generated legal commentary on Swiss federal law. 9 laws, 4 languages, updated daily. Freely accessible under CC BY-SA 4.0, funded by individual donations.',
  },

  // Pipeline
  'support.pipeline_title': { de: 'Wie ein Artikel entsteht', fr: "Comment naît un article", it: 'Come nasce un articolo', en: 'How an article is made' },
  'support.step1_label': { de: 'Recherche', fr: 'Recherche', it: 'Ricerca', en: 'Research' },
  'support.step1_desc': {
    de: 'Leitentscheide und Doktrin aus 930\'000+ Bundesgerichtsentscheiden (opencaselaw.ch), Gesetzesmaterialien (Botschaften, Erläuterungsberichte, Protokolle) und Kommentarliteratur.',
    fr: "Arrêts de principe et doctrine parmi 930'000+ décisions du Tribunal fédéral (opencaselaw.ch), matériaux législatifs (messages, rapports explicatifs, procès-verbaux) et littérature de commentaire.",
    it: "Sentenze di principio e dottrina tra 930'000+ decisioni del Tribunale federale (opencaselaw.ch), materiali legislativi (messaggi, rapporti esplicativi, verbali) e letteratura di commento.",
    en: 'Leading cases and doctrine from 930,000+ Federal Supreme Court decisions (opencaselaw.ch), legislative materials (Federal Council messages, explanatory reports, debate records), and commentary literature.',
  },
  'support.step2_label': { de: 'Generierung', fr: 'Génération', it: 'Generazione', en: 'Generation' },
  'support.step2_desc': {
    de: 'Ein spezialisierter KI-Agent (Claude Sonnet 4.6) schreibt die doktrinale Analyse nach strikten Vorgaben: sechs Pflichtsektionen, Randziffern, Quellenpflicht, Konzisionsdisziplin.',
    fr: "Un agent IA spécialisé (Claude Sonnet 4.6) rédige l'analyse doctrinale selon des exigences strictes : six sections obligatoires, numéros marginaux, obligation de sources, discipline de concision.",
    it: "Un agente IA specializzato (Claude Sonnet 4.6) redige l'analisi dottrinale secondo requisiti rigorosi: sei sezioni obbligatorie, numeri marginali, obbligo di fonti, disciplina di concisione.",
    en: 'A specialized AI agent (Claude Sonnet 4.6) writes the doctrinal analysis under strict requirements: six mandatory sections, marginal numbers, source obligations, conciseness discipline.',
  },
  'support.step3_label': { de: 'Prüfung', fr: 'Évaluation', it: 'Valutazione', en: 'Evaluation' },
  'support.step3_desc': {
    de: 'Ein unabhängiges KI-Modell (Claude Opus 4.6) prüft gegen zehn Qualitätskriterien. Bei Nichtbestehen: automatische Wiederholung bis zu drei Mal.',
    fr: "Un modèle IA indépendant (Claude Opus 4.6) évalue selon dix critères de qualité. En cas d'échec : répétition automatique jusqu'à trois fois.",
    it: 'Un modello IA indipendente (Claude Opus 4.6) valuta secondo dieci criteri di qualità. In caso di esito negativo: ripetizione automatica fino a tre volte.',
    en: 'An independent AI model (Claude Opus 4.6) evaluates against ten quality criteria. On failure: automatic retry up to three times.',
  },
  'support.step4_label': { de: 'Übersetzung', fr: 'Traduction', it: 'Traduzione', en: 'Translation' },
  'support.step4_desc': {
    de: 'Übersetzung in Französisch, Italienisch und Englisch.',
    fr: 'Traduction en français, italien et anglais.',
    it: 'Traduzione in francese, italiano e inglese.',
    en: 'Translation into French, Italian, and English.',
  },

  // Prompt
  'support.prompt_title': { de: 'Der Prompt', fr: 'Le prompt', it: 'Il prompt', en: 'The prompt' },
  'support.prompt_intro': {
    de: 'Dies ist ein Auszug aus dem tatsächlichen Prompt, der jede Doktrin-Generierung steuert:',
    fr: "Voici un extrait du prompt réel qui guide chaque génération doctrinale :",
    it: 'Questo è un estratto dal prompt reale che guida ogni generazione dottrinale:',
    en: 'This is an excerpt from the actual prompt that governs every doctrine generation:',
  },

  // Example
  'support.example_title': { de: 'Ergebnis', fr: 'Résultat', it: 'Risultato', en: 'Result' },
  'support.example_intro': {
    de: 'Art. 8 BV (Rechtsgleichheit) — generiert mit Botschaft, Erläuterungsbericht und Protokollen aus National- und Ständerat:',
    fr: 'Art. 8 Cst. (Égalité) — généré avec le message, le rapport explicatif et les procès-verbaux du Conseil national et du Conseil des États :',
    it: 'Art. 8 Cost. (Uguaglianza) — generato con il messaggio, il rapporto esplicativo e i verbali del Consiglio nazionale e del Consiglio degli Stati:',
    en: 'Art. 8 FC (Equality) — generated with the Federal Council message, explanatory report, and National Council and Council of States debate records:',
  },
  'support.example_cta': {
    de: 'Art. 8 BV — Doktrin ansehen',
    fr: 'Art. 8 Cst. — Voir la doctrine',
    it: 'Art. 8 Cost. — Vedere la dottrina',
    en: 'Art. 8 FC — View doctrine',
  },

  // Cost
  'support.cost_title': { de: 'Kosten', fr: 'Coûts', it: 'Costi', en: 'Cost' },
  'support.cost_intro': {
    de: 'Ein Artikel kostet CHF 6 — aufgeschlüsselt:',
    fr: 'Un article coûte CHF 6 — détaillé :',
    it: 'Un articolo costa CHF 6 — in dettaglio:',
    en: 'One article costs CHF 6 — broken down:',
  },
  'support.cost_gen': { de: 'Generierung', fr: 'Génération', it: 'Generazione', en: 'Generation' },
  'support.cost_eval': { de: 'Qualitätsprüfung', fr: 'Contrôle qualité', it: 'Controllo qualità', en: 'Quality check' },
  'support.cost_trans': { de: 'Übersetzung (3 Sprachen)', fr: 'Traduction (3 langues)', it: 'Traduzione (3 lingue)', en: 'Translation (3 languages)' },
  'support.cost_mat': { de: 'Materialien', fr: 'Matériaux', it: 'Materiali', en: 'Materials' },
  'support.cost_retry': { de: 'Wiederholungen', fr: 'Itérations', it: 'Iterazioni', en: 'Retries' },
  'support.cost_reserve': { de: 'Reserve', fr: 'Réserve', it: 'Riserva', en: 'Reserve' },
  'support.cost_note': {
    de: 'Schätzungen auf Grundlage aktueller API-Preise. Können sich ändern.',
    fr: "Estimations basées sur les prix API actuels. Susceptibles de changer.",
    it: 'Stime basate sui prezzi API attuali. Soggette a variazioni.',
    en: 'Estimates based on current API pricing. Subject to change.',
  },

  // Scale
  'support.scale_title': { de: 'Massstab', fr: 'Échelle', it: 'Scala', en: 'Scale' },
  'support.col_law': { de: 'Gesetz', fr: 'Loi', it: 'Legge', en: 'Law' },
  'support.col_articles': { de: 'Artikel', fr: 'Articles', it: 'Articoli', en: 'Articles' },
  'support.col_target': { de: 'Ziel', fr: 'Objectif', it: 'Obiettivo', en: 'Target' },
  'support.col_status': { de: 'Status', fr: 'Statut', it: 'Stato', en: 'Status' },
  'support.status_progress': { de: 'In Arbeit', fr: 'En cours', it: 'In corso', en: 'In progress' },
  'support.status_open': { de: 'Offen', fr: 'Ouvert', it: 'Aperto', en: 'Open' },

  // Commitment
  'support.commitment_title': { de: 'Dauerhaft frei', fr: 'Libre en permanence', it: 'Permanentemente libero', en: 'Permanently free' },
  'support.commitment_text': {
    de: 'openlegalcommentary ist und bleibt frei zugänglich und quelloffen. Die Inhalte stehen dauerhaft unter CC BY-SA 4.0, der Code unter MIT-Lizenz. Es gibt keine Bezahlschranke, keine Premium-Version, keine Einschränkung des Zugangs. Spenden finanzieren die Erstellung der Inhalte — nicht den Zugang zu ihnen.',
    fr: "openlegalcommentary est et restera librement accessible et open source. Les contenus sont placés en permanence sous CC BY-SA 4.0, le code sous licence MIT. Il n'y a pas de mur payant, pas de version premium, pas de restriction d'accès. Les dons financent la création des contenus — pas l'accès.",
    it: "openlegalcommentary è e rimarrà liberamente accessibile e open source. I contenuti sono posti in permanenza sotto CC BY-SA 4.0, il codice sotto licenza MIT. Non ci sono barriere di pagamento, nessuna versione premium, nessuna restrizione dell'accesso. Le donazioni finanziano la creazione dei contenuti — non l'accesso.",
    en: 'openlegalcommentary is and will remain freely accessible and open source. Content is permanently licensed under CC BY-SA 4.0, code under MIT. There is no paywall, no premium version, no access restriction. Donations fund the creation of content — not access to it.',
  },

  // Independence
  'support.independence_title': { de: 'Unabhängigkeit', fr: 'Indépendance', it: 'Indipendenza', en: 'Independence' },
  'support.independence_text': {
    de: 'Keine Sponsoren, keine Werbung. Finanzierung ausschliesslich über individuelle Spenden. Spenderinnen und Spender werden auf Wunsch namentlich erwähnt — darüber hinaus keine Gegenleistung. Die Gründung einer gemeinnützigen Aktiengesellschaft ist in Vorbereitung.',
    fr: "Pas de sponsors, pas de publicité. Financement exclusivement par des dons individuels. Les donateurs sont mentionnés nommément sur demande — aucune autre contrepartie. La création d'une société anonyme d'utilité publique est en préparation.",
    it: "Nessuno sponsor, nessuna pubblicità. Finanziamento esclusivamente tramite donazioni individuali. I donatori sono menzionati nominativamente su richiesta — nessun'altra contropartita. È in preparazione la costituzione di una società anonima di pubblica utilità.",
    en: 'No sponsors, no advertising. Funding exclusively from individual donations. Donors are named on request — no other consideration. A public-benefit corporation (gemeinnützige AG) is being established.',
  },

  // Donate
  'support.donate_title': { de: 'Spenden', fr: 'Faire un don', it: 'Donare', en: 'Donate' },
  'support.donate_setup': {
    de: 'Die Spendenkanäle werden derzeit eingerichtet. Bei Interesse wenden Sie sich direkt an das Projekt.',
    fr: "Les canaux de don sont en cours de mise en place. Si vous êtes intéressé, contactez directement le projet.",
    it: 'I canali di donazione sono in fase di allestimento. Se interessati, contattate direttamente il progetto.',
    en: 'Donation channels are being set up. If interested, contact the project directly.',
  },
  'support.donate_contact': { de: 'Kontakt', fr: 'Contact', it: 'Contatto', en: 'Contact' },

  // Supporters
  'support.supporters_title': { de: 'Unterstützende', fr: 'Soutiens', it: 'Sostenitori', en: 'Supporters' },
  'support.supporters_intro': {
    de: 'Die folgenden Personen unterstützen openlegalcommentary (mit Einwilligung):',
    fr: 'Les personnes suivantes soutiennent openlegalcommentary (avec leur accord) :',
    it: 'Le seguenti persone sostengono openlegalcommentary (con il loro consenso):',
    en: 'The following individuals support openlegalcommentary (with their consent):',
  },
  'support.supporters_cta': {
    de: 'Werden Sie Teil dieser Liste.',
    fr: 'Rejoignez cette liste.',
    it: 'Entrate a far parte di questa lista.',
    en: 'Join this list.',
  },

  // Translation fallback
  'article.fallback_notice': {
    de: '',
    fr: 'Traduction non encore disponible. Le texte original allemand est affiché.',
    it: 'Traduzione non ancora disponibile. Viene visualizzato il testo originale tedesco.',
    en: 'Translation not yet available. Showing the German original.',
  },

  // Language switcher
  'lang.label': { de: 'Sprache', fr: 'Langue', it: 'Lingua', en: 'Language' },

  // Concepts
  'nav.concepts': { de: 'Konzepte', fr: 'Concepts', it: 'Concetti', en: 'Concepts' },
  'concepts.title': { de: 'Konzepte', fr: 'Concepts', it: 'Concetti', en: 'Concepts' },
  'concepts.subtitle': { de: 'Rechtskonzepte über Gesetzesgrenzen hinweg', fr: 'Concepts juridiques transversaux', it: 'Concetti giuridici trasversali', en: 'Cross-cutting legal concepts' },
  'concepts.confidence': { de: 'Doktrineller Status', fr: 'Statut doctrinal', it: 'Stato dottrinale', en: 'Doctrinal status' },
  'concepts.settled': { de: 'Gefestigt', fr: 'Établi', it: 'Consolidato', en: 'Settled' },
  'concepts.contested': { de: 'Umstritten', fr: 'Contesté', it: 'Contestato', en: 'Contested' },
  'concepts.evolving': { de: 'In Entwicklung', fr: 'En évolution', it: 'In evoluzione', en: 'Evolving' },
  'concepts.provisions': { de: 'Betroffene Bestimmungen', fr: 'Dispositions concernées', it: 'Disposizioni interessate', en: 'Related provisions' },

  // Contested
  'nav.contested': { de: 'Streitfragen', fr: 'Questions disputées', it: 'Questioni controverse', en: 'Disputed Questions' },
  'contested.title': { de: 'Streitfragen', fr: 'Questions disputées', it: 'Questioni controverse', en: 'Disputed Questions' },
  'contested.subtitle': { de: 'Wo vernünftige Juristinnen und Juristen uneins sind', fr: 'Où les juristes raisonnables divergent', it: 'Dove i giuristi ragionevoli divergono', en: 'Where reasonable jurists disagree' },
  'contested.question': { de: 'Die Frage', fr: 'La question', it: 'La questione', en: 'The question' },
  'contested.positions': { de: 'Positionen', fr: 'Positions', it: 'Posizioni', en: 'Positions' },

  // Cross-references
  'crossref.title': { de: 'Querverweise', fr: 'Références croisées', it: 'Riferimenti incrociati', en: 'Cross-references' },
  'crossref.concepts': { de: 'Konzepte', fr: 'Concepts', it: 'Concetti', en: 'Concepts' },
  'crossref.contested': { de: 'Streitfragen', fr: 'Questions disputées', it: 'Questioni controverse', en: 'Disputed Questions' },
};

export function t(key: string, lang: Lang): string {
  const entry = translations[key];
  if (!entry) return key;
  return entry[lang] ?? entry['de'] ?? key;
}
