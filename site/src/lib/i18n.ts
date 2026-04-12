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
    de: 'DAS RECHT GEHÖRT ALLEN',
    fr: 'LE DROIT APPARTIENT À TOUS',
    it: 'IL DIRITTO APPARTIENE A TUTTI',
    en: 'THE LAW BELONGS TO EVERYONE',
  },
  'support.headline': {
    de: 'Der erste offene Rechtskommentar der Schweiz',
    fr: 'Le premier commentaire juridique ouvert de Suisse',
    it: 'Il primo commento giuridico aperto della Svizzera',
    en: "Switzerland's first open legal commentary",
  },
  'support.lead': {
    de: 'openlegalcommentary macht das Schweizer Bundesrecht für alle zugänglich — KI-gestützt, quellenfundiert, täglich aktualisiert, in vier Sprachen, kostenlos. Für immer.',
    fr: "openlegalcommentary rend le droit fédéral suisse accessible à tous — assisté par IA, fondé sur les sources, mis à jour quotidiennement, en quatre langues, gratuit. Pour toujours.",
    it: "openlegalcommentary rende il diritto federale svizzero accessibile a tutti — assistito dall'IA, fondato sulle fonti, aggiornato quotidianamente, in quattro lingue, gratuito. Per sempre.",
    en: 'openlegalcommentary makes Swiss federal law accessible to everyone — AI-assisted, source-grounded, daily-updated, in four languages, free. Forever.',
  },
  'support.problem_title': { de: 'Das Problem', fr: 'Le problème', it: 'Il problema', en: 'The problem' },
  'support.problem_1': {
    de: 'Ein einzelner Band eines Standardkommentars kostet CHF 300–500. Für die vollständige Abdeckung des Bundesrechts benötigen Praktikerinnen und Praktiker Dutzende Bände — oder Datenbankabonnemente, die Tausende pro Jahr kosten.',
    fr: "Un seul volume d'un commentaire de référence coûte CHF 300–500. Pour une couverture complète du droit fédéral, les praticiens ont besoin de dizaines de volumes — ou d'abonnements à des bases de données coûtant des milliers de francs par an.",
    it: 'Un singolo volume di un commentario di riferimento costa CHF 300–500. Per una copertura completa del diritto federale, i professionisti necessitano di decine di volumi — o abbonamenti a banche dati che costano migliaia di franchi all\'anno.',
    en: 'A single volume of a standard commentary costs CHF 300–500. For complete coverage of federal law, practitioners need dozens of volumes — or database subscriptions costing thousands per year.',
  },
  'support.problem_2': {
    de: 'Studierende, Einzelanwälte, kleine Kanzleien, Bürgerinnen und Bürger — die meisten Menschen haben keinen Zugang zu dem Recht, das sie betrifft.',
    fr: "Étudiants, avocats indépendants, petites études, citoyens — la plupart des gens n'ont pas accès au droit qui les concerne.",
    it: 'Studenti, avvocati indipendenti, piccoli studi, cittadini — la maggior parte delle persone non ha accesso al diritto che li riguarda.',
    en: "Students, solo practitioners, small firms, citizens — most people lack access to the law that governs them.",
  },
  'support.problem_quote': {
    de: '«Das Recht gehört allen — nicht nur denen, die es sich leisten können.»',
    fr: '«Le droit appartient à tous — pas seulement à ceux qui peuvent se le permettre.»',
    it: '«Il diritto appartiene a tutti — non solo a chi può permetterselo.»',
    en: '"The law belongs to everyone — not just those who can afford it."',
  },
  'support.solution_title': { de: 'Die Lösung', fr: 'La solution', it: 'La soluzione', en: 'The solution' },
  'support.solution_1': {
    de: 'openlegalcommentary ist ein KI-gestützter Rechtskommentar, der auf den tatsächlichen Gesetzesmaterialien basiert — nicht auf Vermutungen.',
    fr: "openlegalcommentary est un commentaire juridique assisté par IA, fondé sur les matériaux législatifs réels — pas sur des suppositions.",
    it: "openlegalcommentary è un commento giuridico assistito dall'IA, basato sui materiali legislativi reali — non su supposizioni.",
    en: 'openlegalcommentary is an AI-assisted legal commentary grounded in actual legislative materials — not guesswork.',
  },
  'support.feature_1': {
    de: 'Doktrinale Analyse mit Randziffern, Streitständen und Praxishinweisen',
    fr: 'Analyse doctrinale avec numéros marginaux, controverses et indications pratiques',
    it: 'Analisi dottrinale con numeri marginali, controversie e indicazioni pratiche',
    en: 'Doctrinal analysis with marginal numbers, doctrinal debates, and practical guidance',
  },
  'support.feature_2': {
    de: 'Fundiert in echten Botschaften, parlamentarischen Debatten und Erläuterungsberichten',
    fr: 'Fondé sur les messages du Conseil fédéral, les débats parlementaires et les rapports explicatifs',
    it: 'Fondato su messaggi del Consiglio federale, dibattiti parlamentari e rapporti esplicativi',
    en: 'Grounded in actual Federal Council messages, parliamentary debates, and explanatory reports',
  },
  'support.feature_3': {
    de: 'Täglich aktualisiert mit neuer Bundesgerichtsrechtsprechung via OpenCaseLaw',
    fr: 'Mis à jour quotidiennement avec la nouvelle jurisprudence du Tribunal fédéral via OpenCaseLaw',
    it: 'Aggiornato quotidianamente con la nuova giurisprudenza del Tribunale federale via OpenCaseLaw',
    en: 'Daily-updated with new Federal Supreme Court case law via OpenCaseLaw',
  },
  'support.feature_4': {
    de: 'In vier Sprachen: Deutsch, Französisch, Italienisch, Englisch',
    fr: 'En quatre langues : allemand, français, italien, anglais',
    it: 'In quattro lingue: tedesco, francese, italiano, inglese',
    en: 'In four languages: German, French, Italian, English',
  },
  'support.feature_5': {
    de: 'Frei lizenziert unter CC BY-SA 4.0 — offen für alle, für immer',
    fr: 'Sous licence libre CC BY-SA 4.0 — ouvert à tous, pour toujours',
    it: 'Con licenza libera CC BY-SA 4.0 — aperto a tutti, per sempre',
    en: 'Freely licensed under CC BY-SA 4.0 — open to all, forever',
  },
  'support.quality_title': { de: 'Qualitätsbeispiel', fr: 'Exemple de qualité', it: 'Esempio di qualità', en: 'Quality example' },
  'support.quality_intro': {
    de: 'Art. 8 BV (Rechtsgleichheit) — mit namentlich genannten Ständerätinnen und Nationalräten, echten BBl-Seitenverweisen, Originalzitaten aus den parlamentarischen Debatten und einer lückenlosen Entstehungsgeschichte vom Erläuterungsbericht 1995 über die Botschaft 1996 bis zur Schlussabstimmung 1998.',
    fr: "Art. 8 Cst. (Égalité) — avec des conseillers aux États et nationaux nommément cités, des références BBl exactes, des citations originales des débats parlementaires et un historique législatif complet du rapport explicatif 1995 au vote final 1998.",
    it: "Art. 8 Cost. (Uguaglianza) — con consiglieri agli Stati e nazionali citati per nome, riferimenti BBl esatti, citazioni originali dei dibattiti parlamentari e una storia legislativa completa dal rapporto esplicativo 1995 al voto finale 1998.",
    en: 'Art. 8 FC (Equality) — with named members of parliament, exact BBl page references, original quotes from parliamentary debates, and a complete legislative history from the 1995 explanatory report through the 1996 message to the 1998 final vote.',
  },
  'support.quality_cta': {
    de: 'Art. 8 BV — Rechtsgleichheit lesen',
    fr: 'Lire Art. 8 Cst. — Égalité',
    it: 'Leggere Art. 8 Cost. — Uguaglianza',
    en: 'Read Art. 8 FC — Equality',
  },
  'support.budget_title': { de: 'Was Ihre Spende bewirkt', fr: 'Ce que votre don accomplit', it: 'Cosa realizza la vostra donazione', en: 'What your donation achieves' },
  'support.budget_intro': {
    de: 'Jeder Franken fliesst direkt in die Generierung, Qualitätsprüfung und Übersetzung der Kommentare.',
    fr: 'Chaque franc va directement à la génération, au contrôle qualité et à la traduction des commentaires.',
    it: 'Ogni franco va direttamente alla generazione, al controllo qualità e alla traduzione dei commenti.',
    en: 'Every franc goes directly to generating, quality-checking, and translating the commentaries.',
  },
  'support.budget_4': {
    de: '1 Artikel in 4 Sprachen, qualitätsgeprüft',
    fr: '1 article en 4 langues, vérifié',
    it: '1 articolo in 4 lingue, verificato',
    en: '1 article in 4 languages, quality-checked',
  },
  'support.budget_200': {
    de: 'Das gesamte Anwaltsgesetz (BGFA)',
    fr: "Toute la loi sur les avocats (LLCA)",
    it: "Tutta la legge sugli avvocati (LLCA)",
    en: 'The entire Lawyers Act (BGFA)',
  },
  'support.budget_1000': {
    de: 'Die gesamte Bundesverfassung (BV)',
    fr: 'Toute la Constitution fédérale (Cst.)',
    it: 'Tutta la Costituzione federale (Cost.)',
    en: 'The entire Federal Constitution (FC)',
  },
  'support.budget_21000': {
    de: 'Alle 9 Bundesgesetze (4\'843 Artikel)',
    fr: 'Les 9 lois fédérales (4\'843 articles)',
    it: 'Tutte le 9 leggi federali (4\'843 articoli)',
    en: 'All 9 federal laws (4,843 articles)',
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
  'support.cost_gen': { de: 'Generierung (Sonnet 4.6)', fr: 'Génération (Sonnet 4.6)', it: 'Generazione (Sonnet 4.6)', en: 'Generation (Sonnet 4.6)' },
  'support.cost_eval': { de: 'Qualitätsprüfung (Opus 4.6)', fr: 'Contrôle qualité (Opus 4.6)', it: 'Controllo qualità (Opus 4.6)', en: 'Quality evaluation (Opus 4.6)' },
  'support.cost_trans': { de: 'Übersetzung (3 Sprachen)', fr: 'Traduction (3 langues)', it: 'Traduzione (3 lingue)', en: 'Translation (3 languages)' },
  'support.cost_mat': { de: 'Materialienrecherche', fr: 'Recherche de matériaux', it: 'Ricerca dei materiali', en: 'Legislative materials research' },
  'support.cost_retry': { de: 'Qualitäts-Wiederholungsläufe', fr: 'Itérations de qualité', it: 'Iterazioni di qualità', en: 'Quality retry iterations' },
  'support.cost_reserve': { de: 'Reserve (25%)', fr: 'Réserve (25%)', it: 'Riserva (25%)', en: 'Reserve (25%)' },
  'support.independence_title': { de: 'Unabhängigkeit', fr: 'Indépendance', it: 'Indipendenza', en: 'Independence' },
  'support.independence_1': {
    de: 'Keine Sponsoren. Keine Werbung. Keine redaktionelle Einflussnahme.',
    fr: 'Pas de sponsors. Pas de publicité. Pas d\'influence éditoriale.',
    it: 'Nessuno sponsor. Nessuna pubblicità. Nessuna influenza editoriale.',
    en: 'No sponsors. No advertising. No editorial influence.',
  },
  'support.independence_2': {
    de: 'openlegalcommentary wird ausschliesslich durch individuelle Spenden finanziert. Jede Spenderin und jeder Spender trägt denselben Rang — es gibt keine bevorzugte Behandlung.',
    fr: "openlegalcommentary est financé exclusivement par des dons individuels. Chaque donateur a le même rang — il n'y a pas de traitement préférentiel.",
    it: 'openlegalcommentary è finanziato esclusivamente da donazioni individuali. Ogni donatore ha lo stesso rango — non esiste alcun trattamento preferenziale.',
    en: 'openlegalcommentary is funded exclusively by individual donations. Every donor has equal standing — there is no preferential treatment.',
  },
  'support.independence_3': {
    de: 'Vollständige Transparenz: Jeder Franken ist einem Zweck zugeordnet. Die Kostenstruktur wird neben den Kommentaren publiziert.',
    fr: 'Transparence totale : chaque franc est affecté à un but. La structure des coûts est publiée à côté des commentaires.',
    it: 'Trasparenza totale: ogni franco è assegnato a uno scopo. La struttura dei costi è pubblicata accanto ai commenti.',
    en: 'Full transparency: every franc is accounted for. The cost structure is published alongside the commentaries.',
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
