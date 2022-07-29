# Transaction API

## How to install

Enable execution on `install.sh` and `source` it to create the virtual environment and install necessary packages. 

## How to run 

Enable execution on `run.sh` and run it. In a separate terminal window, run the API calls. There are examples of calls in a walkthrough in `walkthrough.txt`. To see how things are operating, you may view `transactions.json`, `pending_transactions.json`, and `balances.json`.

## Background

I figured that in order to keep track of the transactions that were 'spent' in order, I would need to keep a ledger of debits and credits for each account. I decided to make those transactions 'pending' until they were spent. This may or may not work with how it was intended, but since we are not working with a database, I decided it would be best to only keep the pending transactions around while we need them. 

The pending transactions do not ever add to the official balances, but they are kept track of as long as they are pending, and until the points themselves are spent.

This would assume that there is a separate system for 'issuing' points, where users can actually add to their offical balances, but that is not included in this project. 

