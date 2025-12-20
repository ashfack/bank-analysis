
// views/DetailsView.js
import { qs, setHTML } from '../utils/dom.js';

export class DetailsView {
  constructor({ containerSelector = '#details-modal-body' } = {}) {
    this.container = qs(containerSelector);
  }

  showLoading(period, breakdownStyle) {
    setHTML(this.container, `<p>Loading breakdown for <strong>${period}</strong> (${breakdownStyle})...</p>`);
  }

  showError(period, err) {
    setHTML(this.container, `
      <p>
        Unable to load details for <strong>${period}</strong>.
        ${err ? ` <em>${String(err)}</em>` : ''}
      </p>
    `);
  }

  showEmpty() {
    setHTML(this.container, '<p>No details available for this period.</p>');
  }

  render(period, data) {
    if (!data || data.length === 0) {
      this.showEmpty();
      return;
    }
    let html = `<h3>Expense Breakdown for ${period}</h3>`;
    html += `<table>
      <thead><tr><th>Category</th><th>Total</th><th># Ops</th></tr></thead>
      <tbody>`;
    for (const item of data) {
      const total = typeof item.total === 'number' ? item.total.toFixed(2) : item.total;
      const nbOps = item.nb_operations ?? '';
      const category = item.category_parent ?? '';
      html += `<tr><td>${category}</td><td>${total}</td><td>${nbOps}</td></tr>`;
    }
    html += `</tbody></table>`;
    setHTML(this.container, html);
  }
}
