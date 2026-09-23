// Mesekatalógus témaszűrővel. Használja: index.html (böngészés) és app.html (választás).
export function renderCatalog({ box, chips, data, onPick, selectedId }) {
  let theme = null;

  const el = (tag, props = {}, ...kids) => {
    const e = Object.assign(document.createElement(tag), props);
    e.append(...kids);
    return e;
  };

  function drawChips() {
    chips.innerHTML = "";
    const all = [{ id: null, label: "Az összes" }, ...data.themes];
    for (const t of all) {
      const b = el("button", { type: "button", className: "chip", textContent: t.label });
      b.setAttribute("aria-pressed", String(theme === t.id));
      if (t.description) b.title = t.description;
      b.addEventListener("click", () => { theme = t.id; drawChips(); drawList(); });
      chips.append(b);
    }
  }

  function cover(s) {
    if (s.cover) return el("img", { src: s.cover, alt: "", loading: "lazy" });
    const ph = el("div", { className: "cover-ph" });
    ph.innerHTML = '<svg viewBox="0 0 40 40" aria-hidden="true"><path d="M27 4a17 17 0 1 0 9 26A14 14 0 0 1 27 4z"/></svg>';
    return ph;
  }

  function drawList() {
    box.innerHTML = "";
    const list = data.stories.filter((s) => !theme || s.themes.includes(theme));
    const labels = Object.fromEntries(data.themes.map((t) => [t.id, t.label]));
    for (const s of list) {
      const tag = onPick ? "button" : "article";
      const card = el(tag, { className: "story" });
      if (onPick) {
        card.type = "button";
        card.setAttribute("role", "radio");
        card.setAttribute("aria-checked", String(selectedId?.() === s.id));
        card.addEventListener("click", () => onPick(s));
      }
      const meta = [s.age, ...s.themes.map((t) => labels[t]).filter(Boolean)].join(" · ");
      card.append(cover(s), el("div", {},
        el("h3", { textContent: s.title }),
        el("p", { className: "age", textContent: meta }),
        el("p", { textContent: s.description })));
      box.append(card);
    }
  }

  drawChips();
  drawList();
  return { redraw: drawList };
}
