# Bank Analysis Project

From a bank transaction export, we want to generate monthly insights including:

The total salaries received.<br/>
The total expenses incurred.<br/>
The total savings for the month.<br/>
The total savings compared to your theoretical average salary (i.e., excluding on-call bonuses, exceptional increases, etc.).<br/>
The number of expense transactions per month.<br/>
The ability to compute averages, with an option to exclude outliers (such as negative months or months with exceptional circumstances).<br/>
An advanced mode that provides a detailed breakdown for each month by expense category, including both the total amount and the number of transactions per category.<br/>

The implementation is in Python 3.

## Structure


## Exécution
```bash
python main.py
```

## Tests
```bash
pytest --maxfail=1 --disable-warnings -q
```
