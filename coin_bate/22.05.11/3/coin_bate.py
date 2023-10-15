import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['font.size'] = 15
matplotlib.rcParams['axes.unicode_minus'] = False

import datetime
import time

import pyupbit as bit
access = "비밀키"
secret = "비밀키"
upbit = bit.Upbit(access, secret)

#------------------------------------------------------------------------------------------------데이터 가공 함수>>>>>>>>>>
#----------------------------------------가격 가중별 거래량 계산>>>>>
def fd_del_vol(df):

    del_vol = df['delta'] * df['volume']

    return pd.Series(del_vol)


#----------------------------------------가격차 계산>>>>>
def fd_del(df):

    delta = df['close'] - df['open']

    return pd.Series(delta)


#----------------------------------------VR 계산>>>>>
def fd_vr(df, k):
    up, mid, down = df['close'].diff(), df['close'].diff(), df['close'].diff()

    up[up <= 0] = 0
    mid[mid != 0] = 0
    down[down >= 0] = 0

    up[up > 0] = 1
    mid[mid == 0] = 1
    down[down < 0] = 1

    up *= df['volume']
    mid *= df['volume']
    down *= df['volume']

    v_up = up.ewm(com = k-1, min_periods = k).sum()
    v_mid = mid.ewm(com = k-1, min_periods = k).sum()
    v_down = down.ewm(com = k-1, min_periods = k).sum()

    return pd.Series(((v_up + v_mid) / 2) / ((v_down + v_mid) / 2) * 100)


#----------------------------------------거래량 이동평균>>>>>
def fd_v_m(df, k):
    nums = df['del_vol'].copy()

    V_M = nums.ewm(com = k-1, min_periods = k).mean()

    return pd.Series(V_M)


#----------------------------------------macd 계산>>>>>
def fd_macd(df, k1, k2, sig):
    # 백테스팅 계산
    nums = df['price'].copy()

    macd_k1 = nums.ewm(com = k1-1, min_periods = k1).mean()
    macd_k2 = nums.ewm(com = k2-1, min_periods = k2).mean()

    macd = macd_k2 - macd_k1
    macd_sig = macd.ewm(com = sig-1, min_periods = sig).mean()

    return pd.Series(macd - macd_sig)

#----------------------------------------이동 평균 계산>>>>>
def fd_ma(df, k):
    nums = df['del_vol'].copy()

    MA = nums.ewm(com = k-1, min_periods = k).mean()

    return pd.Series(MA)


#----------------------------------------볼린저 밴드 계산>>>>>
def fd_bb(df, mk, vk):
    nums = df['price'].copy()

    MA = df['bb_mid'].copy()
    MV = nums.rolling(window = mk).std()

    B_U = MA + MV * vk

    return pd.Series(B_U)


