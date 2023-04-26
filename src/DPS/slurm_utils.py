import socket
from DPS.rapl_utils import *
import numpy as np
import math
from DPS.config import *

class Slurm:
	def __init__(self, init_cap, inc_threshold = .98, dec_threshold = .9, inc_amt = 30, dec_amt = 30):
		self._shape = (len(config.EXP_NODES),2)
		self._budget = init_cap * 2 * len(config.EXP_NODES)
		self._power_arr = np.ones(self._shape)
		self._cap_arr = np.ones(self._shape, dtype=int) * init_cap
		self._cap_flag_arr = np.zeros(self._shape, dtype=int)
		self._inc_threshold = inc_threshold
		self._dec_threshold = dec_threshold
		self._min_cap = config.MIN_POWER
		self._max_cap = config.MAX_POWER
		self._inc_amt = inc_amt
		self._dec_amt = dec_amt

	def read_power(self, power_arr):
		if power_arr.shape != self._shape:
			return -1

		self._power_arr = power_arr
		return

	def write_power(self):
		return self._power_arr

	def get_flags(self):
		return self._cap_flag_arr

	def get_caps(self):
		return self._cap_arr

	def set_caps(self):

		extra_budget = self._budget - np.sum(self._cap_arr)
		self._cap_flag_arr *= 0
		cap_inc_cnt = 0

		# Decrease caps
		for i in range(self._shape[0]):
			for j in range(self._shape[1]):
				if self._cap_arr[i,j] > self._min_cap \
					and self._power_arr[i,j] < self._cap_arr[i,j] * self._dec_threshold:

					new_cap = max( (self._cap_arr[i,j] + self._power_arr[i,j]) / 2,\
						self._cap_arr[i,j] - self._dec_amt )
					new_cap = max(self._min_cap, new_cap)
					new_cap = round(new_cap)

					extra_budget += self._cap_arr[i,j] - new_cap
					self._cap_arr[i,j] = new_cap
					self._cap_flag_arr[i,j] = 1

				elif self._power_arr[i,j] > self._cap_arr[i,j] * self._inc_threshold:
					cap_inc_cnt += 1

		# Increase caps

		if not cap_inc_cnt:
			return
			
		avg_excess = extra_budget / cap_inc_cnt

		for i in range(self._shape[0]):
			for j in range(self._shape[1]):
				if not self._cap_flag_arr[i,j] \
					and self._power_arr[i,j] > self._cap_arr[i,j] * self._inc_threshold:

					if self._cap_arr[i,j] >= self._max_cap:
						cap_inc_cnt -= 1
						avg_excess = extra_budget / cap_inc_cnt
						continue

					new_cap = self._cap_arr[i,j] + min(avg_excess, self._inc_amt)
					new_cap = min(self._max_cap, new_cap)
					new_cap = round(new_cap)

					# print(f'[{i+1},{j}] {self._power_arr[i,j]}, {self._cap_arr[i,j]}, {extra_budget}, {cap_inc_cnt}, {avg_excess}, {new_cap}')

					cap_inc_cnt -= 1
					extra_budget -= new_cap - self._cap_arr[i,j]

					if cap_inc_cnt:
						avg_excess = extra_budget / cap_inc_cnt

					self._cap_arr[i,j] = new_cap
					self._cap_flag_arr[i,j] = 1
					
		return







