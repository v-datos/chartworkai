(() => {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  const activateSearchFallback = () => {
    const input = document.querySelector("[data-md-component='search-query']");
    const result = document.querySelector("[data-md-component='search-result']");
    if (!input || !result || input.dataset.fallbackSearch === "active") return;

    input.dataset.fallbackSearch = "active";
    const meta = result.querySelector(".md-search-result__meta");
    const list = result.querySelector(".md-search-result__list");
    const config = JSON.parse(document.querySelector("#__config")?.textContent || "{}");
    const base = new URL(`${config.base || "."}/`, window.location.href);
    let index;
    const getIndex = () => {
      index ||= fetch(new URL("search/search_index.json", base)).then((response) => {
        if (!response.ok) throw new Error(`search index returned ${response.status}`);
        return response.json();
      });
      return index;
    };

    const plainText = (html) => {
      const container = document.createElement("div");
      container.innerHTML = html;
      return container.textContent.replace(/\s+/g, " ").trim();
    };

    const render = async () => {
      const query = input.value.trim().toLowerCase();
      list.replaceChildren();
      if (!query) {
        meta.textContent = "Type to start searching";
        return;
      }

      try {
        const data = await getIndex();
        const matches = data.docs
          .filter((doc) => `${doc.title} ${plainText(doc.text)}`.toLowerCase().includes(query))
          .slice(0, 12);
        meta.textContent = `${matches.length} matching document${matches.length === 1 ? "" : "s"}`;

        matches.forEach((doc) => {
          const item = document.createElement("li");
          item.className = "md-search-result__item";
          const link = document.createElement("a");
          link.className = "md-search-result__link";
          link.href = new URL(doc.location, base);
          const article = document.createElement("article");
          article.className = "md-search-result__article";
          const title = document.createElement("h1");
          title.className = "md-search-result__title";
          title.textContent = doc.title;
          const excerpt = document.createElement("p");
          excerpt.className = "md-search-result__teaser";
          excerpt.textContent = plainText(doc.text).slice(0, 180);
          article.append(title, excerpt);
          link.append(article);
          item.append(link);
          list.append(item);
        });
      } catch (_error) {
        meta.textContent = "Search is temporarily unavailable";
      }
    };

    const deferToNativeSearch = () => {
      window.setTimeout(() => {
        const nativeSearchResponded =
          list.children.length > 0 || !meta.textContent.includes("Type to start searching");
        if (!nativeSearchResponded) render();
      }, 350);
    };

    input.addEventListener("input", deferToNativeSearch);
    input.form?.addEventListener("reset", () => window.setTimeout(render));
  };

  const activateReveals = () => {
    const elements = document.querySelectorAll(
      ".md-typeset > h2:not(.cw-reveal), .md-typeset > table:not(.cw-reveal), .md-typeset > .admonition:not(.cw-reveal)",
    );
    if (reduceMotion.matches || !("IntersectionObserver" in window)) {
      elements.forEach((element) => element.classList.add("cw-reveal--visible"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("cw-reveal--visible");
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -8%", threshold: 0.08 },
    );

    elements.forEach((element) => {
      element.classList.add("cw-reveal");
      observer.observe(element);
    });
  };

  const activate = () => {
    activateReveals();
    activateSearchFallback();
  };

  if (typeof document$ !== "undefined") {
    document$.subscribe(activate);
    activate();
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", activate, { once: true });
    window.addEventListener("load", activate, { once: true });
  } else {
    activate();
  }
})();
