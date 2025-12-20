
// services/DetailsService.js
export class DetailsService {
  /**
   * Fetch details for a given period and breakdown style.
   * Returns a Promise<array>.
   */
  async fetchDetails(period, breakdownStyle) {
    const params = new URLSearchParams({ period, breakdown_style: breakdownStyle });
    const resp = await fetch(`/details?${params.toString()}`);
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }
    return resp.json();
  }
}
