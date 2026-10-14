"""Devanagari -> rough Roman spelling, and a loose "sound key" for search.

Hindi names are spelled many ways in English (Chauhan / Chouhan / Chohan), so search
compares a simplified key on both sides instead of exact spellings.
"""
import re
import unicodedata

VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo', 'ऋ': 'ri',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'ऑ': 'o',
}
MATRAS = {
    'ा': 'aa', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ॉ': 'o',
}
CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'n',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'n',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'ळ': 'l', 'व': 'v',
    'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'क़': 'q', 'ख़': 'kh', 'ग़': 'gh', 'ज़': 'z', 'ड़': 'r', 'ढ़': 'rh', 'फ़': 'f',
}
VIRAMA, NUKTA = '्', '़'
NASALS = {'ं': 'n', 'ँ': 'n', 'ः': 'h'}
DIGITS = str.maketrans('०१२३४५६७८९', '0123456789')


def to_roman(text):
    """Readable Roman spelling: चौहान -> chauhaan -> trimmed to 'chauhan' style."""
    text = unicodedata.normalize('NFC', text).translate(DIGITS)
    out = []
    chars = list(text)
    i = 0
    while i < len(chars):
        c = chars[i]
        if i + 1 < len(chars) and chars[i + 1] == NUKTA:
            c = unicodedata.normalize('NFC', c + NUKTA)
            i += 1
        if c in CONSONANTS:
            out.append(CONSONANTS[c])
            nxt = chars[i + 1] if i + 1 < len(chars) else ''
            if nxt in MATRAS:
                out.append(MATRAS[nxt])
                i += 1
            elif nxt == VIRAMA:
                i += 1
            else:
                out.append('a')  # inherent vowel
        elif c in VOWELS:
            out.append(VOWELS[c])
        elif c in MATRAS:
            out.append(MATRAS[c])
        elif c in NASALS:
            out.append(NASALS[c])
        else:
            out.append(c)
        i += 1
    words = ''.join(out).split(' ')
    # drop the final inherent 'a' (Hindi schwa deletion): "chauhaana" -> "chauhaan"
    words = [w[:-1] if len(w) > 2 and w.endswith('a') and not w.endswith('aa') else w for w in words]
    return ' '.join(words).replace('aa', 'a').replace('ee', 'i').replace('oo', 'u')


def sound_key(text):
    """Loose key so different spellings meet: 'Chouhan', 'chauhan', 'चौहान' -> 'chn'."""
    if re.search(r'[ऀ-ॿ]', text):
        text = to_roman(text)
    s = text.lower()
    s = re.sub(r'[^a-z]', '', s)
    for a, b in (('w', 'v'), ('ph', 'f'), ('sh', 's'), ('z', 'j'), ('q', 'k'), ('x', 'ks')):
        s = s.replace(a, b)
    s = re.sub(r'ch+|c', 'c', s)              # c / ch / chh
    s = re.sub(r'([kgjtdpbr])h', r'\1', s)  # aspirates: kh -> k, bh -> b
    s = re.sub(r'(.)\1+', r'\1', s)          # doubled letters
    s = re.sub(r'[aeiouy]', '', s)          # vowels are spelled every which way
    return s


def deva_key(text):
    """Normalise Devanagari for matching: drop nukta, chandrabindu -> anusvara, no spaces."""
    t = unicodedata.normalize('NFC', text).replace(NUKTA, '').replace('ँ', 'ं')
    return re.sub(r'[\s()\-.,]', '', t)
