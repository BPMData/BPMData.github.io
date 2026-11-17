/* Light/dark theme: follows the device until the visitor clicks the sun or moon,
   then remembers their choice on this browser. Loaded in <head> so the saved
   theme applies before the page paints. */
(function () {
  var KEY = 'bpmdata-theme';
  var root = document.documentElement;
  var media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

  function saved() {
    try { var v = localStorage.getItem(KEY); return v === 'light' || v === 'dark' ? v : null; }
    catch (e) { return null; }
  }
  function current() {
    return root.getAttribute('data-theme') || (media && media.matches ? 'dark' : 'light');
  }
  function label(btn) {
    btn.setAttribute('aria-label', current() === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
    btn.title = btn.getAttribute('aria-label');
  }

  var s = saved();
  if (s) root.setAttribute('data-theme', s);

  document.addEventListener('DOMContentLoaded', function () {
    var btns = document.querySelectorAll('[data-theme-toggle]');
    Array.prototype.forEach.call(btns, function (btn) {
      label(btn);
      btn.addEventListener('click', function () {
        var next = current() === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-theme', next);
        try { localStorage.setItem(KEY, next); } catch (e) {}
        Array.prototype.forEach.call(btns, label);
      });
    });
    if (media && media.addEventListener) {
      media.addEventListener('change', function () { Array.prototype.forEach.call(btns, label); });
    }
  });
})();
