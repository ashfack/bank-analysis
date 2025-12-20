
// views/SavingsView.js
import { qs, qsa, toggleClass } from '../utils/dom.js';

export class SavingsView {
  constructor({
    headerTotalSelector = '.savings-header.savings-total',
    headerVsTheoSelector = '.savings-header.savings-vs-theoretical',
    cellsTotalSelector = '.savings-cell.savings-total',
    cellsVsTheoSelector = '.savings-cell.savings-vs-theoretical',
    savingsModeRadioSelector = 'input[name="savings_mode"]',
    hiddenClass = 'hidden'
  } = {}) {
    this.headerTotal = qs(headerTotalSelector);
    this.headerVsTheo = qs(headerVsTheoSelector);
    this.cellsTotal = qsa(cellsTotalSelector);
    this.cellsVsTheo = qsa(cellsVsTheoSelector);
    this.radios = qsa(savingsModeRadioSelector);
    this.hiddenClass = hiddenClass;
  }

  getMode() {
    const checked = document.querySelector('input[name="savings_mode"]:checked');
    return checked ? checked.value : 'total';
  }

  update() {
    const showTotal = this.getMode() === 'total';
    toggleClass(this.headerTotal, this.hiddenClass, !showTotal);
    toggleClass(this.headerVsTheo, this.hiddenClass, showTotal);
    this.cellsTotal.forEach(td => toggleClass(td, this.hiddenClass, !showTotal));
    this.cellsVsTheo.forEach(td => toggleClass(td, this.hiddenClass, showTotal));
  }

  bind() {
    this.radios.forEach(r => r.addEventListener('change', () => this.update()));
  }

  init() {
    // Keep page consistent with default radio; your HTML already pre-hides vs_theoretical
    this.update();
    this.bind();
  }
}

