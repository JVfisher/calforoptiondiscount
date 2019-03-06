import asyncio

import PyQt5.QtWidgets as qt
# import PySide2.QtWidgets as qt

from ib_insync import IB, util
from ib_insync.contract import *  # noqa
from  ib_insync.objects import OptionComputation


class TickerTable(qt.QTableWidget):

    
    headers = [
        'localSymbol', 'bidSize', 'bid', 'ask', 'askSize',
        'last', 'lastSize', 'close','askImpVol','discount','strike']

    def __init__(self, parent=None):
        qt.QTableWidget.__init__(self, parent)
        self.conId2Row = {}
        self.setColumnCount(len(self.headers))
        self.setHorizontalHeaderLabels(self.headers)
        self.setAlternatingRowColors(True)
        self.symbolofticker = None

    def __contains__(self, contract):
        assert contract.conId
        return contract.conId in self.conId2Row

    def addTicker(self, ticker):
        row = self.rowCount()
        self.insertRow(row)
        self.conId2Row[ticker.contract.conId] = row
        for col in range(len(self.headers)):
            item = qt.QTableWidgetItem('-')
            self.setItem(row, col, item)
        item = self.item(row, 0)
        item.setText(ticker.contract.localSymbol + (
            ticker.contract.currency if ticker.contract.secType == 'CASH'
            else ''))
        self.resizeColumnsToContents()

    def clearTickers(self):
        self.setRowCount(0)
        self.conId2Row.clear()

    def onPendingTickers(self, tickers):
        for ticker in tickers:
            if (type(getattr(ticker,'contract'))!=Stock)&(self.symbolofticker==getattr(ticker, 'contract').symbol):  
                row = self.conId2Row.get(ticker.contract.conId,0)
                for col, header in enumerate(self.headers):
                    item = self.item(row, col)
                    if item!=None:
                        if col == 0:
                            continue
                        if col == 8:                   
                            if (getattr(ticker, 'lastGreeks',0)!=0)&(getattr(ticker, 'lastGreeks',0)!=None): 
                                if getattr(ticker, 'lastGreeks',0)[0]!=None:
                                    val = '{0:0.3f}'.format(getattr(ticker, 'lastGreeks',0)[0])
                                else:
                                    val = 'NaN'
                                item.setText(str(val))
                            continue
                        if col == 9:
                            if getattr(ticker, 'ask',0)!=0:
                                val = '{0:0.2f}%'.format(100*(getattr(ticker, 'ask',0)/getattr(ticker, 'contract').strike))
                                item.setText(str(val))            
                            continue
                        if col == 10:
                            val = '{0:0.2f}'.format(getattr(ticker, 'contract').strike)
                            item.setText(str(val))            
                            continue
    
                        val = getattr(ticker, header)                    
                        item.setText(str(val))
                        
            self.resizeColumnsToContents()


class Window(qt.QWidget):

    def __init__(self, host, port, clientId):
        qt.QWidget.__init__(self)
        
        self.vxxbLabel = qt.QLabel('VXXB')
        self.vxxbButton = qt.QPushButton('VXXB')
        self.tltLabel = qt.QLabel('TLT')
        self.tltButton = qt.QPushButton('TLT')
        self.gldLabel = qt.QLabel('GLD')
        self.gldButton = qt.QPushButton('GLD')
        self.vxxbButton.clicked.connect(self.onVXXBButtonClicked)
        self.gldButton.clicked.connect(self.onGLDButtonClicked)
        self.tltButton.clicked.connect(self.onTLTButtonClicked)
        self.pricedic = {}
        
#        self.edit = qt.QLineEdit('', self)
#        self.edit.editingFinished.connect(self.add)
        self.table = TickerTable()
        self.connectButton = qt.QPushButton('Connect')
        self.connectButton.clicked.connect(self.onConnectButtonClicked)
        
        
        layout = qt.QGridLayout(self)#qt.QVBoxLayout(self)
        

        layout.addWidget(self.vxxbLabel,0,0,1,2)
        layout.addWidget(self.vxxbButton,1,0,1,2)
        layout.addWidget(self.tltLabel,0,2,1,2)
        layout.addWidget(self.tltButton,1,2,1,2)
        layout.addWidget(self.gldLabel,0,4,1,2)
        layout.addWidget(self.gldButton,1,4,1,2)        
        
        
