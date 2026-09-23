# Illusztrációk

Minden meséhez kell egy borító (`borito.jpeg`) és fejezetenként egy kép (`1.jpeg` … `4.jpeg`).
A mesékben a képek helye már be van jelölve, így elég a fájlokat a mese mappájába tenni.
Amíg egy kép hiányzik, a mese működik, a PDF-ben egyszerűen kimarad (a borító helyén egy hold jelenik meg),
a `python -m app.check_stories` pedig kiírja, melyik hiányzik még.

## Formátum

- Fekvő, 4:3 arányú kép (pl. 1184×896 vagy 1536×1152 px), JPEG.
- A kép ne tartalmazzon szöveget, betűket, feliratot.

## A legfontosabb szabály: ne látsszon a gyerek arca

A főszereplő minden vásárlónál más: kisfiú vagy kislány, szőke vagy barna, 2 vagy 7 éves.
Ha a képen egy konkrét gyerek látszik, a szülő azt fogja érezni, hogy „ez nem az én gyerekem”.
Ezért a képeken a gyerek:

- hátulról, messziről, kicsiben látszik, vagy
- csak a keze, a lába, a takaró alól kilógó haja látszik, vagy
- egyáltalán nincs a képen, és a mese állatszereplői, tárgyai, helyszínei kerülnek előtérbe.

A promptok ezt már tartalmazzák (`child seen from behind`, `face not visible` stb.).

## Egységes stílus

Minden prompt végére másold oda ezt a stílusleírást, hogy a képek egy könyvnek tűnjenek:

```
Soft watercolor and colored pencil children's picture book illustration, cute characters with large
expressive eyes, warm pastel palette, gentle glowing light, cozy and calm mood, rounded friendly shapes,
soft white vignette edges, no text, no letters, no words, 4:3 landscape.
```

**Visszatérő szereplők:** előbb generáld le egyszer a szereplőt önmagában (a lenti „karakterlap” prompttal),
és a jól sikerült képet add meg referenciaként a többi képnél (ChatGPT-ben töltsd fel és írd hozzá:
„use this character exactly”, Midjourney-ben `--cref` / omni reference). Így minden oldalon ugyanaz a nyuszi,
ugyanaz a manó lesz.

**Plüss:** a mesékben a plüss nevét a szülő adja meg, a kinézetét nem tudjuk. Ezért mindig egy semleges,
kopottas, barna plüssmacit rajzoltass (`a small worn brown teddy bear`).

Kereskedelmi felhasználás előtt nézd meg, hogy a használt képgeneráló feltételei megengedik-e a képek eladását.

---

## A bátor kis róka és a titokzatos erdő (`roka/`)

A borító már megvan. A fejezetekhez igazodj a borító rókájához (töltsd fel referenciaként).

1. `1.jpeg` — A cozy child's bedroom at night, a tiny emerald-green bird with glowing starlit wings flying in through an open window, a child in pajamas sitting up in bed seen from behind, holding a small worn brown teddy bear.
2. `2.jpeg` — A narrow path into an enchanted forest at dusk, juniper bushes and ancient oaks with softly glowing leaves, a small child with a backpack and a teddy bear under one arm walking away from the viewer, tiny and far away.
3. `3.jpeg` — A moonlit forest clearing sprinkled with silver light, a small red fox kit sitting sadly behind a big rock, wiping a tear with its paw, a glowing golden star-shaped jewel in front of it.
4. `4.jpeg` — A giant old oak tree glowing in a thousand colors with a radiant star in its branches, fireflies dancing along a path, the little fox happily waving goodbye, a small child and teddy bear seen from behind in the distance.

## A sárkánykaland és az elveszett csillag (`sarkany/`)

A borító már megvan. A fejezetekhez igazodj a borító sárkányához.

1. `1.jpeg` — A magical kingdom high above the clouds, mountain peaks touching fluffy clouds, a village in a valley, the sky suddenly darkening as a big green dragon flies away holding a glowing sun-crystal.
2. `2.jpeg` — A steep rocky mountain path in strong wind, a small child with a satchel seen from behind climbing upward, a tired little bird resting on the child's shoulder.
3. `3.jpeg` — Inside a cave lined with sparkling crystals, a huge but gentle green-scaled dragon sitting sadly in the corner, hugging a glowing crystal, looking lonely, not scary.
4. `4.jpeg` — The happy green dragon flying above the clouds at sunset with a small child riding on its back seen from behind, the valley below lit up by the glowing sun-crystal.

## A Holdnyuszi altatója (`holdnyuszi/`)

**Karakterlap:** A small moon rabbit with soft silvery-white fur that glows faintly, very long ears, big gentle dark eyes, a tiny crescent-moon mark on its forehead, full body, plain background.

- `borito.jpeg` — The silvery moon rabbit sliding down a beam of moonlight toward a cozy bedroom window, big crescent moon and stars in a deep blue night sky, peaceful and dreamy.
1. `1.jpeg` — A cozy dim bedroom at night, a rumpled blanket and a child's hand peeking out, a small worn brown teddy bear on the pillow, moonlight streaming through the window.
2. `2.jpeg` — The moon rabbit sitting on the edge of a bed, gently showing how to breathe with a paw on its own tummy, calm and kind expression, soft moonlight.
3. `3.jpeg` — Close-up of a quilted blanket with small feet-shaped bumps under it, the moon rabbit whispering goodnight to them, tiny sparkles drifting, everything soft and heavy with sleep.
4. `4.jpeg` — A soft white cloud floating over a sleeping town at night, a small child seen from behind sitting on the cloud with a teddy bear, the moon rabbit counting stars, a cat asleep on a bench below.

