
export const qs = (selector, root = document) => root.querySelector(selector);
export const qsa = (selector, root = document) => Array.from(root.querySelectorAll(selector));

export const addClass = (el, cls) => el && el.classList.add(cls);
export const removeClass = (el, cls) => el && el.classList.remove(cls);
export const toggleClass = (el, cls, force) => el && el.classList.toggle(cls, force);

export const setHTML = (el, html) => { if (el) el.innerHTML = html; };

export const on = (el, event, handler, options) => el && el.addEventListener(event, handler, options);