#        layout.addWidget(self.edit)
        layout.addWidget(self.table,2,0,6,6)
        layout.addWidget(self.connectButton,9,2,1,2)
        
        

        self.connectInfo = (host, port, clientId)
        self.ib = IB()
        self.ib.pendingTickersEvent += self.table.onPendingTickers
        self.ib.pendingTickersEvent += self.onPendingTickersForLabels

    def add(self, contract):
        if (contract and self.ib.qualifyContracts(contract)
                and contract not in self.table):
            ticker = self.ib.reqMktData(contract, '', False, False, None)
            self.table.addTicker(ticker)

    def onConnectButtonClicked(self, _):
        if self.ib.isConnected():
            self.ib.disconnect()
            self.table.clearTickers()
            self.connectButton.setText('Connect')
        else:
            self.ib.connect(*self.connectInfo)
            self.connectButton.setText('Disonnect')
            
            self.vxxb = Stock('VXXB',exchange='SMART')
            self.ib.qualifyContracts(self.vxxb)
            self.table.vxxbticker = self.ib.reqMktData(self.vxxb, '', False, False, None)
            
            self.tlt = Stock('TLT',exchange='ARCA')
            self.ib.qualifyContracts(self.tlt)
            self.table.tltticker = self.ib.reqMktData(self.tlt, '', False, False, None)
            
            self.gld = Stock('GLD',exchange='ARCA')
            self.ib.qualifyContracts(self.gld)
            self.table.gldticker = self.ib.reqMktData(self.gld, '', False, False, None)
            
    def closeEvent(self, ev):
        asyncio.get_event_loop().stop()

    def onPendingTickersForLabels(self, tickers):
        for ticker in tickers:
            if type(getattr(ticker,'contract'))==Stock:  
                if ticker.contract.symbol=='VXXB':
                    self.vxxbprice = ticker.marketPrice()
                    self.vxxbLabel.setText('{0:0.2f}'.format(self.vxxbprice))
                    self.table.vxxbprice = self.vxxbprice
                    self.pricedic['VXXB'] = self.vxxbprice
#                    print('vxxb:'+str(ticker.marketPrice()))
                elif ticker.contract.symbol=='GLD':
                    self.gldprice = ticker.marketPrice()
                    self.gldLabel.setText('{0:0.2f}'.format(self.gldprice))
                    self.table.gldprice=self.gldprice
                    self.pricedic['GLD'] = self.gldprice
#                    print('gld:'+str(ticker.marketPrice()))
                else:
                    self.tltprice = ticker.marketPrice()
                    self.tltLabel.setText('{0:0.2f}'.format(self.tltprice))
                    self.table.tltprice=self.tltprice
                    self.pricedic['TLT'] = self.tltprice
#                    print('tlt:'+str(ticker.marketPrice()))
                    
                    
    def prepareOptionContract(self,stockcontract):        
        
        contractPrice = self.pricedic[stockcontract.symbol]
        chains = self.ib.reqSecDefOptParams(stockcontract.symbol, '', stockcontract.secType,stockcontract.conId)
        chain = next(c for c in chains if c.exchange == 'SMART')
#        print(chain)
        strikes = sorted([strike for strike in chain.strikes
        if contractPrice - 2 < strike < contractPrice + 2])
        expirations = sorted(exp for exp in chain.expirations)[:2]

        contracts = [Option(stockcontract.symbol, expiration, strike, 'P','SMART')
                    for expiration in expirations
                    for strike in strikes]
#        print(contracts)
        self.ib.qualifyContracts(*contracts)
        for ac in contracts:
            self.add(contract=ac)           
            
            
    def onVXXBButtonClicked(self, _):
        if self.ib.isConnected():
            self.table.clearTickers()
            self.prepareOptionContract(self.vxxb)
            self.table.symbolofticker = 'VXXB'
            
    def onGLDButtonClicked(self, _):
        if self.ib.isConnected():
            self.table.clearTickers()
            self.prepareOptionContract(self.gld)
            self.table.symbolofticker = 'GLD'
            
    def onTLTButtonClicked(self, _):
        print('TLT')
        if self.ib.isConnected():
            self.table.clearTickers()
            self.prepareOptionContract(self.tlt)
            self.table.symbolofticker = 'TLT'


            
            
                
if __name__ == '__main__':
    util.patchAsyncio()
    util.useQt()
    # util.useQt('PySide2')
    window = Window('127.0.0.1', 7497, 1)
    window.resize(990, 980)
    window.show()
    IB.run()
