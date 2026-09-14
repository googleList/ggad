document.documentElement.classList.add("js");

const revealItems = document.querySelectorAll("[data-reveal]");
const showIfInView = (item) => {
  const rect = item.getBoundingClientRect();
  if (rect.top < window.innerHeight * 1.08) {
    item.classList.add("is-visible");
    return true;
  }
  return false;
};

if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.14 }
  );

  revealItems.forEach((item) => {
    if (!showIfInView(item)) {
      observer.observe(item);
    }
  });
} else {
  revealItems.forEach((item) => item.classList.add("is-visible"));
}

const articleCards = document.querySelectorAll("[data-article-card]");
const articleCategoryButtons = document.querySelectorAll("[data-article-category-button]");
const articlePagination = document.querySelector(".pagination");
const articleStatus = document.querySelector("[data-article-status]");
const articlePageSize = 6;
let activeArticleCategory = "all";
let activeArticlePage = 1;

const getCategoryLabel = () => {
  const activeButton = Array.from(articleCategoryButtons).find(
    (button) => button.dataset.articleCategory === activeArticleCategory
  );
  return activeButton ? activeButton.textContent.trim() : "全部";
};

const getFilteredArticleCards = () =>
  Array.from(articleCards).filter((card) => {
    const category = card.dataset.articleCategory || "sem";
    return activeArticleCategory === "all" || category === activeArticleCategory;
  });

const renderArticlePagination = (totalPages) => {
  if (!articlePagination) {
    return;
  }

  articlePagination.innerHTML = "";

  const appendButton = (label, page, options = {}) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.dataset.articlePageButton = "";
    button.dataset.articlePage = String(page);
    button.disabled = Boolean(options.disabled);
    button.classList.toggle("is-active", page === activeArticlePage && !options.control);
    if (page === activeArticlePage && !options.control) {
      button.setAttribute("aria-current", "page");
    }
    button.addEventListener("click", () => {
      activeArticlePage = page;
      showArticles();
    });
    articlePagination.appendChild(button);
  };

  const appendGap = () => {
    const gap = document.createElement("span");
    gap.textContent = "...";
    gap.setAttribute("aria-hidden", "true");
    articlePagination.appendChild(gap);
  };

  appendButton("上一页", Math.max(1, activeArticlePage - 1), {
    control: true,
    disabled: activeArticlePage === 1
  });

  const pages = [];
  for (let page = 1; page <= totalPages; page += 1) {
    if (
      page === 1 ||
      page === totalPages ||
      Math.abs(page - activeArticlePage) <= 1 ||
      (activeArticlePage <= 3 && page <= 4) ||
      (activeArticlePage >= totalPages - 2 && page >= totalPages - 3)
    ) {
      pages.push(page);
    }
  }

  pages.forEach((page, index) => {
    if (index > 0 && page - pages[index - 1] > 1) {
      appendGap();
    }
    appendButton(String(page), page);
  });

  appendButton("下一页", Math.min(totalPages, activeArticlePage + 1), {
    control: true,
    disabled: activeArticlePage === totalPages
  });
};

const showArticles = () => {
  const filteredCards = getFilteredArticleCards();
  const totalPages = Math.max(1, Math.ceil(filteredCards.length / articlePageSize));
  activeArticlePage = Math.min(activeArticlePage, totalPages);
  const start = (activeArticlePage - 1) * articlePageSize;
  const pageCards = filteredCards.slice(start, start + articlePageSize);

  articleCards.forEach((card) => {
    card.hidden = true;
  });
  pageCards.forEach((card) => {
    card.hidden = false;
  });

  articleCategoryButtons.forEach((button) => {
    const isActive = button.dataset.articleCategory === activeArticleCategory;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });

  renderArticlePagination(totalPages);

  if (articleStatus) {
    articleStatus.textContent = `${getCategoryLabel()} · 第 ${activeArticlePage} 页，共 ${totalPages} 页 · ${filteredCards.length} 篇`;
  }
};

if (articleCards.length) {
  articleCategoryButtons.forEach((button) => {
    button.addEventListener("click", () => {
      activeArticleCategory = button.dataset.articleCategory || "all";
      activeArticlePage = 1;
      showArticles();
    });
  });

  showArticles();
}

const toolTabButtons = document.querySelectorAll("[data-tool-tab]");
const toolTabPanels = document.querySelectorAll("[data-tool-panel]");
const toolSideLinks = document.querySelectorAll("[data-tool-jump]");

const setActiveToolSideLink = (hash) => {
  toolSideLinks.forEach((link) => {
    link.classList.toggle("is-active", link.getAttribute("href") === hash);
  });
};

const showToolPanel = (target) => {
  toolTabButtons.forEach((button) => {
    const isActive = button.dataset.toolTab === target;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });

  toolTabPanels.forEach((panel) => {
    const isActive = panel.dataset.toolPanel === target;
    panel.classList.toggle("is-active", isActive);
    panel.hidden = !isActive;
  });
};

if (toolTabButtons.length && toolTabPanels.length) {
  toolTabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      showToolPanel(button.dataset.toolTab || "ai");
    });
  });
}

if (toolSideLinks.length) {
  toolSideLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const targetPanel = link.dataset.toolJump || "ai";
      const hash = link.getAttribute("href") || "";
      const target = hash ? document.querySelector(hash) : null;

      showToolPanel(targetPanel);
      setActiveToolSideLink(hash);

      if (target) {
        window.requestAnimationFrame(() => {
          target.scrollIntoView({ behavior: "smooth", block: "start" });
          history.replaceState(null, "", hash);
        });
      }
    });
  });

  const initialSideLink = Array.from(toolSideLinks).find(
    (link) => link.getAttribute("href") === window.location.hash
  );
  if (initialSideLink) {
    showToolPanel(initialSideLink.dataset.toolJump || "ai");
    setActiveToolSideLink(window.location.hash);
  }
}

const navDropdowns = document.querySelectorAll(".nav-dropdown");

const closeNavDropdowns = (exceptDropdown) => {
  navDropdowns.forEach((dropdown) => {
    if (dropdown !== exceptDropdown) {
      dropdown.classList.remove("is-open");
      const button = dropdown.querySelector(".nav-drop-toggle");
      if (button) {
        button.setAttribute("aria-expanded", "false");
      }
    }
  });
};

navDropdowns.forEach((dropdown) => {
  const button = dropdown.querySelector(".nav-drop-toggle");
  if (!button) {
    return;
  }

  dropdown.addEventListener("click", (event) => {
    event.stopPropagation();
  });

  button.addEventListener("click", (event) => {
    event.stopPropagation();
    const isOpen = dropdown.classList.toggle("is-open");
    button.setAttribute("aria-expanded", String(isOpen));
    closeNavDropdowns(dropdown);
  });
});

document.addEventListener("click", () => closeNavDropdowns());
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeNavDropdowns();
  }
});
