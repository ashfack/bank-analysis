
// controllers/SummaryController.js
import { qsa } from '../utils/dom.js';

export class SummaryController {
  constructor({ detailsService, detailsView, modalView, getBreakdownStyle }) {
    this.detailsService = detailsService;
    this.detailsView = detailsView;
    this.modalView = modalView;
    this.getBreakdownStyle = getBreakdownStyle;
    this.currentPeriod = null;
    this.lastTriggerEl = null; // to restore focus via ModalView
  }

  async fetchAndRender(period) {
    const style = this.getBreakdownStyle();
    this.detailsView.showLoading(period, style);
    try {
      const data = await this.detailsService.fetchDetails(period, style);
      this.currentPeriod = period;
      this.detailsView.render(period, data);
    } catch (err) {
      this.detailsView.showError(period, err);
    }
  }

  refreshIfOpen() {
    if (this.currentPeriod && this.modalView.isOpen()) {
      void this.fetchAndRender(this.currentPeriod);
    }
  }

  bindSummaryRowClicks(rowSelector = '.summary-row') {
    const rows = qsa(rowSelector);
    rows.forEach(row => {
      row.addEventListener('click', () => {
        this.lastTriggerEl = row; // give ModalView something to return focus to
        this.modalView.open();
        const period = row.dataset.period;
        void this.fetchAndRender(period);
      });
    });
  }

  bindBreakdownStyleRadios(radioSelector = 'input[name="breakdown_style"]') {
    const radios = qsa(radioSelector);
    radios.forEach(r => {
      r.addEventListener('change', () => this.refreshIfOpen());
    });
  }
}
