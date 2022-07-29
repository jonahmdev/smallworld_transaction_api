import json
from datetime import datetime

account_balance_file = 'balances.json'
pending_transactions_file = 'pending_transactions.json'
transactions_file = 'transactions.json'


# data get and write functions
def get_balance_data():
    with open(account_balance_file, 'r') as balances:
        balance_data = json.loads(balances.read())
    return balance_data

def write_balance_data(balance_data):
    with open(account_balance_file, 'w') as balances:
        balances.write(json.dumps(balance_data, indent=4))

def get_pending_transactions_data():
    with open(pending_transactions_file, 'r') as pending_transactions:
        pending_transactions_data = json.loads(pending_transactions.read())
    return pending_transactions_data

def write_pending_transactions_data(pending_transactions_data):
    with open(pending_transactions_file, 'w') as pending_transactions:
        pending_transactions.write(json.dumps(pending_transactions_data, indent=4))

# helper function to remove list items by indices
def remove_by_index(input_list, keys):
    indices = sorted(keys, reverse=True)
    for i in indices:
        if i < len(input_list):
            input_list.pop(i)
    
    return input_list

# account specific get functions
def get_pending_transactions(account_id):
    pending_amt = 0
    with open(pending_transactions_file, 'r') as pending_file:
        pending_transactions_dict = json.loads(pending_file.read())
    if account_pending_transactions := pending_transactions_dict.get(account_id, None):
        debit_transactions = account_pending_transactions.get('debit', None)
        credit_transactions = account_pending_transactions.get('credit', None)
        if debit_transactions:
            for debit_transaction in debit_transactions:
                pending_amt -= debit_transaction.get('remaining')
        if credit_transactions:
            for credit_transaction in credit_transactions:
                pending_amt += credit_transaction.get('remaining')
    return pending_amt

def get_balance(account_id):
    account_balance_dict = get_balance_data()
    return account_balance_dict.get(account_id, None)

def get_net_balance(account_id):
    official_balance = get_balance(account_id)
    pending_amount = get_pending_transactions(account_id)
    net_balance = official_balance + pending_amount
    return net_balance

def account_has_funds(account_id, amount):
    net_balance = get_net_balance(account_id)
    new_balance = net_balance - amount
    return new_balance >= 0


# more complex functions to perform transactions by checking, adding, modifying
def add_transaction_to_ledger(debit_account, credit_account, amount, timestamp):
    transaction_dict = {
        'creditWalletId': credit_account,
        'debitWalletId': debit_account,
        'points': amount,
        'timestamp': str(timestamp)
    }
    with open(transactions_file, 'r') as transactions:
        transactions_data = json.loads(transactions.read())
    transactions_data['transactions'].append(transaction_dict)
    with open(transactions_file, 'w') as transactions:
        transactions.write(json.dumps(transactions_data, indent=4))

def add_pending_transaction(account_id, alt_account, amount, type, timestamp):
    pending_transaction = {
        'points': amount,
        'timestamp': str(timestamp),
        'remaining': amount
    }
    if type == 'debit':
        pending_transaction['credit_account'] = alt_account
    elif type == 'credit':
        pending_transaction['debit_account'] = alt_account
    with open(pending_transactions_file, 'r') as pending_transactions:
        pending_transactions_data = json.loads(pending_transactions.read())
    if account_pending_transactions := pending_transactions_data.get(account_id, None):
        if account_pending_transactions_type := account_pending_transactions.get(type, None):
            account_pending_transactions_type.append(pending_transaction)
            pending_transactions_data[account_id][type] = account_pending_transactions_type
        else:
            pending_transactions_data[account_id][type] = [pending_transaction]
    else:
        pending_transactions_data[account_id] = {
            type: [
                pending_transaction
            ]
        }
    with open(pending_transactions_file, 'w') as pending_transactions:
        pending_transactions.write(json.dumps(pending_transactions_data, indent=4))

def add_pending_transactions_to_ledger(debit_account, credit_account, amount, timestamp):
    # add credit pending transaction
    add_pending_transaction(debit_account, credit_account, amount, 'credit', timestamp)
    # add debit pending transaction
    add_pending_transaction(credit_account, debit_account, amount, 'debit', timestamp)

def add_transaction(debit_account, credit_account, amount):
    timestamp = datetime.now()
    # check debit_account and amount
    if account_has_funds(credit_account, amount):
        # add transaction to ledger
        add_transaction_to_ledger(debit_account, credit_account, amount, timestamp)
        # add pending transactions to pending transactions ledgers
        add_pending_transactions_to_ledger(debit_account, credit_account, amount, timestamp)
        return True
    else:
        return False

def add_spend_transaction_to_ledger(account, amount, timestamp):
    transaction_dict = {
        'creditWalletId': account,
        'points': amount,
        'timestamp': str(timestamp)
    }
    with open(transactions_file, 'r') as transactions:
        transactions_data = json.loads(transactions.read())
    transactions_data['transactions'].append(transaction_dict)
    with open(transactions_file, 'w') as transactions:
        transactions.write(json.dumps(transactions_data, indent=4))

def deduct_balance(account, amount):
    balance_data = get_balance_data()
    balance_data[account] -= amount
    write_balance_data(balance_data)

def spend_points(account_id, amount):
    timestamp = datetime.now()
    wallets_deducted = {}

    # check if account has funds to spend
    if account_has_funds(account_id, amount):
        pending_transactions_data = get_pending_transactions_data()
        account_transactions = pending_transactions_data.get(account_id)
        credit_transactions = account_transactions.get('credit')
        
        remaining_amount = amount
        keys_to_pop = []

        # for each credit transaction from oldest to newest,
        # remove pending transactions and deduct them from balance 
        # deduct remaining amount from pending transactions that will not be fully deducted
        for key, val in enumerate(credit_transactions):
            if remaining_amount > 0:
                transaction_remaining = val.get('remaining')
                debit_account = val.get('debit_account')
                
                if transaction_remaining <= remaining_amount:
                    transaction_amt = transaction_remaining
                    keys_to_pop.append(key)
                else:
                    transaction_amt = remaining_amount
                    credit_transactions[key]['remaining'] -= transaction_amt
                
                remaining_amount -= transaction_amt
                add_spend_transaction_to_ledger(debit_account, transaction_amt, timestamp)
                deduct_balance(debit_account, transaction_amt)
                    
                if wallets_deducted.get(debit_account, None):
                    wallets_deducted[debit_account] += transaction_amt
                else:
                    wallets_deducted[debit_account] = transaction_amt

        credit_transactions = remove_by_index(credit_transactions, keys_to_pop)
        pending_transactions_data[account_id]['credit'] = credit_transactions

        write_pending_transactions_data(pending_transactions_data)
        
        response = [] 
        for key in wallets_deducted.keys():
            response.append(
                {
                    'creditWalletId': key, 
                    'points': wallets_deducted[key]
                }
            )
        return response
        
    else:
        return False

         