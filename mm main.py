import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['font.size'] = 15
matplotlib.rcParams['axes.unicode_minus'] = False

import time

import pyupbit as bit
access = "비밀키"
secret = "비밀키"
upbit = bit.Upbit(access, secret)

#------------------------------------------------------------------------------------------------거래 코인 조회>>>>>>>>>>
# 코인 조회
# print(bit.get_tickers(fiat="KRW"))

#------------------------------------------------------------------------------------------------코인 데이터 분석>>>>>>>>>>
#----------------------------------------15분봉>>>>>
def fd_vr(df, k):
    df = df.tail(k).copy()
    df['delta'] = df['close'] - df['open']
    df = df[['delta'] + ['volume']]

    v_up = df.loc[df['delta'] > 0, 'volume'].sum()
    v_mid = df.loc[df['delta'] == 0, 'volume'].sum()
    v_down = df.loc[df['delta'] < 0, 'volume'].sum()

    if (v_down + v_mid) / 2 == 0:
        return (v_down + v_mid) / 2 * 100
    else:
        return ((v_up + v_mid) / 2) / ((v_down + v_mid) / 2) * 100

    # up = pd.Series(np.where(df['delta'] > 0, df['volume'], 0))
    # mid = pd.Series(np.where(df['delta'] == 0, df['volume'], 0))
    # down = pd.Series(np.where(df['delta'] < 0, df['volume'], 0))

    # v_up = up.ewm(com = k-1, min_periods = k).sum()
    # v_mid = mid.ewm(com = k-1, min_periods = k).sum()
    # v_down = down.ewm(com = k-1, min_periods = k).sum()

    # vr = pd.Series(((v_up + v_mid) / 2) / ((v_down + v_mid) / 2) * 100)
    # return vr.iloc[-1]

def fd_d_obv(df, st, k):
    df= df.tail(k).copy()
    df['delta'] = df['close'] - df['open']
    df = df[['delta'] + ['volume']]
    df['obv'] = 0

    # for idx, row in df.iterrows():
    #     if idx == df.index[0]:
    #         if row['delta'] > 0:
    #             row['obv'] = st + row['volume']
    #         elif row['delta'] == 0:
    #             row['obv'] = st
    #         else:
    #             row['obv'] = st - row['volume']
    #         go_obv = row['obv']

    #     else:
    #         if row['delta'] > 0:
    #             row['obv'] = go_obv + row['volume']
    #         elif row['delta'] == 0:
    #             row['obv'] = go_obv
    #         else:
    #             row['obv'] = go_obv - row['volume']
    #         go_obv = row['obv']

    for i in range(k):
        if i == 0:
            if df.iloc[i, 0] > 0:
                df.iloc[i, 2] = st + df.iloc[i, 1]
            elif df.iloc[i, 0] == 0:
                df.iloc[i, 2] = st
            else:
                df.iloc[i, 2] = st - df.iloc[i, 1]
            go_obv = df.iloc[i, 2]

        else:
            if df.iloc[i, 0] > 0:
                df.iloc[i, 2] = go_obv + df.iloc[i, 1]
            elif df.iloc[i, 0] == 0:
                df.iloc[i, 2] = go_obv
            else:
                df.iloc[i, 2] = go_obv - df.iloc[i, 1]
            go_obv = df.iloc[i, 2]

    obv_la = go_obv
    obv_km = df['obv'].mean()

    return obv_la - obv_km

    # obv_la = df['obv'].ewm(com = k-1, min_periods = k)
    # obv_km = df['obv'].ewm(com = k-1, min_periods = k).mean()

    # return obv_la.iloc[-1] - obv_km.iloc[-1]



