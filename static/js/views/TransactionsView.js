
// views/TransactionsView.js
import { qs, setHTML } from '../utils/dom.js';

export class TransactionsView {
  constructor({ containerSelector = '#transactions-modal-body' } = {}) {
    this.container = qs(containerSelector);
  }

  showLoading({ period, label, kind }) {
    setHTML(this.container, `
      Loading transactions for ${period} [${kind}:${label}]...
    `);
  }

  showError(err) {
    setHTML(this.container, `
      Unable to load transactions. ${err ? String(err) : ''}
    `);
  }

  showEmpty() {
    setHTML(this.container, 'No transactions for this selection.');
  }

  render(list) {
    if (!list || list.length === 0) {
      this.showEmpty();
      return;
    }

    let html = `
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Message</th>
            <th>Amount</th>
            <th>Supplier</th>
          </tr>
        </thead>
        <tbody>
    `;
    for (const tx of list) {
      const date   = tx.date ?? '';
      const message  = tx.message ?? '';
      const category   = tx.category ?? '';
      const amount = typeof tx.amount === 'number'
        ? tx.amount.toFixed(2)
        : (tx.amount ?? '');
      const supplier   = tx.supplier ?? '';
      html += `
        <tr>
          <td>${date}</td>
          <td>${message}</td>
          <td>${amount}</td>
          <td>${supplier}</td>
        </tr>
      `;
    }
    html += `</tbody></table>`;
    setHTML(this.container, html);
  }
}
