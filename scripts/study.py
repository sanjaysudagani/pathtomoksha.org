"""Original, unreviewed study notes keyed to the frozen edition's XML IDs."""
from html import escape

NOTES = {
    'adi-1-1-0': (
        [('śrī-vedavyāsāya', 'to the revered Vedavyāsa'), ('namaḥ', 'homage')],
        'Homage to the revered Vedavyāsa.'),
    'adi-1-1-1': (
        [('nārāyaṇam', 'to Nārāyaṇa'), ('namaskṛtya', 'having bowed'), ('naram', 'to Nara'),
         ('ca eva', 'and also'), ('nara-uttamam', 'the foremost of men'), ('devīm', 'the goddess'),
         ('sarasvatīm', 'Sarasvatī'), ('ca eva', 'and also'), ('vyāsam', 'to Vyāsa (parenthetical reading)'),
         ('tataḥ', 'then'), ('jayam', 'Jaya, “Victory”'), ('udīrayet', 'one should recite')],
        'Having bowed to Nārāyaṇa, to Nara, foremost of men, and to the goddess Sarasvatī, one should then recite the Jaya.'),
    'adi-1-1-2': (
        [('nārāyaṇam', 'Nārāyaṇa'), ('sura-gurum', 'teacher of the gods'), ('jagad-eka-nātham', 'sole lord of the world'),
         ('bhakta-priyam', 'dear to devotees'), ('sakala-loka-namaskṛtam', 'honored by all worlds'), ('ca', 'and'),
         ('traiguṇya-varjitam', 'free of the three qualities'), ('ajam', 'unborn'), ('vibhum', 'all-pervading'),
         ('ādyam', 'primordial'), ('īśam', 'lord'), ('vande', 'I bow to'), ('bhava-ghnam', 'destroyer of worldly becoming'),
         ('amara-asura-siddha-vandyam', 'revered by gods, asuras, and perfected beings')],
        'I bow to Nārāyaṇa, teacher of the gods and sole lord of the world, dear to devotees and honored by all worlds. Free of the three qualities, unborn and all-pervading, he is the primordial lord who ends worldly becoming, revered by gods, asuras, and perfected beings.'),
    'adi-1-1-3': (
        [('namaḥ', 'homage'), ('dharmāya', 'to Dharma'), ('mahate', 'great'), ('namaḥ', 'homage'),
         ('kṛṣṇāya', 'to Kṛṣṇa'), ('vedhase', 'the creator'), ('brāhmaṇebhyaḥ', 'to the brahmins'),
         ('namaskṛtya', 'having bowed'), ('dharmān', 'duties'), ('vakṣyāmi', 'I shall explain'), ('śāśvatān', 'enduring')],
        'Homage to great Dharma. Homage to Kṛṣṇa, the creator. Having bowed to the brahmins, I shall explain the enduring duties.'),
    'adi-1-1-4': (
        [('oṃ', 'sacred syllable opening each salutation'), ('namaḥ', 'homage'), ('bhagavate', 'to the blessed Lord'),
         ('vāsudevāya', 'to Vāsudeva'), ('pitāmahāya', 'to the grandsire'), ('prajāpatibhyaḥ', 'to the lords of creatures'),
         ('kṛṣṇa-dvaipāyanāya', 'to Kṛṣṇa Dvaipāyana'), ('sarva-vighna-vināyakebhyaḥ', 'to all the Vināyakas associated with obstacles')],
        'Oṃ, homage to the blessed Lord Vāsudeva. Oṃ, homage to the grandsire. Oṃ, homage to the lords of creatures. Oṃ, homage to Kṛṣṇa Dvaipāyana. Oṃ, homage to all the Vināyakas associated with obstacles.')
}

def study_html(locator):
    if locator not in NOTES:
        return ''
    words, meaning = NOTES[locator]
    gloss = '; '.join(f'<i lang="sa-Latn">{escape(word)}</i> — {escape(value)}' for word, value in words)
    note = '<p>The source includes Vyāsa in parentheses. This draft follows the main reading.</p>' if locator == 'adi-1-1-1' else ''
    return f'<section class="study"><small>English study notes · draft</small><h3>Synonyms</h3><p>{gloss}.</p><h3>Translation</h3><p><strong>{escape(meaning)}</strong></p>{note}</section>'
