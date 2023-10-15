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
    nums = df['del_vol'].copy()

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
    nums = df['close'].copy()

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
#----------------------------------------60분봉 데이터 불러오기>>>>>
def get_data_60(tick, count, time):
    count60m = count

    date_60m = bit.get_ohlcv(ticker=tick, interval='minute60', count=count60m, to=time)

    return pd.DataFrame(date_60m)

#----------------------------------------15분봉 데이터 불러오기>>>>>
def get_data_15(tick, count, time):
    count15m = count * 4

    date_15m = bit.get_ohlcv(ticker=tick, interval='minute15', count=count15m, to=time)

    return pd.DataFrame(date_15m)

#----------------------------------------05분봉 데이터 불러오기>>>>>
def get_data_05(tick, count, time):
    count05m = count * 12

    date_05m = bit.get_ohlcv(ticker=tick, interval='minute5', count=count05m, to=time)

    return pd.DataFrame(date_05m)

#----------------------------------------01분봉 데이터 불러오기>>>>>
def get_data_01(tick, count, time):
    count01m = count

    date_01m = bit.get_ohlcv(ticker=tick, interval='week', count=count01m, to=time)

    return pd.DataFrame(date_01m)

#----------------------------------------데이터 가공>>>>>
def set_data(df):
    macd_k1, macd_k2, macd_sig = 6, 60, 12

    df['delta'] = fd_del(df) # 6
    df['del_vol'] = fd_del_vol(df) # 7
    df['vm5'] = fd_v_m(df, 5) # 8
    df['vm10'] = fd_v_m(df, 20) # 9
    df['vm20'] = fd_v_m(df, 60) # 10
    df['macd'] = fd_macd(df, macd_k1, macd_k2, macd_sig)
    df['bb_mid'] = 0 #fd_ma(df, 20) # 12
    # df['bb_up'] = 0 #fd_bb(df, 20, 2)
    # df['bb_down'] = 0 #fd_bb(df, 20, -2)
    df['buy'] = np.NAN # 13
    df['sell'] = np.NAN # 14

    return pd.DataFrame(df)

#----------------------------------------15분봉>>>>>
coin_name = "KRW-WAVES"
count = 6
to_time = '20220413'

# df_60 = get_data_60(coin_name, count, to_time)
# df_15 = get_data_15(coin_name, count, to_time)
# df_05 = get_data_05(coin_name, count, to_time)
df_01 = get_data_01(coin_name, count, to_time)

# df_60 = set_data(df_60)
# df_15 = set_data(df_15)
# df_05 = set_data(df_05)
df_01 = set_data(df_01)

# backtest = backTesting(df_15, 1000000, 1, 1)
# backtest.execute()

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

idx = ['KRW-BTC', 'KRW-ETH', 'KRW-NEO', 'KRW-MTL', 'KRW-LTC', 'KRW-XRP', 'KRW-ETC', 'KRW-OMG', 'KRW-SNT', 'KRW-WAVES', 'KRW-XEM', 'KRW-QTUM', 'KRW-LSK', 'KRW-STEEM',
 'KRW-XLM', 'KRW-ARDR', 'KRW-ARK', 'KRW-STORJ', 'KRW-GRS', 'KRW-REP', 'KRW-ADA', 'KRW-SBD', 'KRW-POWR', 'KRW-BTG', 'KRW-ICX', 'KRW-EOS', 'KRW-TRX', 'KRW-SC', 'KRW-ONT', 
'KRW-ZIL', 'KRW-POLY', 'KRW-ZRX', 'KRW-LOOM', 'KRW-BCH', 'KRW-BAT', 'KRW-IOST', 'KRW-RFR', 'KRW-CVC', 'KRW-IQ', 'KRW-IOTA', 'KRW-MFT', 'KRW-ONG', 'KRW-GAS', 'KRW-UPP', 
'KRW-ELF', 'KRW-KNC', 'KRW-BSV', 'KRW-THETA', 'KRW-QKC', 'KRW-BTT', 'KRW-MOC', 'KRW-ENJ', 'KRW-TFUEL', 'KRW-MANA', 'KRW-ANKR', 'KRW-AERGO', 'KRW-ATOM', 'KRW-TT', 'KRW-CRE', 
'KRW-MBL', 'KRW-WAXP', 'KRW-HBAR', 'KRW-MED', 'KRW-MLK', 'KRW-STPT', 'KRW-ORBS', 'KRW-VET', 'KRW-CHZ', 'KRW-STMX', 'KRW-DKA', 'KRW-HIVE', 'KRW-KAVA', 'KRW-AHT', 'KRW-LINK', 
'KRW-XTZ', 'KRW-BORA', 'KRW-JST', 'KRW-CRO', 'KRW-TON', 'KRW-SXP', 'KRW-HUNT', 'KRW-PLA', 'KRW-DOT', 'KRW-SRM', 'KRW-MVL', 'KRW-STRAX', 'KRW-AQT', 'KRW-GLM', 'KRW-SSX', 
'KRW-META', 'KRW-FCT2', 'KRW-CBK', 'KRW-SAND', 'KRW-HUM', 'KRW-DOGE', 'KRW-STRK', 'KRW-PUNDIX', 'KRW-FLOW', 'KRW-DAWN', 'KRW-AXS', 'KRW-STX', 'KRW-XEC', 'KRW-SOL', 'KRW-MATIC', 
'KRW-NU', 'KRW-AAVE', 'KRW-1INCH', 'KRW-ALGO', 'KRW-NEAR', 'KRW-WEMIX', 'KRW-AVAX', 'KRW-T', 'KRW-CELO', 'KRW-GMT']

col = ['price', 'volume', 'value']
datalist = []

for i in range(114):
    datalist.append(pd.DataFrame(columns = col))

while True:
    for i in range(114):
        coin_name = idx[i]
        count = 1
        to_time = None
        df_01 = get_data_01(coin_name, count, to_time)
        print("불러움", datetime.datetime.now(), idx[i], df_01.shape[0])
        time.sleep(0.03)
        if df_01.shape[0] != 0:
            datalist[i].loc[datetime.datetime.now()] = (df_01.iloc[-1, 3], df_01.iloc[-1, 4], df_01.iloc[-1, 5])
            # print("저장됨", idx[i], datalist[i][-1])
        dataname = idx[i] + '.csv'
        datalist[i].to_csv(dataname, encoding='utf-8-sig')
