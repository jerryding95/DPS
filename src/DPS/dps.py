import subprocess
import time
import socket
import sys
import numpy as np
from config import *
from noise_utils import *
from slurm_utils import *
from rapl_utils import *
from process_utils import *
from scipy.signal import find_peaks


class DPS_supermaster:
	SHAPE = (len(config.EXP_NODES),2)
	RAPL_CAP_ARR = np.ones(SHAPE,dtype=np.int)*config.TDP
	RAPL_POWER_ARR = np.ones(SHAPE)
	EST_POWER_ARR_HX = np.ones((20,SHAPE[0],SHAPE[1]))*20
	RAPL_CAP_FLAGS = np.ones(SHAPE,dtype=np.int)
	RAPL_POWER_LEVEL = np.zeros(SHAPE,dtype=np.int)
	SHORT_EPOCH_FLAG = np.zeros(SHAPE,dtype=np.int)
	_sentinel = Sentinel(config.CLUSTER_COUNT)
	ALGS = ['equal','dps','oracle','slurm']
	CAP = 165
	SLURM_SCHEDULER = None
	percentile_inc = None
	percentile_dec = None
	allowance = None
	deriv_threshold = None
	process_noise = None
	measurement_noise = None
	ALG = None
	filter_md = None
	cap_file, level_file, est_file = None, None, None
	worker_p_arr, stdout_arr = [], []
	sockets = []

	def __init__(self, alg, deriv_threshold = config.DERIV_THRESHOLD, \
			process_noise = config.PROCESS_NOISE, measurement_noise = config.MEASUREMENT_NOISE, \
			percentile_inc = 0.2, percentile_dec = 0.2, allowance = 0.95, \
			cap_file = 'cap.log', level_file = 'level.log', est_file = 'est.log'):
		# self.SHAPE = (len(config.EXP_NODES),2)
		# self.RAPL_CAP_ARR = np.ones(SHAPE,dtype=np.int)*config.TDP
		# self.RAPL_POWER_ARR = np.ones(SHAPE)
		# self.EST_POWER_ARR_HX = np.ones((20,SHAPE[0],SHAPE[1]))*20
		# self.RAPL_CAP_FLAGS = np.ones(SHAPE,dtype=np.int)
		# self.RAPL_POWER_LEVEL = np.zeros(SHAPE,dtype=np.int)
		# self.SHORT_EPOCH_FLAG = np.zeros(SHAPE,dtype=np.int)
		# self.SLURM_SCHEDULER = None

		self.RAPL_CAP_ARR = np.ones(self.SHAPE,dtype=np.int)*config.TDP
		self.ALG = alg
		self.deriv_threshold = deriv_threshold
		self.process_noise = process_noise
		self.measurement_noise = measurement_noise
		self.percentile_inc = percentile_inc
		self.percentile_dec = percentile_dec
		self.allowance = allowance
		self.filter_md = kalman_md(self.EST_POWER_ARR_HX[-1],50.0,self.process_noise,1.0)
		# self._sentinel = Sentinel(config.CLUSTER_COUNT)
		self.cap_file, self.level_file, self.est_file = open(cap_file,'a'), open(level_file,'a'), open(est_file,'a')
		# self.func = {'equal': equal_alc_caps,
		# 		'dps': mult_inc_mult_dec,
		# 		'oracle': oracle_alc_caps,
		# 		'slurm': slurm_alc_caps}
		if self.ALG not in self.ALGS:
			print(f'[ERROR]: {self.ALG} is not implemented!')
			sys.exit()

		print(f'Initializing all worker rapl cap to {config.TDP}')
		set_workers_pkg_power_cap(config.TDP,config.TDP)

		# Start dyn_rapl_worker on all workers
		self.worker_p_arr, self.stdout_arr = self.start_dyn_workers('~/chameleon-files/dps_worker.py', \
			f'--cap {config.TDP}')

		time.sleep(3)

		# Establish connections
		self.sockets = self.connect_to_workers()

	def __del__(self):
		self.cap_file.close()
		self.level_file.close()
		self.est_file.close()
		for s in self.sockets:
			s.close()
		for f in self.stdout_arr:
			f.close()
		print('DPS scheduler destructed.')

	######### Process Uilt Functions #########

	def start_dyn_workers(self, file, args):
		cmd = f'sudo python3 {file} {args}'

		agent_p_arr = []
		stdout_arr = []
		nodes_per_cluster = config.NODE_COUNT//config.CLUSTER_COUNT
		for i in config.EXP_NODES:
			print(f'Starting dyn_rapl_worker on worker{i}')
			fname = f"logs/random_app_exp_{config.TDP}_stdout_worker_{i}.txt"
			f = open(config.RECORD_PATH.joinpath(fname), "a")
			p = subprocess.Popen(["ssh", f'slave{i}', cmd], stdout=f,stderr=f)
			agent_p_arr.append(p)
			stdout_arr.append(f)
			print(f'dyn_rapl_worker started on worker{i}')
		return agent_p_arr, stdout_arr

	##########################################


	################## Stateless Module ##################

	def mult_inc(self, budget):
		for n in np.argsort(self.RAPL_POWER_ARR.ravel()):
			i,j = n//2, n%2
			if not self.RAPL_CAP_FLAGS[i][j] \
				and self.RAPL_POWER_ARR[i][j] >= self.allowance*self.RAPL_CAP_ARR[i][j] \
				and budget > 0:
				extra_need = min(budget, self.RAPL_CAP_ARR[i][j]*self.percentile_inc)
				# if budget >= RAPL_CAP_ARR[i][j]+extra_need:
				self.RAPL_CAP_ARR[i][j] += extra_need
				self.RAPL_CAP_FLAGS[i][j] = 1
				budget -= extra_need
		return budget

	def mult_dec(self, budget):
		for cap, power, flag in zip(self.RAPL_CAP_ARR, self.RAPL_POWER_ARR, self.RAPL_CAP_FLAGS):
			for i in range(2):
				if power[i] < self.allowance*cap[i]:
					cut_down = round(cap[i]*self.percentile_dec)
					if cap[i] - cut_down >= power[i]:
						new_cap = max(round(power[i]), cap[i] - cut_down, 70)
						budget += cap[i] - new_cap
						cap[i] = new_cap
						flag[i] = 1
		return budget

	def mult_inc_mult_dec(self):

		self.RAPL_CAP_FLAGS *= 0
		budget = self.SHAPE[0]*self.SHAPE[1]*config.TDP - np.sum(self.RAPL_CAP_ARR)

		# MD
		budget = self.mult_dec(budget)

		# MI with random priority
		budget = self.mult_inc(budget)

		return budget

	#####################################################

	################ Kalman Filter Module ###############

	def update_history(self):
		self.filter_md.iterate(self.RAPL_POWER_ARR,self.measurement_noise)
		self.EST_POWER_ARR_HX[:-1] = self.EST_POWER_ARR_HX[1:]
		self.EST_POWER_ARR_HX[-1] = self.filter_md.est_state()

	#####################################################

	################## Priority Module ##################

	def update_priorities(self, history_length = 5):

		# Decide whether power is changing periodically fast

		for i in range(self.SHAPE[0]):
			for j in range(self.SHAPE[1]):
				if self.SHORT_EPOCH_FLAG[i,j]:
					if np.std(self.EST_POWER_ARR_HX[:,i,j]) <= 5:
						self.SHORT_EPOCH_FLAG[i,j] = 0
					elif all([p<70 for p in self.EST_POWER_ARR_HX[:,i,j]]):
						self.SHORT_EPOCH_FLAG[i,j] = 0
						self.RAPL_POWER_LEVEL[i,j] = 0

				else:
					peaks, _ = find_peaks(self.EST_POWER_ARR_HX[:,i,j], prominence = self.deriv_threshold-5)
					if len(peaks) >= 2:
						self.SHORT_EPOCH_FLAG[i,j] = 1
						self.RAPL_POWER_LEVEL[i,j] = 1


		for prev_power, power, level, flag, cap, ind in \
				zip(self.EST_POWER_ARR_HX[-history_length], self.EST_POWER_ARR_HX[-1], \
				self.RAPL_POWER_LEVEL, self.SHORT_EPOCH_FLAG, self.RAPL_CAP_ARR, \
				np.arange(len(self.RAPL_CAP_ARR))):
			for i in range(self.SHAPE[1]):
				if not level[i]:
					if power[i] - prev_power[i] >= self.deriv_threshold:
						level[i] = 1
					elif power[i] - prev_power[i] >= 0 and power[i] >= 0.95*cap[i]:
						level[i] = 1

				elif not flag[i]:
					if power[i] - prev_power[i] <= -self.deriv_threshold:
						level[i] = 0
					elif all([p[ind,i]<70 for p in self.EST_POWER_ARR_HX]):
						level[i] = 0

		return

	########################################################

	################## Readjusting Module ##################

	def readjust_caps(self, budget):

		all_tdp = all([cap==config.TDP for cap in self.RAPL_CAP_ARR.ravel()])
		all_low = all([power < self.allowance*config.TDP for power in self.RAPL_POWER_ARR.ravel()])

		# If all at tdp:
		# No change should be done if all levels are high
		if all_tdp and all(self.RAPL_POWER_LEVEL.ravel()):
			self.RAPL_CAP_FLAGS = self.RAPL_CAP_FLAGS * 0
			return True

		# If not all at tdp:
		if not all_tdp:

			# If all low, reset
			if all_low:
				self.RAPL_CAP_FLAGS = self.RAPL_CAP_FLAGS * 0 + 1
				self.RAPL_CAP_ARR = self.RAPL_CAP_ARR * 0 + config.TDP
				return True


			# If no budget left, reset sockets with high level
			if budget <= 0:

				# If all levels are low, no need to reset
				if not any(self.RAPL_POWER_LEVEL.ravel()):
					return True

				# Not all levels are level, reset sockets with high level
				rest_budget = 0
				count = 0
				for level, cap in zip(self.RAPL_POWER_LEVEL, self.RAPL_CAP_ARR):
					for i in range(2):
						if level[i]:
							rest_budget += cap[i]
							count += 1
				new_cap = round(rest_budget/count)
				for level, cap, flag in zip(self.RAPL_POWER_LEVEL, self.RAPL_CAP_ARR, self.RAPL_CAP_FLAGS):
					for i in range(2):
						if level[i]:
							flag[i] = 1
							cap[i] = new_cap
				return True

			# If there is budget left, reallocate it to high sockets
			# Reallocate based on the cap each socket has now
			else:
				cur_caps = []
				inds = []
				for i in range(self.SHAPE[0]):
					for j in range(self.SHAPE[1]):
						if self.RAPL_POWER_LEVEL[i,j]:
							cur_caps.append(self.RAPL_CAP_ARR[i,j])
							inds.append((i,j))
				cur_caps = np.array(cur_caps)
				realloc_ratios = 1/cur_caps/np.sum(1/cur_caps)
				for ind, ratio in zip(inds, realloc_ratios):
					self.RAPL_CAP_FLAGS[ind] = True
					self.RAPL_CAP_ARR[ind] += round(budget * ratio)
				return True

		return False

	##########################################

	################# DPS function #################

	def dps(self):
		self.update_history()
		self.update_priorities()
		budget = self.mult_inc_mult_dec()
		self.readjust_caps(budget)
		return


	################# Others #################

	def equal_alc_caps(self):
		# print('Equal: not changing caps')
		return

	def oracle_alc_caps(self):

		allowance = 0.95

		budget = self.SHAPE[0]*self.SHAPE[1]*config.TDP 
		consumption = np.sum([max(config.MIN_POWER,p) for p in self.RAPL_POWER_ARR.ravel()])

		# budget*allowance > consumption: 
		# Restore cap to highest
		if budget*allowance > consumption:
			self.RAPL_CAP_ARR *= 0
			self.RAPL_CAP_ARR += config.MAX_POWER


		# budget*allowance <= consumption
		# Cap sockets higher than 70 so that budget*allowance = consumption
		else:
			inds = np.argwhere(self.RAPL_POWER_ARR > config.MIN_POWER)
			power_denomitor = consumption - config.MIN_POWER * (self.SHAPE[0]*self.SHAPE[1]-len(inds))
			cap_budget = budget - config.MIN_POWER * (self.SHAPE[0]*self.SHAPE[1]-len(inds))

			for i in range(self.SHAPE[0]):
				for j in range(self.SHAPE[1]):
					if [i,j] not in inds:
						self.RAPL_CAP_ARR[i,j] = config.MIN_POWER
					else:
						self.RAPL_CAP_ARR[i,j] = round(self.RAPL_POWER_ARR[i,j]*cap_budget/power_denomitor)

		self.RAPL_CAP_FLAGS *= 0
		self.RAPL_CAP_FLAGS += 1
		
		# print('Oracle applied.')
		return

	def slurm_alc_caps(self):
		if not self.SLURM_SCHEDULER:
			self.SLURM_SCHEDULER = Slurm(init_cap = config.TDP)

		self.SLURM_SCHEDULER.read_power(self.RAPL_POWER_ARR)
		self.SLURM_SCHEDULER.set_caps()
		self.RAPL_CAP_ARR = self.SLURM_SCHEDULER.get_caps()
		self.RAPL_CAP_FLAGS = self.SLURM_SCHEDULER.get_flags()

		# print('Slurm applied.')
		return


	##########################################


	#### Cap Adjusting Algorithm Together ####

	def decide_caps(self, alg):
		func = {'equal': self.equal_alc_caps,
			'dps': self.dps,
			'oracle': self.oracle_alc_caps,
			'slurm': self.slurm_alc_caps}

		if alg not in func:
			return 0

		func[alg]()
		return 1

	##########################################

	############## Recording #################

	def record_rapl(self):
		np.savetxt(self.cap_file, self.RAPL_CAP_ARR)
		np.savetxt(self.level_file, self.RAPL_POWER_LEVEL)
		np.savetxt(self.est_file, self.EST_POWER_ARR_HX[-1])
		# print('Rapl caps recorded.')
		return

	##########################################

	############## supermaster - worker communication #################

	def connect_to_workers(self):
		# Establish connections
		sockets = [socket.socket() for _ in config.EXP_IPS]
		for s,host,node in zip(sockets,config.EXP_IPS,config.EXP_NODES):
			try:
				print(f'Connecting to worker {node}...')
				s.connect((host,config.SOCKET_PORT))
				print(f'Connected')
			except ConnectionRefusedError:
				# end_monitoring(stdout_arr)
				print(f'Connection refused by Worker {node}, exitting...')
				killProcess('dyn_rapl_worker',sudo=True)
				sys.exit()
		return sockets

	def encode_msg(self):
		new_caps = []
		for caps, flags in zip(self.RAPL_CAP_ARR, self.RAPL_CAP_FLAGS):
			power0 = caps[0] if not flags[0] else caps[0] | 0x800
			power1 = caps[1] if not flags[1] else caps[1] | 0x800
			new_caps.append(f'{power0:0{3}x}{power1:0{3}x}')
		return new_caps

	def send_msg(self, caps):
		for s, mssg, host in zip(self.sockets, caps, config.EXP_NODES):
			s.send(mssg.encode('utf-8'))
		return 1

	def recv_msg(self):
		power_readings = ['' for _ in config.EXP_NODES]
		for i, s in enumerate(self.sockets):
			while not power_readings[i]:
				try:
					power_readings[i] = s.recv(6)
				except ConnectionResetError:
					print(f'Worker {i+1}: ConnectionResetError!')
					sys.exit()
		return power_readings

	def decode_msg(self, power_readings):
		for i, power_reading in enumerate(power_readings):
			self.RAPL_POWER_ARR[i,0] = int(power_reading[:3], 16)
			self.RAPL_POWER_ARR[i,1] = int(power_reading[3:], 16)
		return 1

	def send_end_msg(self):
		print('Sending ending messages to workers...')
		for s in self.sockets:
			s.send(b'ffffff')
		print('Messages all sent.')
		return 1

	###################################################################

	############# Expose sentinel ############

	def sentinel_set(self, ind):
		self._sentinel.set(ind)
		return

	def sentinel_get(self):
		return self._sentinel.get()

	##########################################

	##### Supermaster Executing Function #####

	def exec(self):
		count = 0
		# Apply algorithm till experiment over
		while not all(self.sentinel_get()):

			# print('\n[New Iteration]')
			count += 1
			if count%60 == 0:
				print(f'Iteration {count}')

			# Recording rapl caps
			self.record_rapl()

			# Communicate with workers
			new_caps = self.encode_msg()
			self.send_msg(new_caps)
			power_readings = self.recv_msg()
			self.decode_msg(power_readings)

			self.decide_caps(self.ALG)

		# Send messages that workload finished
		self.send_end_msg()

		return 1

	##########################################