#------------------------------------------------------------------------------------------------백테스팅 테스트>>>>>>>>>>
class backTesting:
    def __init__(self, data2, cash, k1, k2):
        # self.df60 = data1
        self.df15 = data2
        # self.df05 = data3

        self.buy_sig = False
        self.sell_sig = False
        self.see = False

        self.fee = 0.001

        self.st_cash = cash
        self.ed_cash = cash
        self.highest_cash = cash
        self.lowest_cash = cash

        self.buy_cash = 0
        self.sell_cash = 0

        self.ror = 1
        self.acu_ror = 1
        self.mdd = 0

        self.buy_cot = 0
        self.sell_cot = 0
        self.win_cot = 0

        self.k1 = k1 # vr 관련
        self.k2 = k2 # macd 관련

        self.name = 'test_' + str(k1) + '_' + str(k2) + '.csv'

            

    def execute(self):
        # 0:오픈, 1:고가, 2:저가, 3:종가, 4:거래량, 5:거래대금
    
        for i in range(25, self.df15.shape[0]):

            op = self.df15.iloc[i, 0]
            ep = self.df15.iloc[i, 3]
            lp = self.df15.iloc[i, 2]
            hp = self.df15.iloc[i, 1]

            v5 = self.df15.iloc[i, 8]
            v10 = self.df15.iloc[i, 9]
            v20 = self.df15.iloc[i, 10]

            if self.buy_sig:
                if (v20 / v5) <= self.k1 or (v10 / v5) <= self.k2: # 
                    self.sell(i, ep / self.buy_cash)

            else:
                if self.sell_sig: # 지우삼
                    if (v20 / v5) > self.k1 and  (v10 / v5) > self.k2: #
                        if True:
                            self.buy(i)

                    
            if self.ror > 1:
                self.win_cot += 1
                self.acu_ror *= self.ror
                self.ror = 1
            elif self.ror != 1:
                self.acu_ror *= self.ror
                self.ror = 1

            self.highest_cash = max(self.highest_cash, self.ed_cash)

            self.lowest_cash = min(self.lowest_cash, self.ed_cash)

            dd = (self.highest_cash - self.ed_cash) / self.highest_cash * 100
            self.mdd = max(self.mdd, dd)

        self.df15.to_csv(self.name, encoding='utf-8-sig')

        if self.buy_cot == 0:
            pass
        else:
            buy = self.df15.loc[self.df15['buy'] > 0, 'buy']
        if self.sell_cot == 0:
            pass
        else:
            sell = self.df15.loc[self.df15['sell'] > 0, 'sell']

        self.result()

        plt.figure(1, figsize=(40, 3))
        plt.plot(self.df15.index, self.df15['close'], color='green', label="가격")
        if self.buy_cot == 0:
            pass
        else:
            plt.plot(buy.index, buy, color='red', marker='o', ms='5', ls='none')
        if self.sell_cot == 0:
            pass
        else:
            plt.plot(sell.index, sell, color='blue', marker='o', ms='5', ls='none')

        plt.figure(2, figsize=(40, 6))
        plt.plot(self.df15.index, self.df15['macd'], color='orange', label="macd")
        # plt.plot(self.df15.index, self.df15['vm5'], color='c', label="vm5")
        # plt.plot(self.df15.index, self.df15['vm10'], color='y', label="vm10")
        # plt.plot(self.df15.index, self.df15['vm20'], color='m', label="vm20")
        plt.legend()
        plt.grid(axis='y')
        plt.show()

        return self.acu_ror

    # 구매하기
    def buy(self,  i):
        self.see = False
        self.buy_sig = True
        self.buy_cot += 1
        self.buy_cash = self.df15.iloc[i, 3]
        self.ed_cash -= self.buy_cash * 0.0005
        self.df15.iloc[i, 13] = self.buy_cash#


    # 판매하기
    def sell(self, i, prc):
        self.prc = prc
        self.see = False
        self.buy_sig = False
        self.sell_sig = False

        self.sell_cot += 1
        self.ed_cash *= self.prc
        self.ed_cash *= 0.9995

        if self.prc >= 1.1:
            self.df15.iloc[i, 14] = self.df15.iloc[i, 1] #
        else:
            self.df15.iloc[i, 14] = self.df15.iloc[i, 3] #
        
        self.ror = self.prc * 0.9995
        


    def result(self) :
        print('='*40)
        print('테스트 결과')
        print('-'*40)
        print('총 구입 횟수 : %s' %self.buy_cot)
        print('총 판매 횟수 : %s' %self.sell_cot)
        print('승리 횟수 : %s' %self.win_cot)
        if min(self.buy_cot, self.sell_cot) == 0:
            print('승률 : 0')
        else:
            print('승률 : %s' %(self.win_cot / min(self.buy_cot, self.sell_cot) * 100))
        print('누적 수익률 : %s' %self.acu_ror)
        print('현재 잔액 : %s' % self.ed_cash)
        print('최고 잔액 : %s' % self.highest_cash)
        print('최저 잔액 : %s' % self.lowest_cash)
        print('최대 낙폭 (MDD) : %s' % self.mdd)
        print('='*40)
        
#------------------------------------------------------------------------------------------------코인 데이터 셋팅>>>>>>>>>>
#----------------------------------------데이터 불러오기>>>>>
def get_data(tick, count, time):
    count = count

    date = bit.get_ohlcv(ticker=tick, interval='week', count=count, to=time)

    return pd.DataFrame(date)

#----------------------------------------데이터 가공>>>>>
def set_data(df):
    macd_k1, macd_k2, macd_sig = 6, 60, 12

    df['volume'] = df['volume'].diff() # 1
    df['value'] = df['value'].diff() # 2

    df['delta'] = df['price'].diff() # 3
    df['del_vol'] = fd_del_vol(df) # 4
    df['vm5'] = fd_v_m(df, 5) # 5
    df['vm10'] = fd_v_m(df, 20) # 6
    df['vm20'] = fd_v_m(df, 60) # 7
    df['macd'] = fd_macd(df, macd_k1, macd_k2, macd_sig) # 8
    df['bb_mid'] = fd_ma(df, 20) # 9
    df['bb_up'] = fd_bb(df, 20, 2) # 10
    df['bb_down'] = fd_bb(df, 20, -2) # 11
    df['buy'] = np.NAN # 12
    df['sell'] = np.NAN # 13

    return pd.DataFrame(df)

#----------------------------------------초기 데이터 셋팅>>>>>
# coin_name = "KRW-CELO"
# count = 6
# to_time = '20220413'

# df = pd.read_csv('KRW-CELO_t.csv')
# df = set_data(df)
# print(df)
# df.to_csv('KRW-CELO_t.csv', encoding='utf-8-sig')

# backtest = backTesting(df, 1000000, 1, 1)
# backtest.execute()



