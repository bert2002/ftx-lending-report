# ftx-lending-report

Create FTX lending report

# Configuration

Create a FTX account on the account and create an API pair. Add the new credentials to `ftx-lending-report.py`:

```
FTX_API_KEY=''
FTX_SECRET=''
```
Last step is to run the script:

```
$ ./ftx-lending-report.py
USDT was lent last at 2021-01-22T18:00:00+00:00 at 0.000010 with total 6428.261073. The current rate is 0.000005 and your offer is 0.000006
```

# Limitations

- only works when one coin is lent (see line 80)  
- hard coded USDT
