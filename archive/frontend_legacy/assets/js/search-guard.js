(function () {
  function installAutofillDecoy() {
    if (!document.body || document.getElementById('__search-guard-decoy')) return;

    const decoy = document.createElement('div');
    decoy.id = '__search-guard-decoy';
    decoy.setAttribute('aria-hidden', 'true');
    decoy.style.cssText = 'position:absolute;left:-9999px;top:-9999px;width:0;height:0;overflow:hidden;pointer-events:none;';
    decoy.innerHTML = [
      '<input type="text" tabindex="-1" autocomplete="username" />',
      '<input type="password" tabindex="-1" autocomplete="current-password" />'
    ].join('');

    document.body.prepend(decoy);
  }

  function clearAutofillValue(input) {
    if (!input || input.dataset.searchGuardTyped === 'true') return;
    if (document.activeElement === input) return;
    if (input.value) {
      input.value = '';
    }
  }

  function unlockInput(input) {
    input.readOnly = false;
  }

  function guardInput(input, index) {
    if (!input || input.dataset.searchGuardReady === 'true') return;

    input.dataset.searchGuardReady = 'true';
    input.autocomplete = 'new-password';
    input.setAttribute('autocapitalize', 'off');
    input.setAttribute('autocorrect', 'off');
    input.setAttribute('spellcheck', 'false');
    input.setAttribute('inputmode', 'search');
    input.setAttribute('data-lpignore', 'true');
    input.setAttribute('data-form-type', 'other');
    input.name = `story_search_${index}_${Math.random().toString(36).slice(2, 10)}`;
    input.readOnly = true;

    ['focus', 'mousedown', 'touchstart', 'keydown'].forEach((eventName) => {
      input.addEventListener(eventName, () => unlockInput(input), { once: true });
    });

    input.addEventListener('input', () => {
      if (document.activeElement === input) {
        input.dataset.searchGuardTyped = 'true';
      }
    });

    [0, 120, 400, 1200].forEach((delay) => {
      window.setTimeout(() => clearAutofillValue(input), delay);
    });
  }

  function initSearchGuard() {
    installAutofillDecoy();
    document
      .querySelectorAll('input[data-search-guard="true"]')
      .forEach((input, index) => guardInput(input, index));
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSearchGuard);
  } else {
    initSearchGuard();
  }
})();
