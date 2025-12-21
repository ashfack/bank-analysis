
import { DetailsService } from './services/DetailsService.js';
import { SavingsView } from './views/SavingsView.js';
import { DetailsView } from './views/DetailsView.js';
import { ModalView } from './views/ModalView.js';
import { SummaryController } from './controllers/SummaryController.js';
import { TransactionsService } from './services/TransactionsService.js';
import { TransactionsView } from './views/TransactionsView.js';
import { TransactionsController } from './controllers/TransactionsController.js'; // étape 5

function getBreakdownStyleValue() {
  const checked = document.querySelector('input[name="breakdown_style"]:checked');
  return checked ? checked.value : 'standard';
}

document.addEventListener('DOMContentLoaded', () => {
  const savingsView = new SavingsView();
  const detailsView = new DetailsView({ containerSelector: '#details-modal-body' });
  const modalView = new ModalView();

  const transactionsModalView = new ModalView({
    modalSelector: '#transactions-modal',
    dialogSelector: '#transactions-modal .modal-dialog'
  });

  const detailsService = new DetailsService();
  const transactionsService = new TransactionsService();

  const summaryController = new SummaryController({
    detailsService,
    detailsView,
    modalView,
    getBreakdownStyle: getBreakdownStyleValue
  });


   const transactionsView = new TransactionsView({ containerSelector: '#transactions-modal-body' });
   const transactionsController = new TransactionsController({
     transactionsService,
     transactionsView,
     transactionsModalView,
     getCurrentPeriod: () => summaryController.currentPeriod
   });

  transactionsController.bindTo(detailsView);

  savingsView.init();
  summaryController.bindSummaryRowClicks('.summary-row');
  summaryController.bindBreakdownStyleRadios('input[name="breakdown_style"]');

});
