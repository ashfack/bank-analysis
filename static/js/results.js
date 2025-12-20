
// main.js
import { DetailsService } from './services/DetailsService.js';
import { SavingsView } from './views/SavingsView.js';
import { DetailsView } from './views/DetailsView.js';
import { ModalView } from './views/ModalView.js';
import { SummaryController } from './controllers/SummaryController.js';

function getBreakdownStyleValue() {
  const checked = document.querySelector('input[name="breakdown_style"]:checked');
  return checked ? checked.value : 'standard';
}

document.addEventListener('DOMContentLoaded', () => {
  const savingsView = new SavingsView();
  const detailsView = new DetailsView({ containerSelector: '#details-modal-body' });
  const modalView = new ModalView();
  const detailsService = new DetailsService();

  const controller = new SummaryController({
    detailsService,
    detailsView,
    modalView,
    getBreakdownStyle: getBreakdownStyleValue
  });

  savingsView.init();
  controller.bindSummaryRowClicks('.summary-row');
  controller.bindBreakdownStyleRadios('input[name="breakdown_style"]');
});