#------------------------------------------------------------------------------------------------데이터 수집>>>>>>>>>>
#----------------------------------------변수 데이터 수집>>>>>
# idx = [0.2]
# col = [0.3]
# df2 = pd.DataFrame(index = idx, columns = col)
# df2.to_csv('testdata.csv', encoding='utf-8-sig')

# for i in idx:
#     for j in col:
#         print(i, j)
#         backtest = backTesting(df_01, 1000000, i, j)
#         aa = backtest.execute()
#         df2.loc[i, j] = aa
# df2.to_csv('testdata.csv', encoding='utf-8-sig')

# 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1
# 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1
# 0.65, 0.66, 0.67, 0.68, 0.69, 0.7, 0.71, 0.72, 0.73, 0.74, 0.75
# 0.75, 0.76, 0.77, 0.78, 0.79, 0.8, 0.81, 0.82, 0.83, 0.84, 0.85

#------------------------------------------------------------------------------------------------데이터 수집>>>>>>>>>>
#----------------------------------------시간 데이터 수집>>>>>
idx = ['KRW-NEO', 'KRW-MTL', 'KRW-LTC', 'KRW-XRP', 'KRW-OMG', 'KRW-SNT', 'KRW-WAVES', 'KRW-XEM', 'KRW-QTUM', 'KRW-LSK', 'KRW-STEEM', 'KRW-XLM', 'KRW-ARDR', 'KRW-ARK', 
'KRW-STORJ', 'KRW-GRS', 'KRW-REP', 'KRW-ADA', 'KRW-SBD', 'KRW-POWR', 'KRW-ICX', 'KRW-EOS', 'KRW-TRX', 'KRW-SC', 'KRW-ONT', 'KRW-ZIL', 'KRW-POLY', 'KRW-ZRX', 'KRW-LOOM', 
'KRW-BAT', 'KRW-IOST', 'KRW-RFR', 'KRW-CVC', 'KRW-IQ', 'KRW-IOTA', 'KRW-MFT', 'KRW-ONG', 'KRW-GAS', 'KRW-UPP', 'KRW-ELF', 'KRW-KNC', 'KRW-THETA', 'KRW-QKC', 'KRW-MOC', 
'KRW-ENJ', 'KRW-TFUEL', 'KRW-MANA', 'KRW-ANKR', 'KRW-AERGO', 'KRW-ATOM', 'KRW-TT', 'KRW-CRE', 'KRW-MBL', 'KRW-WAXP', 'KRW-HBAR', 'KRW-MED', 'KRW-MLK', 'KRW-STPT', 'KRW-ORBS', 
'KRW-VET', 'KRW-CHZ', 'KRW-STMX', 'KRW-DKA', 'KRW-HIVE', 'KRW-KAVA', 'KRW-AHT', 'KRW-LINK', 'KRW-XTZ', 'KRW-BORA', 'KRW-JST', 'KRW-CRO', 'KRW-TON', 'KRW-SXP', 'KRW-HUNT', 
'KRW-PLA', 'KRW-DOT', 'KRW-SRM', 'KRW-MVL', 'KRW-STRAX', 'KRW-AQT', 'KRW-GLM', 'KRW-SSX', 'KRW-META', 'KRW-FCT2', 'KRW-CBK', 'KRW-SAND', 'KRW-HUM', 'KRW-DOGE', 'KRW-STRK', 
'KRW-PUNDIX', 'KRW-FLOW', 'KRW-DAWN', 'KRW-AXS', 'KRW-STX', 'KRW-XEC', 'KRW-SOL', 'KRW-MATIC', 'KRW-AAVE', 'KRW-1INCH', 'KRW-ALGO', 'KRW-NEAR', 'KRW-WEMIX', 'KRW-AVAX', 'KRW-T', 
'KRW-CELO', 'KRW-GMT']
# 데이터 셋팅

cp_Data = pd.DataFrame(columns = idx)
ca_Data = pd.DataFrame(columns = idx)
cb_Data = pd.DataFrame(columns = idx)

while True:
    # 데이터 조회
    coin_price = pd.Series(bit.get_current_price(ticker = idx))
    coin_order = bit.get_orderbook(ticker = idx)
    print("불러움", datetime.datetime.now())
        
    # 데이터 가공
    cp_Data.loc[datetime.datetime.now()] = coin_price

    ca_list = []
    cb_list = []
    for i in range(len(idx)):
        ca_list.append(coin_order[i]['total_ask_size'])
        cb_list.append(coin_order[i]['total_bid_size'])

    ca_Data.loc[datetime.datetime.now()] = pd.Series(ca_list, index=idx)
    cb_Data.loc[datetime.datetime.now()] = pd.Series(cb_list, index=idx)

    # 데이터 저장
    cp_Data.to_csv('cp_Data.csv', encoding='utf-8-sig')
    ca_Data.to_csv('ca_Data.csv', encoding='utf-8-sig')
    cb_Data.to_csv('cb_Data.csv', encoding='utf-8-sig')
