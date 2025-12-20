
// views/ModalView.js
import { qs, qsa, addClass, removeClass } from '../utils/dom.js';

export class ModalView {
  constructor({
    modalSelector = '#details-modal',
    dialogSelector = '#details-modal .modal-dialog',
    closeSelectors = '[data-close]',
    hiddenClass = 'hidden',
    bodyOpenClass = 'modal-open'
  } = {}) {
    this.modal = qs(modalSelector);
    this.dialog = qs(dialogSelector);
    this.closeEls = qsa(closeSelectors, this.modal);
    this.hiddenClass = hiddenClass;
    this.bodyOpenClass = bodyOpenClass;
    this.lastFocused = null;

    // Bind handlers
    this.onKeydown = this.onKeydown.bind(this);
    this.onBackdropOrButtonClick = this.onBackdropOrButtonClick.bind(this);
  }

  isOpen() {
    return !this.modal.classList.contains(this.hiddenClass);
  }

  open() {
    if (this.isOpen()) return;

    this.lastFocused = document.activeElement;
    removeClass(this.modal, this.hiddenClass);
    addClass(document.body, this.bodyOpenClass);

    // Focus dialog and trap
    this.dialog.setAttribute('tabindex', '-1');
    this.dialog.focus();

    // Events
    document.addEventListener('keydown', this.onKeydown);
    this.modal.addEventListener('click', this.onBackdropOrButtonClick);
  }

  close() {
    if (!this.isOpen()) return;

    addClass(this.modal, this.hiddenClass);
    removeClass(document.body, this.bodyOpenClass);

    // Remove events
    document.removeEventListener('keydown', this.onKeydown);
    this.modal.removeEventListener('click', this.onBackdropOrButtonClick);

    // Restore focus
    if (this.lastFocused && this.lastFocused.focus) {
      this.lastFocused.focus();
    }
  }

  onKeydown(e) {
    if (e.key === 'Escape') {
      this.close();
      return;
    }
    // Basic focus trap: keep focus within the dialog
    if (e.key === 'Tab') {
      const focusables = qsa(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
        this.dialog
      ).filter(el => el.offsetParent !== null);
      if (focusables.length === 0) return;

      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  }

  onBackdropOrButtonClick(e) {
    const target = e.target;
    if (target.matches('[data-close]')) {
      this.close();
      return;
    }
    // Close when clicking the backdrop (outside dialog)
    if (target.classList.contains('modal-backdrop')) {
      this.close();
    }
  }
}
