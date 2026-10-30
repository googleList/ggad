(() => {
  const tabs = [...document.querySelectorAll("[data-tool-tab]")];
  const panels = [...document.querySelectorAll("[data-tool-panel]")];
  const links = [...document.querySelectorAll("[data-tool-jump]")];
  if (!tabs.length || tabs.length !== panels.length) return;

  const readLocation = () => {
    let id;
    try {
      id = decodeURIComponent(location.hash.slice(1));
    } catch {
      return null;
    }
    const target = document.getElementById(id);
    const panel = target?.closest("[data-tool-panel]");
    return panels.includes(panel) ? { panel, target, hash: `#${id}` } : null;
  };

  const select = (panel, hash) => {
    const name = panel.dataset.toolPanel;
    tabs.forEach((tab) => {
      const active = tab.dataset.toolTab === name;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
    });
    panels.forEach((item) => {
      item.hidden = item !== panel;
      item.classList.toggle("is-active", item === panel);
    });
    const current = links.find((link) => link.getAttribute("href") === hash)
      || links.find((link) => link.dataset.toolJump === name);
    links.forEach((link) => {
      link.classList.toggle("is-active", link === current);
      if (link === current) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
    current?.scrollIntoView({ block: "nearest", inline: "nearest" });
  };

  const restore = () => {
    const match = readLocation();
    if (match) {
      select(match.panel, match.hash);
      match.target.scrollIntoView({ block: "start" });
    } else if (!location.hash) {
      select(panels[0], "");
    }
  };

  const activate = (tab) => {
    const panel = panels.find((item) => item.id === tab.getAttribute("aria-controls"));
    if (!panel) return;
    const hash = `#${panel.id}`;
    select(panel, hash);
    if (location.hash !== hash) history.pushState(null, "", hash);
  };

  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => activate(tab));
    tab.addEventListener("keydown", (event) => {
      let next;
      if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
      if (event.key === "ArrowLeft") next = (index + tabs.length - 1) % tabs.length;
      if (event.key === "Home") next = 0;
      if (event.key === "End") next = tabs.length - 1;
      if (next === undefined) return;
      event.preventDefault();
      activate(tabs[next]);
      tabs[next].focus();
    });
  });

  links.forEach((link) => {
    link.addEventListener("click", (event) => {
      if (event.button || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      const panel = panels.find((item) => item.dataset.toolPanel === link.dataset.toolJump);
      if (panel) select(panel, link.getAttribute("href"));
      // Keep native fragment navigation, history and modified-click behavior.
    });
  });

  select(panels[0], "");
  document.documentElement.classList.add("tool-navigation-ready");
  restore();
  window.addEventListener("hashchange", restore);
  window.addEventListener("popstate", restore);
})();
