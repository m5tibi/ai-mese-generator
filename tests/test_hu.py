import pytest

from app import hu

# név -> (-val/-vel, tárgyeset, -nak/-nek, -hoz/-hez/-höz)
CASES = {
    "Bence": ("Bencével", "Bencét", "Bencének", "Bencéhez"),
    "Ábel": ("Ábellel", "Ábelt", "Ábelnek", "Ábelhez"),
    "Zsófi": ("Zsófival", "Zsófit", "Zsófinak", "Zsófihoz"),
    "Gergő": ("Gergővel", "Gergőt", "Gergőnek", "Gergőhöz"),
    "Örs": ("Örssel", "Örsöt", "Örsnek", "Örshöz"),
    "Máté": ("Mátéval", "Mátét", "Máténak", "Mátéhoz"),
    "Marcell": ("Marcellel", "Marcellt", "Marcellnek", "Marcellhez"),
    "Kornell": ("Kornellel", "Kornellt", "Kornellnek", "Kornellhez"),
    "Anett": ("Anettel", "Anettet", "Anettnek", "Anetthez"),
    "Bernadett": ("Bernadettel", "Bernadettet", "Bernadettnek", "Bernadetthez"),
    "Kovács": ("Kováccsal", "Kovácsot", "Kovácsnak", "Kovácshoz"),
    "Balázs": ("Balázzsal", "Balázst", "Balázsnak", "Balázshoz"),
    "Max": ("Maxszal", "Maxot", "Maxnak", "Maxhoz"),
    "Bálint": ("Bálinttal", "Bálintot", "Bálintnak", "Bálinthoz"),
    "Noémi": ("Noémivel", "Noémit", "Noéminek", "Noémihez"),
    "Emil": ("Emillel", "Emilt", "Emilnek", "Emilhez"),
    "Dominik": ("Dominikkal", "Dominikot", "Dominiknak", "Dominikhoz"),
    "Öcsi": ("Öcsivel", "Öcsit", "Öcsinek", "Öcsihez"),
    "Pötyi": ("Pötyivel", "Pötyit", "Pötyinek", "Pötyihez"),
    "Györgyi": ("Györgyivel", "Györgyit", "Györgyinek", "Györgyihez"),
    "Tünde": ("Tündével", "Tündét", "Tündének", "Tündéhez"),
    "Kati néni": ("Kati nénivel", "Kati nénit", "Kati néninek", "Kati nénihez"),
}


@pytest.mark.parametrize("name,expected", CASES.items())
def test_inflect(name, expected):
    assert tuple(hu.inflect(name, r) for r in ("val", "t", "nak", "hoz")) == expected


@pytest.mark.parametrize("word,suffix,expected", [
    ("Bence", "ek", "Bencéék"),
    ("Hanna", "va", "Hannává"),
    ("Ábel", "vá", "Ábellé"),
    ("Zoé", "ból", "Zoéból"),
    ("Luca", "kent", "Lucaként"),
])
def test_other_suffixes(word, suffix, expected):
    assert hu.inflect(word, suffix) == expected


def test_article():
    assert hu.article("Ernő") == "az"
    assert hu.article("Bence") == "a"
