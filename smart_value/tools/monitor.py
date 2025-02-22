from datetime import datetime
import xlwings
import pathlib
import re
import smart_value.stock
import smart_value.tools.stock_model
import smart_value.financial_data.riskfree_rate


def read_opportunity(opportunities_path):
    """Read all the opportunities at the opportunities_path.

    :param opportunities_path: path of the model in the opportunities' folder
    :return: an Asset object
    """

    opportunity = None
    r_stock = re.compile(".*_Stock_Valuation_v")
    # get the formula results using xlwings because openpyxl doesn't evaluate formula
    with xlwings.App(visible=False) as app:
        xl_book = app.books.open(opportunities_path)
        dash_sheet = xl_book.sheets('Dashboard')
        # Update the models first in the opportunities folder
        if r_stock.match(str(opportunities_path)):
            company = smart_value.stock.Stock(dash_sheet.range('C3').value, "yf")
            smart_value.tools.stock_model.update_dashboard(dash_sheet, company)
            xl_book.save(opportunities_path)  # xls must be saved to update the values
            opportunity = read_stock(dash_sheet)
        else:
            pass  # to be implemented
        xl_book.close()
    return opportunity


def read_stock(dash_sheet):
    """Read the opportunity from the models in the opportunities' folder.

    :param dash_sheet: xlwings object of the model
    :return: a Stock object
    """

    company = smart_value.stock.Stock(dash_sheet.range('C3').value)
    company.name = dash_sheet.range('C4').value
    company.exchange = dash_sheet.range('I3').value
    company.price = dash_sheet.range('I4').value
    company.price_currency = dash_sheet.range('J4').value
    company.ideal_price = dash_sheet.range('B19').value
    company.current_irr = dash_sheet.range('G17').value
    company.risk_premium = dash_sheet.range('H17').value
    company.is_updated = dash_sheet.range('E6').value
    company.periodic_payment = dash_sheet.range('I13').value
    company.last_fy = dash_sheet.range('C6').value
    company.invest_horizon = 3  # default 3 years holding period for stocks
    return company


class Monitor:
    """A Monitor with many opportunities"""

    def __init__(self):
        self.opportunities = []
        self.load_opportunities()
        self.us_riskfree = smart_value.financial_data.riskfree_rate.risk_free_rate("us")
        self.cn_riskfree = smart_value.financial_data.riskfree_rate.risk_free_rate("cn")

    # Todo: Analysis using Pandas

    def load_opportunities(self):
        """Load the asset information from the opportunities folder"""

        # Copy the latest Valuation template
        opportunities_folder_path = pathlib.Path.cwd().resolve() / 'financial_models' / 'Opportunities'
        r = re.compile(".*Valuation_v")

        try:
            if pathlib.Path(opportunities_folder_path).exists():
                path_list = [val_file_path for val_file_path in opportunities_folder_path.iterdir()
                             if opportunities_folder_path.is_dir() and val_file_path.is_file()]
                opportunities_path_list = list(item for item in path_list if r.match(str(item)))
                if len(opportunities_path_list) == 0:
                    raise FileNotFoundError("No opportunity file", "opp_file")
            else:
                raise FileNotFoundError("The opportunities folder doesn't exist", "opp_folder")
        except FileNotFoundError as err:
            if err.args[1] == "opp_folder":
                print("The opportunities folder doesn't exist")
            if err.args[1] == "opp_file":
                print("No opportunity file", "opp_file")
        else:
            # load and update the new valuation xlsx
            for opportunities_path in opportunities_path_list:
                # load and update the new valuation xlsx
                print(f"Working with {opportunities_path}...")
                self.opportunities.append(read_opportunity(opportunities_path))
            # load the opportunities
            monitor_file_path = opportunities_folder_path / 'Monitor' / 'Monitor.xlsx'
            print("Updating Monitor...")
            self.update_monitor(monitor_file_path)

    def update_monitor(self, monitor_file_path):
        """Update the Monitor file

        :param monitor_file_path: the path of the Monitor file
        """

        with xlwings.App(visible=False) as app:
            pipline_book = app.books.open(monitor_file_path)
            self.update_opportunities(pipline_book)
            self.update_holdings(pipline_book)
            self.update_market(pipline_book)
            pipline_book.save(monitor_file_path)
            pipline_book.close()

    def update_opportunities(self, pipline_book):
        """Update the opportunities sheet in the Pipeline_monitor file

        :param pipline_book: xlwings book object
        """

        monitor_sheet = pipline_book.sheets('Opportunities')
        monitor_sheet.range('B5:N200').clear_contents()

        r = 5
        for a in self.opportunities:
            monitor_sheet.range((r, 2)).value = a.asset_code
            monitor_sheet.range((r, 3)).value = a.name
            monitor_sheet.range((r, 4)).value = a.exchange
            monitor_sheet.range((r, 5)).value = a.price
            monitor_sheet.range((r, 6)).value = a.current_irr
            monitor_sheet.range((r, 7)).value = a.risk_premium
            monitor_sheet.range((r, 8)).value = f'=F{r}-G{r}'
            monitor_sheet.range((r, 9)).value = a.periodic_payment
            monitor_sheet.range((r, 10)).value = f'=I{r}/E{r}'
            monitor_sheet.range((r, 11)).value = a.ideal_price
            monitor_sheet.range((r, 12)).value = a.last_fy
            monitor_sheet.range((r, 13)).value = a.invest_horizon
            monitor_sheet.range((r, 14)).value = a.is_updated
            r += 1

    def update_holdings(self, pipline_book):
        """Update the Current_Holdings sheet in the Pipeline_monitor file.

        :param pipline_book: xlwings book object
        """

        holding_sheet = pipline_book.sheets('Current_Holdings')
        holding_sheet.range('B7:J200').clear_contents()

        k = 7
        for a in self.opportunities:
            if a.total_units:
                holding_sheet.range((k, 2)).value = a.asset_code
                holding_sheet.range((k, 3)).value = a.name
                holding_sheet.range((k, 4)).value = a.exchange
                holding_sheet.range((k, 5)).value = a.price_currency
                holding_sheet.range((k, 6)).value = a.unit_cost
                holding_sheet.range((k, 7)).value = a.total_units
                holding_sheet.range((k, 8)).value = f'=F{k}*G{k}'
                # holding_sheet.range((k, 9)).value =
                # holding_sheet.range((k, 10)).value =
                k += 1

        # Current Holdings
        holding_sheet.range('I2').value = datetime.today().strftime('%Y-%m-%d')

    def update_market(self, pipline_book):
        """Update the Current_Holdings sheet in the Pipeline_monitor file.

        :param pipline_book: xlwings book object
        """

        market_sheet = pipline_book.sheets('Market')

        market_sheet.range('D3').value = self.us_riskfree