## Pislogó és a bújócskázó árnyak (`pislogo/`)

**Karakterlap:** A tiny friendly firefly with a softly glowing yellow-green tail, big round shiny eyes, small translucent wings, cheerful smile, full body, plain dark background.

- `borito.jpeg` — The little firefly glowing on a windowsill of a dark child's bedroom, friendly soft shadows on the wall, warm and not scary.
1. `1.jpeg` — A child's bedroom at night with a wardrobe and a coat on a hook casting a long funny-shaped shadow on the wall, a lump under the blanket clutching a teddy bear, face hidden, slightly spooky but gentle.
2. `2.jpeg` — The tiny firefly blinking on the windowsill, its light making a small warm circle in the dark room, a child's eyes peeking over the edge of a blanket (only the top of the head visible).
3. `3.jpeg` — The firefly shining on a coat hanging on a hook, revealing it is just a coat with a chestnut peeking out of the pocket, the long shadow now looking silly, playful mood.
4. `4.jpeg` — A small warm night-light glowing on a bedside table, a teddy bear tucked in a bed, the firefly waving goodbye outside the window in a garden full of fireflies.

## Az első nap az oviban (`ovi/`)

- `borito.jpeg` — A bright, friendly kindergarten entrance with colorful drawings on the door, a small child seen from behind holding an adult's hand and a teddy bear, morning sunshine.
1. `1.jpeg` — A cozy bedroom in the evening after bath time, a teddy bear sitting on a pillow looking a little worried, a child's hands holding it gently.
2. `2.jpeg` — A kindergarten cloakroom with small cubbies, each with a little picture symbol on the door (sun, apple, snail, car), a smiling kind kindergarten teacher crouching down, warm light.
3. `3.jpeg` — A kindergarten playroom with building blocks, a toy kitchen and a bookshelf, two children seen from behind building a tall block tower together, a teddy bear and a plush bunny sitting on top like guards.
4. `4.jpeg` — The kindergarten door opening in the afternoon light, a parent kneeling with open arms, a small child running toward them seen from behind, holding a teddy bear.

## Nyami és a szivárványtányér (`szivarvanytanyer/`)

**Karakterlap:** A tiny food explorer gnome, as small as a spoon, with a round red berry-shaped hat, shoes like two green peas, a little explorer's magnifying glass, curious happy face, full body, plain background.

- `borito.jpeg` — The tiny gnome standing on the rim of a plate full of colorful vegetables arranged like a rainbow, holding a magnifying glass, playful and bright.
1. `1.jpeg` — A dinner table with a child's plate holding a small portion of green vegetables, a child's hand pushing the plate away, and the tiny gnome peeking over the plate's edge.
2. `2.jpeg` — The tiny gnome bowing politely on the edge of the plate, then sniffing a vegetable dramatically, nearly sneezing, funny expression.
3. `3.jpeg` — A child's fingers holding a tiny mouse-sized bite of vegetable on a fork, the gnome watching excitedly, jumping with joy next to a glass of water.
4. `4.jpeg` — A beautiful rainbow-colored plate with red, orange, yellow, green and purple foods, the gnome waving goodbye and sitting on a slice of fruit.

## Csillámka és a falánk Cukormanók (`fogmoso/`)

**Karakterlap 1:** A tiny sparkly helper fairy, thumb-sized, with shimmering translucent wings, a toothbrush-shaped wand, a white dress like tooth enamel, kind cheerful face, full body.
**Karakterlap 2:** Tiny round silly sugar gnomes, candy-colored, with crumb-covered cheeks and happy greedy grins, funny not scary, group of five.

- `borito.jpeg` — The sparkly fairy flying next to a toothbrush with a swirl of foam, tiny silly candy-colored gnomes sliding down the bubbles like a slide, bathroom mirror in the background.
1. `1.jpeg` — A magical landscape of shiny white teeth like a row of pearls, tiny candy-colored gnomes happily nibbling on cookie crumbs and jam drops, funny not scary.
2. `2.jpeg` — A bathroom mirror with the tiny sparkly fairy peeking out from behind it, a toothbrush in a cup on the shelf, warm evening light.
3. `3.jpeg` — A toothbrush with pea-sized toothpaste and lots of foam, tiny sugar gnomes sliding down the foam laughing and waving, the fairy conducting like a music teacher, musical notes in the air (no letters).
4. `4.jpeg` — A child's bright smile in a bathroom mirror shown only as sparkling white teeth and reflections, the fairy clapping happily, cozy bedroom visible through the door.

## Amikor megérkezett a kistesó (`kistestver/`)

- `borito.jpeg` — A small child seen from behind leaning over a baby crib, the baby's tiny hand holding the child's finger, soft morning light, very tender mood.
1. `1.jpeg` — A child's drawing-style daydream bubble showing a baby playing football and reading dinosaur books, next to a real sleeping newborn wrapped in a blanket, humorous and warm.
2. `2.jpeg` — A living room with adults gathered around a baby, gifts and flowers, and a small child sitting alone in the corner among toys, seen from behind, slightly sad, gentle colors.
3. `3.jpeg` — Two candles on a low table, the second one being lit from the flame of the first, both flames equally bright, an adult's arm around a small child's shoulders seen from behind.
4. `4.jpeg` — A big sibling's hands showing a picture book to a smiling baby lying on a play mat, a diaper stack nearby, warm cheerful home.
