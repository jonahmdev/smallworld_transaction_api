from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
import uvicorn
from transaction_util import (
    get_balance, 
    get_pending_transactions, 
    add_transaction, 
    spend_points,
    get_balance_data
)
app = Starlette()

@app.route('/balances', methods=['GET'])
async def get_all_balances(request):
    response = get_balance_data()
    return JSONResponse(response)

@app.route('/balance/{account_id:str}', methods=['GET'])
async def get_account_balance(request):
    account_id = request.path_params['account_id']
    account_balance = get_balance(account_id)
    if account_balance == None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    pending_transactions = get_pending_transactions(account_id)

    return JSONResponse({
        'account_balance': account_balance,
        'pending_transactions': pending_transactions
    })

@app.route('/transaction/{debit_account:str}/{credit_account:str}', methods=['POST'])
async def post_transaction(request):
    debit_account = request.path_params['debit_account']
    credit_account = request.path_params['credit_account']
    amt = int(request.query_params.get('amt'))
    for account in [debit_account, credit_account]:
        if get_balance(account) == None:
            raise HTTPException(status_code=500, detail=f"Account Does Not Exist! ({account})\n")
    if not add_transaction(debit_account, credit_account, amt):
        raise HTTPException(status_code=500, detail="Insufficient Funds in Credit Account!\n")
    return JSONResponse({
        'result': 'transaction processed'
    })
    
@app.route('/spend/{account_id:str}', methods=['POST'])
async def post_spend_points(request):
    account_id = request.path_params['account_id']
    amt = int(request.query_params.get('amt'))
    if get_balance(account_id) == None:
        raise HTTPException(status_code=500, detail="Account Does Not Exist!\n")
    if response := spend_points(account_id, amt):
        return JSONResponse({
            'result': response
        })
    else:
        raise HTTPException(status_code=500, detail="Insufficient Funds in Account!\n")

if __name__ == '__main__':
    uvicorn.run(app='transaction_api:app', port=5000, log_level="info", reload=True)