class backTesting:
    def __init__(self, data, cash, vr_lk, vr_mk, k):
        self.df = data
        self.buy_sig = False
        self.sell_sig = False

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

        self.obv_k = 10
        self.vr_k = 20
        self.vr_lk = vr_lk
        self.vr_mk = vr_mk
        self.k = k

    def execute(self):
        # d_obv 값: obv_k, vr 값: vr_k, 시점 포착: vr_lk, 세력 포착: vr_mk, 최대 수익: k
        # 0:오픈, 1:고가, 2:저가, 3:종가, 4:거래량, 5:거래대금
        # 6:vr 7:d_obv
        # self.df.iloc[i, 6]

        self.df['vr'] = 0
        self.df['d_obv'] = 0
        self.df['buy'] = 0
        self.df['sell'] = 0

        vr = []
        d_obv = []

        for i in range(max(self.obv_k, self.vr_k) - 1, self.df.shape[0]):

            if i == self.df.shape[0]:
                vr.append(fd_vr(self.df[0:], self.vr_k))
                d_obv.append(fd_d_obv(self.df[0:], 0, self.obv_k))
            else:
                vr.append(fd_vr(self.df[0:i + 1], self.vr_k))
                d_obv.append(fd_d_obv(self.df[0:i + 1], 0, self.obv_k))

            # print("vr값", vr[-1])
            # print("d_obv값", d_obv[-1])

            self.df.iloc[i, 6] = vr[-1]
            self.df.iloc[i, 7] = d_obv[-1]

            if self.buy_sig:
                if vr[-1] > self.vr_mk:
                    self.sell_sig = True
                    # 구입가 * k 에 매도신청
                    if self.df.iloc[i, 1] >= self.buy_cash * (1 + self.k):
                        self.buy_sig = False
                        self.sell_sig = False
                        self.df.iloc[i, 9] = 2 #
                        self.sell_cot += 1
                        self.ed_cash *= (1 + self.k)
                        self.ror = (1 + self.k)
                elif d_obv[-1] <= 0:
                    # 매도신청 취소  pass if self.sell_sig: else: 
                    self.buy_sig = False
                    self.sell_sig = False
                    self.df.iloc[i, 9] = 1 #
                    self.sell_cot += 1
                    self.ed_cash *= self.df.iloc[i, 3] / self.buy_cash
                    self.ror = self.df.iloc[i, 3] / self.buy_cash
                    
            else:
                if vr[-1] > self.vr_lk:
                    if len(d_obv) > 1:
                        if  d_obv[-2] < 0 and d_obv[-1] > 0:
                            self.buy_sig = True
                            self.df.iloc[i, 8] = 1 #
                            self.buy_cot += 1
                            self.buy_cash = self.df.iloc[i, 3]
                    else:
                        pass

            if self.ror > 1:
                self.win_cot += 1
                self.acu_ror *= self.ror
                self.ror = 1
            elif self.ror != 1:
                self.acu_ror *= self.ror
                self.ror = 1

            # 자산 최고점 갱신
            self.highest_cash = max(self.highest_cash, self.ed_cash)

            # 자산 최저점 갱신
            self.lowest_cash = min(self.lowest_cash, self.ed_cash)

            # 최대 낙폭 계산
            dd = (self.highest_cash - self.ed_cash) / self.highest_cash * 100
            self.mdd = max(self.mdd, dd)

        df.to_csv('maindata.csv', encoding='utf-8-sig')
        self.result()

    def result(self) :
        print('='*40)
        print('테스트 결과')
        print('-'*40)
        print('총 구입 횟수 : %s' %self.buy_cot)
        print('총 판매 횟수 : %s' %self.sell_cot)
        print('승리 횟수 : %s' %self.win_cot)
        print('승률 : %s' %(self.win_cot / min(self.buy_cot, self.sell_cot) * 100))
        print('누적 수익률 : %s' %self.acu_ror)
        print('현재 잔액 : %s' % self.ed_cash)
        print('최고 잔액 : %s' % self.highest_cash)
        print('최저 잔액 : %s' % self.lowest_cash)
        print('최대 낙폭 (MDD) : %s' % self.mdd)
        print('='*40)
        
to_time = '20220501'
count_15m = 8 * 4
count_5m =  24 * 3 * 20
date_15m = bit.get_ohlcv(ticker="KRW-TRX", interval='minute5', count=count_5m, to=to_time)
df = pd.DataFrame(date_15m)

backtest = backTesting(df, 1000000, 105, 300, 5)
backtest.execute()
        
# vr_k = 20
# obv_k = 10

# vr_lk = 150
# vr_mk = 500
# k = 0.08

# df['vr'] = 0
# df['d_obv'] = 0

# df.iloc[-1, 6] = fd_vr(df, vr_k)
# df.iloc[-1, 7] = fd_d_obv(df, 0, obv_k)

# print(df.iloc[-1, 6])
# print(df.iloc[-1, 7])


