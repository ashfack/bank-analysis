
// controllers/TransactionsController.js
export class TransactionsController {
  constructor({ transactionsService, transactionsView, transactionsModalView, getCurrentPeriod }) {
    this.transactionsService = transactionsService;
    this.transactionsView = transactionsView;
    this.transactionsModalView = transactionsModalView;
    this.getCurrentPeriod = getCurrentPeriod;
  }

  bindTo(detailsView) {
    const container = detailsView.container;

    container.addEventListener('click', (e) => {
      const row = e.target.closest('.details-row');
      if (!row) return;
      this.openAndFetchFromRow(row);
    });

    container.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        const row = e.target.closest('.details-row');
        if (!row) return;
        e.preventDefault();
        this.openAndFetchFromRow(row);
      }
    });
  }

  async openAndFetchFromRow(row) {
    const period = this.getCurrentPeriod();
    const label = row.dataset.label;
    const kind  = row.dataset.kind;

    this.transactionsModalView.open();
    this.transactionsView.showLoading({ period, label, kind });

    try {
      const list = await this.transactionsService.fetchTransactions({ period, label, kind });
      this.transactionsView.render(list);
    } catch (err) {
      this.transactionsView.showError(err);
    }
  }
}