class DPS_worker:
	RAPL_CAP_ARR = np.zeros(2)
	fd0, fd1 = None, None
	power_unit0, power_unit1 = None, None
	energy_unit0, energy_unit1 = None, None
	RAPL_CAP_ARR[0] = None
	RAPL_CAP_ARR[1] = None
	s = None
	conn, addr = None, None
	def __init__(self):
		self.fd0, self.fd1 = open_msr(0), open_msr(1)
		self.power_unit0, self.power_unit1 = read_power_unit(self.fd0), read_power_unit(self.fd1)
		self.energy_unit0, self.energy_unit1 = read_energy_unit(self.fd0), read_energy_unit(self.fd1)
		self.RAPL_CAP_ARR[0] = read_pkg_cap(self.fd0, self.power_unit0)
		self.RAPL_CAP_ARR[1] = read_pkg_cap(self.fd1, self.power_unit1)

		print('Wating for master connection...')
		self.s = socket.socket()
		# s.bind((socket.gethostname(), config.SOCKET_PORT))
		self.s.bind(('', config.SOCKET_PORT))
		self.s.listen(1)
		self.conn, self.addr = self.s.accept()
		print('Master connected.')

	def __del__(self):
		if self.s: self.s.close()

	def recv_msg(self):
		print('Wating for message from master...')
		mssg = ''
		while not mssg:
			mssg = self.conn.recv(6)
		print(f'Message received: {mssg}')
		mssg = int(mssg, 16)
		return mssg

	def decode_msg(self, mssg):
		change0, change1 = mssg>>23, (mssg>>11)&0x1
		self.RAPL_CAP_ARR[0], self.RAPL_CAP_ARR[1] = (mssg>>12)&0x7FF, mssg&0x7FF
		return change0, change1

	def encode_msg(self, power0, power1):
		return f'{power0:0{3}x}{power1:0{3}x}'

	def send_msg(self, mssg):
		print(f'Sending power reading {mssg} to master...')
		self.conn.send(mssg.encode('utf-8'))
		print('Power readings sent')
		return

	def read_power(self):
		print('Reading rapl pkg power...')
		start_power0, start_power1 = read_pkg_energy(self.fd0, self.energy_unit0), read_pkg_energy(self.fd1, self.energy_unit1)
		time.sleep(1)
		end_power0, end_power1 = read_pkg_energy(self.fd0, self.energy_unit0), read_pkg_energy(self.fd1, self.energy_unit1)
		power0, power1 = round(end_power0 - start_power0), round(end_power1 - start_power1)
		power0 += int(self.energy_unit0 * 0xFFFFFFFF) if power0 < 0 else 0
		power1 += int(self.energy_unit1 * 0xFFFFFFFF) if power1 < 0 else 0
		print('Rapl pkg power: ', power0, power1)
		return power0, power1


	def exec(self):
		while True:
			print('\n[New Iteration]')
			# Receive signal
			mssg = self.recv_msg()
			# End if application is finished
			if mssg == 0xFFFFFF:
				print('Ending message received, exiting...')
				break

			# Decode signal
			change0, change1 = self.decode_msg(mssg)

			# Change cap
			if change0:
				print('Changing s_0 rapl cap to ', self.RAPL_CAP_ARR[0])
				set_socket_pkg_power_cap(self.fd0, self.RAPL_CAP_ARR[0], self.power_unit0)

			if change1:
				print('Changing s_1 rapl cap to ', self.RAPL_CAP_ARR[1])
				set_socket_pkg_power_cap(self.fd1, self.RAPL_CAP_ARR[1], self.power_unit1)

			# Read rapl
			power0, power1 = self.read_power()

			# Send rapl to master
			mssg = self.encode_msg(power0, power1)
			self.send_msg(mssg)
