# imports
from AlgorithmImports import *
from QuantConnect.Securities.Option import OptionPriceModels
from datetime import datetime, timedelta
# endregion

class BinomialOptionChartAlgorithm(QCAlgorithm):

    def Initialize(self):
        # Backtest period & cash, chan choose any times
        self.SetStartDate(2004, 4, 29)
        self.SetEndDate(  2025, 4, 18)
        self.SetWarmUp(timedelta(days=7))
        self.SetCash(10000)

        # trading spy and its option chain
        self.AddEquity("SPY", Resolution.Minute)
        opt = self.AddOption("SPY", Resolution.Minute)
        opt.SetFilter(-10, +10, timedelta(500), timedelta(750))

        # can use a built in binomial model
        opt.PriceModel = OptionPriceModels.BinomialJarrowRudd()

        # chart to compare
        chart = Chart("Option Model")
        chart.AddSeries(Series("Theoretical", SeriesType.Line, 0))   # left axis
        chart.AddSeries(Series("MarketMid",   SeriesType.Line, 1))   # right axis
        self.AddChart(chart)

        # (Optional) Compare to SPY price
        self.SetBenchmark("SPY")

    def OnData(self, slice: Slice):
        # only plot after 4 on target date
        if self.Time < datetime(2017, 8, 14, 16, 0):
            return
        self.Log("Time,Symbol,Right,Expiry,Strike,Bid,Ask,Last,Theo,OI,Underlying,IV")

        #this is from this:https://www.quantconnect.com/forum/discussion/2659/option-chain-history-theoretical-price-with-different-pricing-models/
        for chain in slice.OptionChains.Values:
            for contract in chain:
                underlying_price = chain.Underlying.Price
                iv = contract.ImpliedVolatility
                oi = contract.OpenInterest
                theo = contract.TheoreticalPrice
                if (theo is None or contract.BidPrice == 0 or contract.AskPrice == 0):
                    continue

                self.Log(f"{self.Time},{contract.Symbol.Value},{contract.Right},{contract.Expiry},{contract.Strike:.2f},"
                        f"{contract.BidPrice:.3f},{contract.AskPrice:.3f},{contract.LastPrice:.3f},{theo:.3f},"
                    f"{oi},{underlying_price:.2f},{iv:.4f}")

        # loop every option chain
        for chain in slice.OptionChains.Values:
            # sort by ATM proximity
            sorted_contracts = sorted(
                chain,
                key=lambda c: abs(c.Strike - chain.Underlying.Price)
            )
            # take the first two 
            for contract in sorted_contracts[:2]:
                # skip unpriced
                if (contract.TheoreticalPrice is None
                    or contract.BidPrice == 0
                    or contract.AskPrice == 0):
                    continue

                theo = contract.TheoreticalPrice
                mid  = 0.5 * (contract.BidPrice + contract.AskPrice)

                self.Plot("Option Model", "Theoretical", theo)
                self.Plot("Option Model", "MarketMid",   mid)
