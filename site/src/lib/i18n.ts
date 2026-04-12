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
    de: 'Diese Plattform befindet sich in aktiver Entwicklung. Die Inhalte werden täglich von KI-Modellen aus öffentlichen Rechtsquellen erstellt und automatisch auf Qualität geprüft.',
    fr: "Cette plateforme est en développement actif. Le contenu est généré quotidiennement par des modèles d'IA à partir de sources juridiques publiques et évalué automatiquement pour sa qualité.",
    it: "Questa piattaforma è in sviluppo attivo. I contenuti sono generati quotidianamente da modelli di IA a partire da fonti giuridiche pubbliche e valutati automaticamente per la qualità.",
    en: 'This platform is in active development. Content is generated daily by AI models from public legal sources and automatically evaluated for quality.',
  },
  'overlay.body2': {
    de: 'Die Kommentare sind ein Ausgangspunkt für die Recherche — keine abschliessende Rechtsauskunft. Prüfen Sie Aussagen stets gegen die Primärquellen.',
    fr: 'Ces commentaires sont un point de départ pour la recherche — pas un conseil juridique définitif. Vérifiez toujours les affirmations par rapport aux sources primaires.',
    it: 'Questi commenti sono un punto di partenza per la ricerca — non una consulenza legale definitiva. Verificate sempre le affermazioni rispetto alle fonti primarie.',
    en: 'These commentaries are a starting point for research — not definitive legal advice. Always verify statements against primary sources.',
  },
  'overlay.body3': {
    de: 'Wir verbessern die Plattform laufend. Übersetzungen können der deutschen Originalfassung hinterherhinken. Feedback ist willkommen.',
    fr: "Nous améliorons la plateforme en continu. Les traductions peuvent être en retard sur la version originale allemande. Vos commentaires sont les bienvenus.",
    it: 'Miglioriamo la piattaforma continuamente. Le traduzioni possono essere in ritardo rispetto alla versione originale tedesca. I vostri commenti sono benvenuti.',
    en: "We're improving the platform continuously. Translations may lag the German original. Feedback is welcome.",
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
    de: 'openlegalcommentary ist ein offener, KI-gestützter Rechtskommentar zum Schweizer Bundesrecht. Die Inhalte sind frei zugänglich unter CC BY-SA 4.0 und werden durch individuelle Spenden finanziert. Diese Seite erläutert, was das Projekt leistet, was es kostet und wie Sie es unterstützen können.',
    fr: "openlegalcommentary est un commentaire juridique ouvert et assisté par IA sur le droit fédéral suisse. Les contenus sont librement accessibles sous CC BY-SA 4.0 et financés par des dons individuels. Cette page explique ce que le projet accomplit, ce qu'il coûte et comment vous pouvez le soutenir.",
    it: "openlegalcommentary è un commento giuridico aperto e assistito dall'IA sul diritto federale svizzero. I contenuti sono liberamente accessibili sotto CC BY-SA 4.0 e finanziati da donazioni individuali. Questa pagina spiega cosa realizza il progetto, quanto costa e come potete sostenerlo.",
    en: 'openlegalcommentary is an open, AI-assisted legal commentary on Swiss federal law. Content is freely accessible under CC BY-SA 4.0 and funded by individual donations. This page explains what the project does, what it costs, and how you can support it.',
  },
  'support.problem_title': { de: 'Was openlegalcommentary ist', fr: "Ce qu'est openlegalcommentary", it: 'Cosa è openlegalcommentary', en: 'What openlegalcommentary is' },
  'support.problem_1': {
    de: 'Ein Rechtskommentar zu allen neun wichtigsten Bundesgesetzen (BV, ZGB, OR, ZPO, StGB, StPO, SchKG, VwVG, BGFA), generiert durch KI-Modelle auf Grundlage öffentlicher Rechtsquellen, tagesaktueller Bundesgerichtsrechtsprechung und der originalen Gesetzesmaterialien (Botschaften, parlamentarische Beratungen, Erläuterungsberichte).',
    fr: "Un commentaire juridique sur les neuf principales lois fédérales (Cst., CC, CO, CPC, CP, CPP, LP, PA, LLCA), généré par des modèles d'IA sur la base de sources juridiques publiques, de la jurisprudence actuelle du Tribunal fédéral et des matériaux législatifs originaux (messages, délibérations parlementaires, rapports explicatifs).",
    it: "Un commento giuridico sulle nove principali leggi federali (Cost., CC, CO, CPC, CP, CPP, LEF, PA, LLCA), generato da modelli di IA sulla base di fonti giuridiche pubbliche, della giurisprudenza attuale del Tribunale federale e dei materiali legislativi originali (messaggi, deliberazioni parlamentari, rapporti esplicativi).",
    en: 'A legal commentary on all nine major federal laws (FC, CC, CO, CPC, SCC, CrimPC, DEBA, APA, BGFA), generated by AI models from public legal sources, current Federal Supreme Court case law, and original legislative materials (Federal Council messages, parliamentary debates, explanatory reports).',
  },
  'support.problem_2': {
    de: 'Jeder Artikel wird in vier Sprachen publiziert (DE/FR/IT/EN), automatisch auf zehn Qualitätskriterien geprüft und bei neuen Leitentscheiden aktualisiert. Die Inhalte stehen unter einer freien Lizenz (CC BY-SA 4.0).',
    fr: "Chaque article est publié en quatre langues (DE/FR/IT/EN), vérifié automatiquement selon dix critères de qualité et mis à jour lors de nouveaux arrêts de principe. Les contenus sont sous licence libre (CC BY-SA 4.0).",
    it: 'Ogni articolo è pubblicato in quattro lingue (DE/FR/IT/EN), verificato automaticamente secondo dieci criteri di qualità e aggiornato in caso di nuove sentenze di principio. I contenuti sono sotto licenza libera (CC BY-SA 4.0).',
    en: 'Each article is published in four languages (DE/FR/IT/EN), automatically evaluated against ten quality criteria, and updated when new leading decisions are published. Content is freely licensed under CC BY-SA 4.0.',
  },
  'support.problem_quote': {
    de: '',
    fr: '',
    it: '',
    en: '',
  },
  'support.solution_title': { de: 'Wie es funktioniert', fr: 'Comment ça fonctionne', it: 'Come funziona', en: 'How it works' },
  'support.solution_1': {
    de: 'Für jeden Gesetzesartikel durchläuft die Generierung einen mehrstufigen Prozess:',
    fr: 'Pour chaque article de loi, la génération suit un processus en plusieurs étapes :',
    it: 'Per ogni articolo di legge, la generazione segue un processo in più fasi:',
    en: 'For each article of law, generation follows a multi-step process:',
  },
  'support.feature_1': {
    de: 'Recherche der Leitentscheide und Doktrin via OpenCaseLaw (930\'000+ Entscheide)',
    fr: 'Recherche des arrêts de principe et de la doctrine via OpenCaseLaw (930\'000+ décisions)',
    it: 'Ricerca delle sentenze di principio e della dottrina via OpenCaseLaw (930\'000+ decisioni)',
    en: 'Research of leading cases and doctrine via OpenCaseLaw (930,000+ decisions)',
  },
  'support.feature_2': {
    de: 'Generierung der doktrinalen Analyse (Entstehungsgeschichte, Norminhalt, Streitstände, Praxishinweise)',
    fr: "Génération de l'analyse doctrinale (historique législatif, contenu normatif, controverses, indications pratiques)",
    it: "Generazione dell'analisi dottrinale (storia legislativa, contenuto normativo, controversie, indicazioni pratiche)",
    en: 'Generation of doctrinal analysis (legislative history, normative content, doctrinal debates, practical guidance)',
  },
  'support.feature_3': {
    de: 'Qualitätsprüfung durch ein unabhängiges KI-Modell gegen zehn Kriterien (Präzision, Konzision, Relevanz, akademische Strenge u.a.)',
    fr: "Contrôle qualité par un modèle d'IA indépendant selon dix critères (précision, concision, pertinence, rigueur académique, etc.)",
    it: "Controllo qualità tramite un modello di IA indipendente secondo dieci criteri (precisione, concisione, rilevanza, rigore accademico, ecc.)",
    en: 'Quality evaluation by an independent AI model against ten criteria (precision, conciseness, relevance, academic rigour, etc.)',
  },
  'support.feature_4': {
    de: 'Übersetzung in Französisch, Italienisch und Englisch',
    fr: 'Traduction en français, italien et anglais',
    it: 'Traduzione in francese, italiano e inglese',
    en: 'Translation into French, Italian, and English',
  },
  'support.feature_5': {
    de: 'Automatische Wiederholung bei ungenügender Qualität (bis zu drei Durchläufe pro Artikel)',
    fr: "Répétition automatique en cas de qualité insuffisante (jusqu'à trois passages par article)",
    it: 'Ripetizione automatica in caso di qualità insufficiente (fino a tre passaggi per articolo)',
    en: 'Automatic retry on insufficient quality (up to three passes per article)',
  },
  'support.quality_title': { de: 'Beispiel', fr: 'Exemple', it: 'Esempio', en: 'Example' },
  'support.quality_intro': {
    de: 'Art. 8 BV (Rechtsgleichheit) zeigt, wie ein Artikel mit vollständigen Materialien aussieht: Entstehungsgeschichte auf Grundlage der Botschaft (BBl 1997 I 141 ff.), des Erläuterungsberichts 1995 und der Protokolle aus National- und Ständerat, mit namentlicher Zuordnung der Voten zu den jeweiligen Ratsmitgliedern.',
    fr: "L'art. 8 Cst. (Égalité) montre à quoi ressemble un article avec des matériaux complets : historique législatif fondé sur le message (FF 1997 I 141 ss), le rapport explicatif 1995 et les procès-verbaux du Conseil national et du Conseil des États, avec attribution nominative des interventions aux parlementaires.",
    it: "L'art. 8 Cost. (Uguaglianza) mostra come appare un articolo con materiali completi: storia legislativa basata sul messaggio (FF 1997 I 141 segg.), il rapporto esplicativo 1995 e i verbali del Consiglio nazionale e del Consiglio degli Stati, con attribuzione nominativa degli interventi ai parlamentari.",
    en: 'Art. 8 FC (Equality) shows what an article with complete materials looks like: legislative history based on the Federal Council message (BBl 1997 I 141 ff.), the 1995 explanatory report, and the National Council and Council of States debate records, with statements attributed to named members of parliament.',
  },
  'support.quality_cta': {
    de: 'Art. 8 BV — Doktrin ansehen',
    fr: 'Art. 8 Cst. — Voir la doctrine',
    it: 'Art. 8 Cost. — Vedere la dottrina',
    en: 'Art. 8 FC — View doctrine',
  },
  'support.budget_title': { de: 'Was Ihre Spende bewirkt', fr: 'Ce que votre don accomplit', it: 'Cosa realizza la vostra donazione', en: 'What your donation achieves' },
  'support.budget_intro': {
    de: 'Jeder Franken fliesst direkt in die Generierung, Qualitätsprüfung und Übersetzung der Kommentare.',
    fr: 'Chaque franc va directement à la génération, au contrôle qualité et à la traduction des commentaires.',
    it: 'Ogni franco va direttamente alla generazione, al controllo qualità e alla traduzione dei commenti.',
    en: 'Every franc goes directly to generating, quality-checking, and translating the commentaries.',
  },
  'support.budget_4': {
    de: '= 1 Artikel (4 Sprachen, qualitätsgeprüft)',
    fr: '= 1 article (4 langues, vérifié)',
    it: '= 1 articolo (4 lingue, verificato)',
    en: '= 1 article (4 languages, quality-checked)',
  },
  'support.budget_200': {
    de: '= BGFA (Anwaltsgesetz, 38 Artikel)',
    fr: '= LLCA (Loi sur les avocats, 38 articles)',
    it: '= LLCA (Legge sugli avvocati, 38 articoli)',
    en: '= BGFA (Lawyers Act, 38 articles)',
  },
  'support.budget_1000': {
    de: '= BV (Bundesverfassung, 233 Artikel)',
    fr: '= Cst. (Constitution fédérale, 233 articles)',
    it: '= Cost. (Costituzione federale, 233 articoli)',
    en: '= FC (Federal Constitution, 233 articles)',
  },
  'support.budget_21000': {
    de: '= alle 9 Bundesgesetze (4\'843 Artikel)',
    fr: '= les 9 lois fédérales (4\'843 articles)',
    it: '= tutte le 9 leggi federali (4\'843 articoli)',
    en: '= all 9 federal laws (4,843 articles)',
  },
  'support.laws_title': { de: 'Gesetze im Überblick', fr: "Vue d'ensemble des lois", it: 'Panoramica delle leggi', en: 'Laws overview' },
  'support.col_law': { de: 'Gesetz', fr: 'Loi', it: 'Legge', en: 'Law' },
  'support.col_articles': { de: 'Artikel', fr: 'Articles', it: 'Articoli', en: 'Articles' },
  'support.col_target': { de: 'Ziel', fr: 'Objectif', it: 'Obiettivo', en: 'Target' },
  'support.col_status': { de: 'Status', fr: 'Statut', it: 'Stato', en: 'Status' },
  'support.transparency_title': { de: 'Kostentransparenz', fr: 'Transparence des coûts', it: 'Trasparenza dei costi', en: 'Cost transparency' },
  'support.transparency_intro': {
    de: 'Was ein Artikel kostet — aufgeschlüsselt:',
    fr: "Ce que coûte un article — détaillé :",
    it: 'Quanto costa un articolo — in dettaglio:',
    en: 'What one article costs — broken down:',
  },
  'support.col_item': { de: 'Position', fr: 'Poste', it: 'Voce', en: 'Item' },
  'support.col_cost': { de: 'Pro Artikel', fr: 'Par article', it: 'Per articolo', en: 'Per article' },
  'support.cost_gen': { de: 'Generierung der Doktrin', fr: 'Génération de la doctrine', it: 'Generazione della dottrina', en: 'Doctrine generation' },
  'support.cost_eval': { de: 'Unabhängige Qualitätsprüfung', fr: 'Contrôle qualité indépendant', it: 'Controllo qualità indipendente', en: 'Independent quality evaluation' },
  'support.cost_trans': { de: 'Übersetzung in 3 Sprachen', fr: 'Traduction en 3 langues', it: 'Traduzione in 3 lingue', en: 'Translation into 3 languages' },
  'support.cost_mat': { de: 'Materialienrecherche und -aufbereitung', fr: 'Recherche et traitement des matériaux', it: 'Ricerca e preparazione dei materiali', en: 'Legislative materials research and processing' },
  'support.cost_retry': { de: 'Wiederholungsläufe bei ungenügender Qualität', fr: 'Itérations en cas de qualité insuffisante', it: 'Iterazioni in caso di qualità insufficiente', en: 'Retry iterations on insufficient quality' },
  'support.cost_reserve': { de: 'Reserve (Preisänderungen, Infrastruktur)', fr: 'Réserve (changements de prix, infrastructure)', it: 'Riserva (variazioni di prezzo, infrastruttura)', en: 'Reserve (price changes, infrastructure)' },
  'support.independence_title': { de: 'Unabhängigkeit', fr: 'Indépendance', it: 'Indipendenza', en: 'Independence' },
  'support.independence_1': {
    de: 'openlegalcommentary nimmt keine Sponsorengelder an und schaltet keine Werbung. Die redaktionelle Unabhängigkeit ist nicht verhandelbar.',
    fr: "openlegalcommentary n'accepte pas de fonds de sponsors et ne diffuse pas de publicité. L'indépendance éditoriale n'est pas négociable.",
    it: "openlegalcommentary non accetta fondi da sponsor e non pubblica pubblicità. L'indipendenza editoriale non è negoziabile.",
    en: 'openlegalcommentary does not accept sponsorship funds and does not run advertising. Editorial independence is non-negotiable.',
  },
  'support.independence_2': {
    de: 'Die Finanzierung erfolgt ausschliesslich über individuelle Spenden. Spenderinnen und Spender werden auf Wunsch namentlich erwähnt. Darüber hinaus besteht keine Gegenleistung.',
    fr: "Le financement provient exclusivement de dons individuels. Les donatrices et donateurs sont mentionnés nommément sur demande. Il n'y a pas d'autre contrepartie.",
    it: 'Il finanziamento proviene esclusivamente da donazioni individuali. I donatori sono menzionati nominativamente su richiesta. Non vi è altra contropartita.',
    en: 'Funding comes exclusively from individual donations. Donors are named on request. There is no other consideration.',
  },
  'support.independence_3': {
    de: 'Die Kostenstruktur ist auf dieser Seite offengelegt. Die Beträge sind Schätzungen auf Grundlage der aktuellen API-Preise und können sich bei Preisänderungen der Anbieter verändern.',
    fr: "La structure des coûts est présentée sur cette page. Les montants sont des estimations basées sur les prix API actuels et peuvent varier en cas de changement de prix des fournisseurs.",
    it: 'La struttura dei costi è presentata in questa pagina. Gli importi sono stime basate sui prezzi API attuali e possono variare in caso di modifiche dei prezzi dei fornitori.',
    en: 'The cost structure is disclosed on this page. Amounts are estimates based on current API pricing and may change if provider prices change.',
  },
  'support.donate_title': { de: 'Spenden', fr: 'Faire un don', it: 'Donare', en: 'Donate' },
  'support.donate_intro': {
    de: 'Ihre Spende geht ohne Abzüge direkt an das Projekt.',
    fr: 'Votre don va directement au projet, sans déduction.',
    it: 'La vostra donazione va direttamente al progetto, senza deduzioni.',
    en: 'Your donation goes directly to the project with no deductions.',
  },
  'support.donate_twint': { de: 'Gebührenfrei', fr: 'Sans frais', it: 'Senza commissioni', en: 'Zero fees' },
  'support.donate_bank_title': { de: 'Banküberweisung', fr: 'Virement bancaire', it: 'Bonifico bancario', en: 'Bank transfer' },
  'support.donate_bank': { de: 'Gebührenfrei', fr: 'Sans frais', it: 'Senza commissioni', en: 'Zero fees' },
  'support.donate_github': { de: 'Für internationale Unterstützende', fr: 'Pour les donateurs internationaux', it: 'Per i sostenitori internazionali', en: 'For international supporters' },
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
