import pandas as pd
from yfinance import Ticker
from datetime import datetime


class Financials:
    """Retrieves the data from YH Finance API and yfinance package"""

    def __init__(self, ticker):
        self.ticker = ticker
        # yfinance
        try:
            self.stock_data = Ticker(self.ticker)
        except KeyError:
            print("Check your stock ticker")
        self.name = self.stock_data.info['shortName']
        self.price = [self.stock_data.info['currentPrice'], self.stock_data.info['currency']]
        self.exchange = self.stock_data.info['exchange']
        self.shares = self.stock_data.info['sharesOutstanding']
        self.report_currency = self.stock_data.info['financialCurrency']
        self.dividends = -int(self.stock_data.get_cashflow().fillna(0).loc['CommonStockDividendPaid'][0]) / self.shares
        self.next_earnings = pd.to_datetime(datetime.fromtimestamp(self.stock_data.info['mostRecentQuarter'])
                                            .strftime("%Y-%m-%d")) + pd.DateOffset(months=6)
        self.balance_sheet = self.get_balance_sheet()
        self.income_statement = self.get_income_statement()

    def get_balance_sheet(self):
        """Returns a DataFrame with selected balance sheet data"""

        balance_sheet = self.stock_data.get_balance_sheet()
        # Start of Cleaning: make sure the data has all the required indexes
        dummy = {"Dummy": [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]}
        dummy_df = pd.DataFrame(dummy, index=['TotalAssets', 'CurrentAssets', 'CurrentLiabilities',
                                              'CurrentDebtAndCapitalLeaseObligation',
                                              'CurrentCapitalLeaseObligation',
                                              'LongTermDebtAndCapitalLeaseObligation',
                                              'LongTermCapitalLeaseObligation',
                                              'TotalEquityGrossMinorityInterest',
                                              'MinorityInterest', 'CashAndCashEquivalents',
                                              'OtherShortTermInvestments', 'InvestmentProperties',
                                              'LongTermEquityInvestment', 'InvestmentinFinancialAssets', 'NetPPE'])
        clean_bs = dummy_df.join(balance_sheet)
        bs_df = clean_bs.loc[['TotalAssets', 'CurrentAssets', 'CurrentLiabilities',
                              'CurrentDebtAndCapitalLeaseObligation',
                              'CurrentCapitalLeaseObligation',
                              'LongTermDebtAndCapitalLeaseObligation',
                              'LongTermCapitalLeaseObligation',
                              'TotalEquityGrossMinorityInterest',
                              'MinorityInterest', 'CashAndCashEquivalents',
                              'OtherShortTermInvestments', 'InvestmentProperties',
                              'LongTermEquityInvestment', 'InvestmentinFinancialAssets', 'NetPPE']]
        bs_df.drop('Dummy', inplace=True, axis=1)
        # Ending of Cleaning: drop the dummy column after join

        return bs_df.fillna(0)

    def get_income_statement(self):
        """Returns a DataFrame with selected income statement data"""

        income_statement = self.stock_data.get_income_stmt()
        # Start of Cleaning: make sure the data has all the required indexes
        dummy = {"Dummy": [None, None, None, None, None]}
        dummy_df = pd.DataFrame(dummy, index=['TotalRevenue', 'CostOfRevenue', 'SellingGeneralAndAdministration',
                                              'InterestExpense', 'NetIncomeCommonStockholders'])
        clean_is = dummy_df.join(income_statement)
        is_df = clean_is.loc[['TotalRevenue', 'CostOfRevenue', 'SellingGeneralAndAdministration',
                              'InterestExpense', 'NetIncomeCommonStockholders']]
        is_df.drop('Dummy', inplace=True, axis=1)
        # Ending of Cleaning: drop the dummy column after join

        return is_df.fillna(0)
