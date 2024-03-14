#%%import gymfrom gym import spacesimport numpy as npclass OrderManager(object):    def __init__(self,balance=10000,fee_rate=0.0007):        self.balance_ = balance        self.fee_rate_ = fee_rate        self.pos_ = 0        self.buy_taded_qty_ = 0        self.sell_trade_qty_ = 0        self.trade_val_ = 0        self.cost_val_ = 0        self.cash_ = 0        self.cost_ = 0        self.draw_down_ = 0.0        self.peak_ret_ = 0.0        self.pos_ret_ = 0.0        self.cost_ = 0.0        self.cost_val_ = 0.0        self.max_pos_value_ = 0.0        self.pnl_ = 0        self.pos_pl_ = 0.0        self.pos_val_ = 0.0        self.time_ = 0        self.bid_ = 0        self.ask_ = 0        self.mid_ = 0        self.pos_open_time_ =0    def reset(self,balance=10000,fee_rate=0.0007):        self.balance_ = balance        self.fee_rate_ = fee_rate        self.pos_ = 0        self.buy_taded_qty_ = 0        self.sell_trade_qty_ = 0        self.trade_val_ = 0        self.cost_val_ = 0        self.cash_ = 0        self.cost_ = 0        self.draw_down_ = 0.0        self.peak_ret_ = 0.0        self.pos_ret_ = 0.0        self.cost_ = 0.0        self.cost_val_ = 0.0        self.max_pos_value_ = 0.0        self.pnl_ = 0        self.pos_pl_ = 0.0        self.pos_val_ = 0.0        self.time_ = 0        self.bid_ = 0        self.ask_ = 0    def onTick(self,msg:dict):        self.time_ = msg["time"]        self.bid_ = msg["bid"]        self.ask_ = msg["ask"]        self.mid_ = 0.5 * (self.bid_ + self.ask_)        if self.bid_==0.0:            self.bid_ = self.ask_        elif self.ask_==0.0:            self.ask_ = self.bid_        self._calcPosState()    def onTrade(self,tradeqty,price,Direction):        self.pos_ += tradeqty        if Direction==1:            self.buy_taded_qty_ += tradeqty            self.pos_open_time_ = self.time_        elif Direction==-1:            self.sell_trade_qty_ += tradeqty            self.pos_open_time_ = self.time_        self._calcCost(tradeqty,price,Direction)        if (self.pos_ == 0):            self.pos_open_time_ = 0            self.prev_open_price_ = 0.0    def _calcCost(self,tradeqty,price,Direction):        trade_val = tradeqty * price        self.trade_val_ += trade_val        self.fee_ = self.trade_val_ * self.fee_rate_        if (Direction == 1):            self.cost_val_ += trade_val            self.cash_ -= trade_val        elif (Direction == -1):            self.cost_val_ -= trade_val            self.cash_ += trade_val        if (self.pos_ == 0):            self.cost_val_ = 0            self.cost_ = 0        else:             self.cost_ = self.cost_val_ / self.pos_    def _calcPosState(self):        if (self.pos_ > 0):            self.max_pos_value_ = max(self.max_pos_value_, self.bid_)            self.draw_down_ = (-self.max_pos_value_ + self.bid_) / self.max_pos_value_            self.pos_val_ = self.pos_ * self.bid_            self.pnl_ = self.cash_ + self.pos_val_            self.pos_pl_ = self.pos_val_ - (self.cost_ * self.pos_)        elif (self.pos_ < 0):            if self.max_pos_value_==0.0:                self.max_pos_value_ = self.ask_            else:                self.max_pos_value_ = min(self.max_pos_value_, self.ask_)            self.draw_down_ = (self.max_pos_value_ - self.ask_) / self.max_pos_value_            self.pos_val_ = self.pos_ * self.ask_            self.pnl_ = self.cash_ + self.pos_val_            self.pos_pl_ = self.pos_val_ - (self.cost_ * self.pos_)        elif (self.pos_ == 0):            self.draw_down_ = 0.0            self.peak_ret_ = 0.0            self.pos_ret_ = 0.0            self.cost_ = 0.0            self.cost_val_ = 0.0            self.max_pos_value_ = 0.0            self.pnl_ = self.cash_            self.pos_pl_ = 0.0            self.pos_val_ = 0.0        if self.pos_!=0:            self.pos_ret_ = self._calcReturn()            if self.pos_ret_>self.peak_ret_:                self.peak_ret_ = self.pos_ret_        close_value = 0.0        if (self.pos_ > 0):            close_value = self.pos_ * self.bid_        elif (self.pos_ < 0):            close_value = (-self.pos_) * self.ask_        total_trade_value = self.trade_val_ + close_value        if total_trade_value == 0.0:            self.total_ret_ = 0.0        else:            self.total_ret_ = self.pnl_ / total_trade_value        if (self.pos_open_time_ != 0):            self.pos_hold_time_ = self._calcTimeDiff(self.pos_open_time_, self.time_)        else:            self.pos_hold_time_ = 0    def _calcReturn(self):        rv = 0        if self.cost_!=0:            if self.pos_>0:                rv = (self.bid_ - self.cost_) / self.cost_            elif self.pos_<0:                rv = (self.cost_ - self.ask_) / self.cost_        return rv    @staticmethod    def _calcTimeDiff(pos_open_time,time):        return (pos_open_time-time).seconds    def status(self):        pass    def get_position_type(self):        if self.pos_>0:            return "long"        elif self.pos_<0:            return "short"        else:            return Noneclass StockTradingEnv(gym.Env):    def __init__(self, df, risk_factor, transaction_cost,order_qty=500):        super(StockTradingEnv, self).__init__()        self.OrderManager = OrderManager()        # 数据集        self.df = df        self.df["mid_price"] = (df['askPx1'] + df['bidPx1'])/2        self.df["spread"] = df['askPx1'] - df['bidPx1']        self.order_qty=order_qty        # 动作空间（离散）        self.action_space = spaces.Discrete(5)  # 添加"hold"操作        # 观测空间        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(12,), dtype=np.float32)        # 状态        self.current_step = None        self.balance = None        self.shares_held = None        self.total_sales_value = None        self.position = None        self.open_price = None        self.is_closing_time = None        # 风险因素和交易成本参数        self.risk_factor = risk_factor        self.transaction_cost = transaction_cost        self.reset()    def reset(self):        # 重置状态        self.current_step = 0        self.balance = 10000.0        self.balance_open = self.balance        self.balance_last = self.balance        self.shares_held = 0.0        self.pnl = 0.0        self.position = None        self.open_price = None        self.is_closing_time = False        # 返回初始观测        return self._next_observation()    def step(self, action):        # 执行动作并更新状态        if action == 0:  # hold操作            pass        elif self.position is None:            if action == 1:  # 买入开仓                self.position = "long"                self.open_price = self.df.iloc[self.current_step]['bidPx1']                self.shares_held += self.order_qty                self.balance_open = self.balance                self.OrderManager.onTrade(self.order_qty,self.open_price,1)            elif action == 3:  # 卖出开仓                self.position = "short"                self.shares_held -= self.order_qty                self.open_price = self.df.iloc[self.current_step]['askPx1']                self.balance_open = self.balance                self.OrderManager.onTrade(self.order_qty,self.open_price,-1)        else:            if action == 2 and self.position == "long":  # 卖出平仓                self.OrderManager.onTrade(abs(self.shares_held),self.open_price,-1)                reward = self._get_reward()                self.position = None                self.balance += reward                self.shares_held = 0.0                self.pnl += reward                balance_now = self.balance_open + reward                reward = self.balance_last - balance_now                self.balance_last = balance_now                return self._next_observation(), reward, False, {}            elif action == 4 and self.position == "short":  # 买入平仓                self.OrderManager.onTrade(abs(self.shares_held),self.open_price,1)                reward = self._get_reward()                self.position = None                self.balance += reward                self.shares_held = 0.0                self.pnl += reward                balance_now = self.balance_open + reward                reward = self.balance_last - balance_now                self.balance_last = balance_now                return self._next_observation(), reward, False, {}        self.current_step += 1        # 检查是否接近收盘时间        if self.df.loc[self.current_step,"datetime"] == "1970-01-01 14:56:00":            self.is_closing_time = True        if self.df.loc[self.current_step,"datetime"] == "1970-01-01 09:30:06":            self.is_closing_time = False        # 执行平仓操作        if self.is_closing_time and self.position is not None:            if self.position == "long":                reward = self._get_reward()                self.position = None                self.balance += reward                self.shares_held = 0.0                self.pnl += reward                return self._next_observation(), reward, False, {}            elif self.position == "short":                reward = self._get_reward()                self.position = None                self.balance += reward                self.shares_held = 0.0                self.pnl += reward                return self._next_observation(), reward, False, {}        else:            # 计算奖励            reward = self._get_reward()        # 判断是否结束        balance_now = self.balance_open +reward        reward = balance_now -self.balance_last        self.balance_last = balance_now        done = (self.current_step >= len(self.df) - 1) | (self.balance<0)        if self.current_step % 1000 == 0:            self._render()        # 返回观测、奖励、完成状态和额外信息        obs = self._next_observation()        return obs, reward, done, {}    def _render(self):        print(f"pnl={self.pnl},self.balance={self.balance},"              f"current_step={self.current_step}",)    def _next_observation(self):        # 返回下一个观测值        state = 0 if self.position is None else 1 if self.shares_held > 0 else -1        next_obs = np.array([            self.df.iloc[self.current_step]['datetime'],            self.df.iloc[self.current_step]['askPx1'],            self.df.iloc[self.current_step]['bidPx1'],            self.df.iloc[self.current_step]['askVlm1'],            self.df.iloc[self.current_step]['bidVlm1'],            self.df.iloc[self.current_step]['score'],            self.df.iloc[self.current_step]['score_long'],            self.df.iloc[self.current_step]['score'],            self.df.iloc[self.current_step]['mid_price'],            self.df.iloc[self.current_step]['spread'],            self.df.iloc[self.current_step]['secID'],            state        ])        self.OrderManager.onTick({            "time":self.df.iloc[self.current_step]['datetime'],            "ask":self.df.iloc[self.current_step]['askPx1'],            "bid":self.df.iloc[self.current_step]['bidPx1']        })        return next_obs    def _get_reward(self):        # 计算奖励        current_price = self.df.iloc[self.current_step]['mid_price']        if self.position is not None:            returns = (self.open_price - current_price) * (-1) * self.shares_held - self.transaction_cost * self.shares_held * current_price        else:            returns = 0        # 风险因素奖励        # risk_reward = self.risk_factor * np.abs(returns)        # 交易成本惩罚        # transaction_penalty = self.transaction_cost * np.abs(returns) * np.abs(self.shares_held)        # 总奖励        reward = returns        return rewardimport gymimport numpy as npimport pandas as pdfrom stable_baselines3 import PPOfrom pathlib import Pathlong_path = "/home/kf/notebook/losh/haiyingci/data_muti_socre_long"symbol = "300274"merge = []for path in sorted(Path("/home/kf/notebook/losh/haiyingci/data_muti_socre").rglob(f"*{symbol}*")):    try:        df_backtest = pd.read_parquet(path)        df_backtest_long = pd.read_parquet(f"{long_path}/{path.parent.name}/{path.name}")        merge.append(pd.merge(df_backtest, df_backtest_long, how="inner", on=["datetime"], suffixes=["", "_long"]))    except Exception as e:        print(e)df = pd.concat(merge)df = df[~df["datetime"].isnull()]df = df.reset_index()env = StockTradingEnv(df, risk_factor=0.01, transaction_cost=0.001)# 初始化PPO算法model = PPO("MlpPolicy", env, verbose=1)# 训练模型model.learn(total_timesteps=10000000)# 使用训练好的模型进行测试obs = env.reset()for _ in range(100):    action, _ = model.predict(obs)    obs, reward, done, _ = env.step(action)    if done:        break# 关闭环境env.close()