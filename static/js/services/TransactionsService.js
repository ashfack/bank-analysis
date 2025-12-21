
// services/TransactionsService.js
export class TransactionsService {
  /**
   * Fetch transactions for a period+label+kind.
   * Returns Promise<array>.
   */
  async fetchTransactions({ period, label, kind }) {
    const params = new URLSearchParams({ period, label, kind });
    const resp = await fetch(`/transactions?${params.toString()}`);
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }
    return resp.json();
  }
}
