/* Shared renderer: both practice and lecture library use the same SQLite-exported lecture record. */
(function () {
  "use strict";
  const sections = [
    ["直感", "intuition"], ["定義・主要公式", "definition"], ["導出・根拠", "derivation"],
    ["具体例", "example"], ["成立条件", "conditions"], ["典型ミス", "pitfalls"],
    ["試験での判断基準", "exam_criteria"]
  ];
  const escape = value => String(value == null ? "" : value).replace(/[&<>"']/g, c =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const mathPattern = /\\\[([\s\S]*?)\\\]|\\\(([\s\S]*?)\\\)|\$\$([\s\S]*?)\$\$/g;
  function textBlocks(source) {
    const src = String(source || "");
    let html = "", index = 0, found;
    const re = new RegExp(mathPattern.source, "g");
    while ((found = re.exec(src)) !== null) {
      const prose = src.slice(index, found.index).trim();
      if (prose) html += '<p class="lecture-prose">' + escape(prose) + '</p>';
      const tex = found[1] ?? found[2] ?? found[3];
      html += '<div class="lecture-equation" data-lecture-tex="' + escape(tex) + '"></div>';
      index = re.lastIndex;
    }
    const remaining = src.slice(index).trim();
    if (remaining) html += '<p class="lecture-prose">' + escape(remaining) + '</p>';
    return html;
  }
  function markup(lecture) {
    if (!lecture) return '<div class="lecture-empty">講義データを取得できません。</div>';
    let html = '<div class="lecture-body">';
    if (lecture.formula_latex) {
      html += '<div class="lecture-primary-formula"><div class="lecture-equation" data-lecture-tex="' +
        escape(lecture.formula_latex) + '"></div></div>';
    }
    for (const [label, field] of sections) {
      if (!lecture[field]) continue;
      html += '<section class="lecture-section"><h3>' + escape(label) +
        '</h3>' + textBlocks(lecture[field]) + '</section>';
    }
    html += '</div>';
    return html;
  }
  function renderMath(root) {
    if (!root) return;
    root.querySelectorAll('[data-lecture-tex]').forEach(el => {
      const tex = el.dataset.lectureTex;
      if (!window.katex) {
        el.textContent = tex;
        el.classList.add("lecture-math-unavailable");
        return;
      }
      try {
        window.katex.render(tex, el, {displayMode:true, throwOnError:true, strict:"ignore"});
      } catch (error) {
        el.textContent = "数式を表示できません: " + tex;
        el.classList.add("lecture-math-unavailable");
        console.error("KaTeX lecture error", error);
      }
    });
  }
  window.LectureView = { markup, renderMath, textBlocks };
})();
